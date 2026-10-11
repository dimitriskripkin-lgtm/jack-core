#!/usr/bin/env python3
"""jack_arena_sandbox.py - Sicherheitsrahmen C fuer die Arena (Kategorie C, Code-Fix). Kap 276.

Drei Schichten, alle fail-closed:
1. ast_gate(source): AST-Tor als Positivliste. Nur erlaubte Knoten, Namen, Attribute und Imports.
   Gleiche Funktion fuer Runner-Tor (vor pytest_run) und Richter-Tor (vor dem Urteil).
2. run_pytest(run_dir, tests): pytest im begrenzten Subprozess. Leere Umgebung, python -I -B,
   eigene Prozessgruppe, Zeitlimit, CPU-/Speicher(RLIMIT_DATA)-/Dateigroessen-/Datei-Handle-Limits, kein Cache, keine Plugins.
   Android: Speicherueberlauf beendet den Prozess per SIGABRT (Status KILLED), nicht per MemoryError.
3. file_state / state_diff: Dateizustand vorher/nachher. Nur das Zielmodul darf sich aendern, nichts Neues.

Befehle: python3 jack_arena_sandbox.py selftest | gate <datei.py>
Kein Netz, keine Geheimnisse, keine JACK-Pfade. Prueflingscode laeuft nie im Runner-Prozess.
"""
import ast
import collections
import hashlib
import itertools
import json
import math
import os
import re
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time

VERSION = "1"
MAX_SOURCE = 20000
MAX_NODES = 5000
SUMMARY_MAX = 1500

# ---------- Schicht 1: AST-Tor ----------
STMT_OK = {"FunctionDef", "Return", "If", "For", "While", "Break", "Continue", "Pass", "Assign",
           "AugAssign", "AnnAssign", "Expr", "Raise", "Try", "Assert", "Delete", "Import", "ImportFrom"}
EXPR_OK = {"BoolOp", "BinOp", "UnaryOp", "IfExp", "Dict", "Set", "ListComp", "SetComp", "DictComp",
           "GeneratorExp", "Compare", "Call", "JoinedStr", "FormattedValue", "Constant", "Attribute",
           "Subscript", "Starred", "Name", "List", "Tuple", "Slice"}
MISC_OK = {"Module", "arguments", "arg", "keyword", "alias", "comprehension", "ExceptHandler",
           "Load", "Store", "Del", "And", "Or", "Add", "Sub", "Mult", "Div", "FloorDiv", "Mod", "Pow",
           "LShift", "RShift", "BitOr", "BitXor", "BitAnd", "Invert", "Not", "UAdd", "USub", "Eq", "NotEq",
           "Lt", "LtE", "Gt", "GtE", "Is", "IsNot", "In", "NotIn"}
NODE_OK = STMT_OK | EXPR_OK | MISC_OK

ALLOWED_BUILTINS = {
    "len", "range", "sorted", "min", "max", "sum", "abs", "round", "int", "float", "str", "bool",
    "list", "dict", "set", "frozenset", "tuple", "enumerate", "zip", "isinstance", "any", "all",
    "reversed", "map", "filter", "divmod", "ord", "chr", "iter", "next", "repr",
    "ValueError", "TypeError", "KeyError", "IndexError", "ZeroDivisionError", "StopIteration",
    "Exception", "ArithmeticError", "LookupError", "RuntimeError", "NotImplementedError",
}


def _public(obj):
    return {n for n in dir(obj) if not n.startswith("_")}


ALLOWED_MODULES = {
    "math": _public(math),
    "itertools": _public(itertools),
    "re": {"compile", "match", "fullmatch", "search", "findall", "finditer", "sub", "subn", "split",
           "escape", "IGNORECASE", "I", "MULTILINE", "M", "DOTALL", "S", "VERBOSE", "X", "ASCII", "A"},
    "functools": {"reduce", "partial", "cmp_to_key"},
    "collections": {"Counter", "defaultdict", "OrderedDict", "deque"},
    "typing": {"List", "Dict", "Tuple", "Set", "Optional", "Iterable", "Iterator", "Sequence", "Any",
               "Union", "Mapping"},
    "string": {"ascii_letters", "ascii_lowercase", "ascii_uppercase", "digits", "punctuation", "whitespace"},
}

# Attribute auf Werten: nur oeffentliche Methoden harmloser Typen (Positivliste). Keine Frame-/Code-/Generator-Innereien.
ALLOWED_ATTRS = set()
for _t in (str, list, dict, set, frozenset, tuple, int, float, bool, re.Pattern, re.Match,
           collections.Counter, collections.defaultdict, collections.OrderedDict, collections.deque):
    ALLOWED_ATTRS |= _public(_t)
ALLOWED_ATTRS |= {"args"}
ALLOWED_ATTRS -= {"format", "format_map"}  # Formatfelder koennen Attribute lesen ("{0.__class__}")


class Block(Exception):
    pass


def _bad_ident(name):
    return not isinstance(name, str) or name.startswith("__")


def ast_gate(source):
    """Prueft Quelltext. Rueckgabe {"ok": bool, "code": OK|POLICY_BLOCK|SYNTAX_ERROR, "reason": str}."""
    if not isinstance(source, str) or len(source) > MAX_SOURCE:
        return {"ok": False, "code": "POLICY_BLOCK", "reason": "Quelltext fehlt oder groesser als %d Zeichen" % MAX_SOURCE}
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError, MemoryError) as e:
        return {"ok": False, "code": "SYNTAX_ERROR", "reason": "nicht parsbar: %s" % type(e).__name__}
    try:
        _check(tree)
    except Block as e:
        return {"ok": False, "code": "POLICY_BLOCK", "reason": str(e)[:200]}
    except RecursionError:
        return {"ok": False, "code": "POLICY_BLOCK", "reason": "zu tief verschachtelt"}
    return {"ok": True, "code": "OK", "reason": "AST-Tor bestanden"}


def _check(tree):
    nodes = list(ast.walk(tree))
    if len(nodes) > MAX_NODES:
        raise Block("zu viele AST-Knoten")
    parent = {}
    for n in nodes:
        for c in ast.iter_child_nodes(n):
            parent[c] = n
    modules, bound = {}, set()
    # 1. Knotentypen und Bezeichner
    for n in nodes:
        k = type(n).__name__
        if k not in NODE_OK:
            raise Block("Knotentyp nicht erlaubt: %s" % k)
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            if isinstance(n, ast.ImportFrom):
                if n.level or n.module not in ALLOWED_MODULES:
                    raise Block("Import nicht erlaubt: %s" % (n.module or "relativ"))
                for a in n.names:
                    if a.name not in ALLOWED_MODULES[n.module]:
                        raise Block("Name aus %s nicht erlaubt: %s" % (n.module, a.name))
                    nm = a.asname or a.name
                    if _bad_ident(nm):
                        raise Block("Bezeichner nicht erlaubt: %s" % nm)
                    bound.add(nm)
            else:
                for a in n.names:
                    if a.name not in ALLOWED_MODULES:
                        raise Block("Import nicht erlaubt: %s" % a.name)
                    nm = a.asname or a.name
                    if _bad_ident(nm):
                        raise Block("Bezeichner nicht erlaubt: %s" % nm)
                    modules[nm] = a.name
        elif isinstance(n, ast.FunctionDef):
            if n.decorator_list:
                raise Block("Dekoratoren nicht erlaubt")
            if _bad_ident(n.name):
                raise Block("Bezeichner nicht erlaubt: %s" % n.name)
            for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                if any(isinstance(x, ast.Call) for x in ast.walk(d)):
                    raise Block("Aufruf in Default-Wert nicht erlaubt")
            bound.add(n.name)
        elif isinstance(n, ast.arg):
            if _bad_ident(n.arg):
                raise Block("Bezeichner nicht erlaubt: %s" % n.arg)
            bound.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            if _bad_ident(n.name):
                raise Block("Bezeichner nicht erlaubt: %s" % n.name)
            bound.add(n.name)
        elif isinstance(n, ast.keyword) and n.arg is not None and _bad_ident(n.arg):
            raise Block("Bezeichner nicht erlaubt: %s" % n.arg)
        elif isinstance(n, ast.Name):
            if _bad_ident(n.id):
                raise Block("Bezeichner nicht erlaubt: %s" % n.id)
            if isinstance(n.ctx, (ast.Store, ast.Del)):
                bound.add(n.id)
        elif isinstance(n, ast.Attribute):
            if n.attr.startswith("_"):
                raise Block("Attribut mit _ nicht erlaubt: %s" % n.attr)
    clash = bound & set(modules)
    if clash:
        raise Block("Modulname wird ueberschrieben: %s" % sorted(clash)[0])
    # 2. Namen lesen, Attribute, Module nur als Praefix
    for n in nodes:
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            if n.id in modules:
                p = parent.get(n)
                if not (isinstance(p, ast.Attribute) and p.value is n):
                    raise Block("Modul nur als modul.name nutzbar: %s" % n.id)
            elif n.id not in bound and n.id not in ALLOWED_BUILTINS:
                raise Block("Name nicht erlaubt: %s" % n.id)
        elif isinstance(n, ast.Attribute):
            v = n.value
            if isinstance(v, ast.Name) and v.id in modules:
                if n.attr not in ALLOWED_MODULES[modules[v.id]]:
                    raise Block("%s.%s nicht erlaubt" % (modules[v.id], n.attr))
            elif n.attr not in ALLOWED_ATTRS:
                raise Block("Attribut nicht erlaubt: %s" % n.attr)
    # 3. Modulebene: keine versteckten Aufrufe beim Import
    for st in tree.body:
        if isinstance(st, (ast.Import, ast.ImportFrom, ast.FunctionDef)):
            continue
        if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
            continue
        if isinstance(st, (ast.Assign, ast.AnnAssign)):
            if any(isinstance(x, (ast.Call, ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)) for x in ast.walk(st)):
                raise Block("Aufruf auf Modulebene nicht erlaubt")
            continue
        raise Block("Anweisung auf Modulebene nicht erlaubt: %s" % type(st).__name__)


# ---------- Schicht 2: pytest im begrenzten Subprozess ----------
def _limiter(cpu_s, mem_bytes, fsize_bytes):
    def apply():
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_s, cpu_s + 1))
        if mem_bytes:  # RLIMIT_DATA statt RLIMIT_AS: Android reserviert viel Adressraum, AS < 16 GB laesst Python nicht starten
            resource.setrlimit(resource.RLIMIT_DATA, (mem_bytes, mem_bytes))
        resource.setrlimit(resource.RLIMIT_FSIZE, (fsize_bytes, fsize_bytes))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    return apply


def run_pytest(run_dir, tests, timeout_s=30, cpu_s=20, mem_mb=768, fsize_kb=1024):
    """Fuehrt die festen Testdateien aus. Rueckgabe dict mit status PASSED|FAILED|ERROR|TIMEOUT|KILLED|NO_TESTS|INFRA."""
    run_dir = os.path.realpath(run_dir)
    for t in tests:
        p = os.path.realpath(os.path.join(run_dir, t))
        if os.path.dirname(p) != run_dir or not os.path.isfile(p):
            return {"status": "INFRA", "rc": None, "summary": "Testdatei unzulaessig: %s" % t, "seconds": 0}
    side = tempfile.mkdtemp(prefix="arena_c_")  # ausserhalb des Run-Ordners: leere ini, tmp
    ini = os.path.join(side, "pytest.ini")
    with open(ini, "w") as f:
        f.write("[pytest]\n")
    tmp = os.path.join(side, "tmp")
    os.mkdir(tmp)
    env = {"PATH": os.path.dirname(sys.executable), "HOME": side, "TMPDIR": tmp, "LANG": "C.UTF-8",
           "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"}
    cmd = [sys.executable, "-I", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:stepwise",
           "--no-header", "-c", ini, "--rootdir", run_dir, "--basetemp", os.path.join(tmp, "bt")] + list(tests)
    t0 = time.time()
    status, out, rc = None, "", None
    try:
        p = subprocess.Popen(cmd, cwd=run_dir, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True,
                             preexec_fn=_limiter(cpu_s, mem_mb * 1024 * 1024 if mem_mb else 0, fsize_kb * 1024))
        try:
            raw, _ = p.communicate(timeout=timeout_s)
            rc = p.returncode
            out = raw.decode("utf-8", errors="replace")
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.communicate()
            status = "TIMEOUT"
    except OSError as e:
        status, out = "INFRA", "Start fehlgeschlagen: %s" % type(e).__name__
    finally:
        shutil.rmtree(side, ignore_errors=True)
    if status is None:
        if "No module named pytest" in out:
            status = "INFRA"
        elif rc == 0:
            status = "PASSED"
        elif rc == 1:
            status = "FAILED"
        elif rc == 5:
            status = "NO_TESTS"
        elif rc is not None and rc < 0:
            status = "KILLED"
        else:
            status = "ERROR"  # 2 = Sammelfehler (z.B. Zielmodul kaputt), 3/4 = interner Fehler/Aufruf
    lines = [l for l in out.splitlines() if l.strip()]
    tail = "\n".join(lines[-25:])
    return {"status": status, "rc": rc, "seconds": round(time.time() - t0, 2), "summary": tail[-SUMMARY_MAX:]}


# ---------- Schicht 3: Dateizustand ----------
def file_state(run_dir):
    st = {}
    for root, dirs, files in os.walk(run_dir):
        dirs.sort()
        rel = os.path.relpath(root, run_dir)
        if rel != ".":
            st[rel + "/"] = "DIR"
        for fn in sorted(files):
            p = os.path.join(root, fn)
            r = os.path.relpath(p, run_dir)
            if os.path.islink(p):
                st[r] = "LINK"
                continue
            with open(p, "rb") as f:
                st[r] = hashlib.sha256(f.read()).hexdigest()
    return st


def state_diff(before, after, may_change=()):
    may = set(may_change)
    new = sorted(k for k in after if k not in before)
    gone = sorted(k for k in before if k not in after)
    changed = sorted(k for k in before if k in after and before[k] != after[k])
    bad = new + gone + [k for k in changed if k not in may]
    return {"ok": not bad, "new": new, "removed": gone, "changed": changed, "violations": bad}


# ---------- Selbsttest ----------
SEC = [
    ("C-SEC-01 direkter Import", "import os\ndef f():\n    return 1\n"),
    ("C-SEC-02 From-Import", "from subprocess import run\ndef f():\n    return 1\n"),
    ("C-SEC-03 Alias", "import socket as math\ndef f():\n    return 1\n"),
    ("C-SEC-04 open", "def f(p):\n    return open(p).read()\n"),
    ("C-SEC-05a exec", "def f(s):\n    exec(s)\n"),
    ("C-SEC-05b eval", "def f(s):\n    return eval(s)\n"),
    ("C-SEC-05c compile", "def f(s):\n    return compile(s, 'x', 'exec')\n"),
    ("C-SEC-06 __import__", "def f():\n    return __import__('os')\n"),
    ("C-SEC-07 getattr", "def f(x):\n    return getattr(x, '__class__')\n"),
    ("C-SEC-08 __builtins__", "def f():\n    return __builtins__\n"),
    ("C-SEC-09a globals", "def f():\n    return globals()['x']\n"),
    ("C-SEC-09b vars", "def f():\n    return vars()\n"),
    ("C-SEC-10a Vollbreite", "def f(s):\n    \uff45\uff58\uff45\uff43(s)\n"),
    ("C-SEC-10b kyrillisch", "def f(s):\n    \u0435xec(s)\n"),
    ("C-SEC-11 Dekorator", "def d(g):\n    return g\n@d\ndef f():\n    return 1\n"),
    ("C-SEC-12 Default-Aufruf", "def f(x=len('abc')):\n    return x\n"),
    ("C-SEC-13 Metaklasse", "class M(type):\n    pass\nclass A(metaclass=M):\n    pass\n"),
    ("C-SEC-14 Klassenkoerper", "class A:\n    x = len('a')\n"),
    ("C-SEC-15 Dunder-Kette", "def f():\n    return ().__class__.__bases__[0].__subclasses__()\n"),
    ("C-SEC-16 Top-Level-Aufruf", "def f():\n    return 1\nf()\n"),
    ("X-01 re.enum.sys", "import re\ndef f():\n    return re.enum.sys.modules\n"),
    ("X-02 typing.sys", "import typing\ndef f():\n    return typing.sys\n"),
    ("X-03 Generator-Frame", "def f():\n    g = (x for x in [1])\n    return g.gi_frame.f_globals\n"),
    ("X-04 Modul als Wert", "import math\ndef f():\n    m = math\n    return m.floor(1.5)\n"),
    ("X-05 Formatfeld", "def f(x):\n    return '{0.real}'.format(x)\n"),
    ("X-06 lambda", "def f():\n    return (lambda: 1)()\n"),
    ("X-07 Untermodul", "import collections.abc\ndef f():\n    return 1\n"),
    ("X-08 relativer Import", "from . import x\ndef f():\n    return 1\n"),
    ("X-09 global", "def f():\n    global y\n    y = 1\n"),
    ("X-10 Walross", "def f(a):\n    return (b := a)\n"),
    ("X-11 yield", "def f():\n    yield 1\n"),
    ("X-12 with open", "def f(p):\n    with open(p) as h:\n        return h.read()\n"),
    ("X-13 Stern-Import", "from math import *\ndef f():\n    return 1\n"),
    ("X-14 Modul ueberschreiben", "import math\ndef f(math):\n    return math.floor(1)\n"),
    ("X-15 type()", "def f():\n    return type('A', (), {})\n"),
    ("X-16 Top-Level-Comprehension", "X = [len(a) for a in ['x']]\ndef f():\n    return X\n"),
    ("X-17 __future__", "from __future__ import annotations\ndef f():\n    return 1\n"),
    ("X-18 unbekannter Name", "def f():\n    return breakpoint()\n"),
]

OK_CASES = [
    ("P-01 reine Funktion", "def add(a, b):\n    return a + b\n"),
    ("P-02 math", "import math\ndef f(x):\n    return math.floor(x) + math.sqrt(4)\n"),
    ("P-03 typing", "from typing import List, Optional\ndef f(xs: List[int]) -> Optional[int]:\n    return max(xs) if xs else None\n"),
    ("P-04 C01 sum_to", '"""Summe."""\ndef sum_to(n):\n    return sum(range(1, n + 1))\n'),
    ("P-05 C02 parse_bool", "TRUE = {'true', '1', 'yes'}\nFALSE = {'false', '0', 'no'}\ndef parse_bool(text):\n    t = text.strip().lower()\n    if t in TRUE:\n        return True\n    if t in FALSE:\n        return False\n    raise ValueError('unbekannt: %r' % text)\n"),
    ("P-06 C03 dedupe", "def dedupe(items):\n    seen = set()\n    out = []\n    for x in items:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n"),
    ("P-07 C04 leer", "def mean(xs):\n    if not xs:\n        return 0.0\n    return sum(xs) / len(xs)\n"),
    ("P-08 C05 csv", "def parse(text):\n    rows = []\n    for line in text.splitlines():\n        line = line.strip()\n        if not line:\n            continue\n        rows.append([c.strip() for c in line.split(',')])\n    return rows\n"),
    ("P-09 C06 retry", "def retry(fn, attempts=3):\n    last = None\n    for i in range(attempts):\n        try:\n            return fn()\n        except ValueError as e:\n            last = e\n    raise RuntimeError('aufgegeben') from last\n"),
    ("P-10 C07 normalize", "import re\ndef norm(s):\n    return re.sub(r'\\s+', ' ', s).strip().lower()\n"),
    ("P-11 C08 intervals", "def merge(iv):\n    out = []\n    for a, b in sorted(iv):\n        if out and a <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], b)\n        else:\n            out.append([a, b])\n    return [tuple(x) for x in out]\n"),
    ("P-12 collections", "from collections import Counter\nimport collections\ndef top(xs):\n    d = collections.defaultdict(int)\n    for x in xs:\n        d[x] += 1\n    return Counter(xs).most_common(1)[0][0]\n"),
    ("P-13 f-string", "def show(n):\n    return f'{n:>4} Stueck {n!r}'\n"),
]

RES = [  # Schicht 2: muessen durch Limits enden, nicht durch das Tor
    ("C-SEC-17 Endlosschleife", "def f():\n    while True:\n        pass\n", ("TIMEOUT", "KILLED", "FAILED")),
    ("C-SEC-18 Speicherbombe", "def f():\n    x = [0] * (10 ** 10)\n    return len(x)\n", ("FAILED", "KILLED")),
    ("C-SEC-18b wachsender Speicher", "def f():\n    x = []\n    for i in range(5000):\n        x.append('a' * 10 ** 6)\n    return len(x)\n", ("FAILED", "KILLED")),
    ("C-SEC-19 tiefe Rekursion", "def f(n=0):\n    return f(n + 1)\n", ("FAILED",)),
]


def selftest():
    ok = total = 0
    for name, src in SEC:
        r = ast_gate(src)
        good = r["code"] == "POLICY_BLOCK"
        ok += good
        total += 1
        print("%-30s %s  %s" % (name, "ok" if good else "FEHLER", r["reason"]))
    for name, src in OK_CASES:
        r = ast_gate(src)
        good = r["ok"]
        ok += good
        total += 1
        print("%-30s %s  %s" % (name, "ok" if good else "FEHLER", r["reason"]))
    base = tempfile.mkdtemp(prefix="arena_sbx_")
    try:
        for name, src, want in RES:
            d = os.path.join(base, "r%d" % total)
            os.mkdir(d)
            with open(os.path.join(d, "ziel.py"), "w") as f:
                f.write(src)
            with open(os.path.join(d, "test_ziel.py"), "w") as f:
                f.write("from ziel import f\n\ndef test_f():\n    assert f() is not None\n")
            gate = ast_gate(src)
            before = file_state(d)
            r = run_pytest(d, ["test_ziel.py"], timeout_s=15, cpu_s=8)
            diff = state_diff(before, file_state(d))
            good = gate["ok"] and r["status"] in want and r["seconds"] < 20 and diff["ok"]
            ok += good
            total += 1
            print("%-30s %s  Tor=%s pytest=%s %.1fs Dateien=%s" % (name, "ok" if good else "FEHLER", gate["code"], r["status"], r["seconds"], "sauber" if diff["ok"] else diff["violations"]))
        # ehrlicher Lauf: gruen, keine neuen Dateien; danach Test manipuliert -> erkannt
        d = os.path.join(base, "ehrlich")
        os.mkdir(d)
        with open(os.path.join(d, "range_sum.py"), "w") as f:
            f.write("def sum_to(n):\n    return sum(range(1, n + 1))\n")
        with open(os.path.join(d, "test_range_sum.py"), "w") as f:
            f.write("from range_sum import sum_to\n\ndef test_null():\n    assert sum_to(0) == 0\n\ndef test_drei():\n    assert sum_to(3) == 6\n")
        before = file_state(d)
        r = run_pytest(d, ["test_range_sum.py"])
        diff = state_diff(before, file_state(d), ["range_sum.py"])
        good = r["status"] == "PASSED" and diff["ok"]
        ok += good
        total += 1
        print("%-30s %s  pytest=%s %.1fs Dateien=%s" % ("ehrlicher Lauf", "ok" if good else "FEHLER", r["status"], r["seconds"], "sauber" if diff["ok"] else diff["violations"]))
        with open(os.path.join(d, "range_sum.py"), "w") as f:
            f.write("def sum_to(n):\n    return sum(range(1, n))\n")
        r = run_pytest(d, ["test_range_sum.py"])
        good = r["status"] == "FAILED" and "failed" in r["summary"]
        ok += good
        total += 1
        print("%-30s %s  pytest=%s" % ("Fehler wird erkannt", "ok" if good else "FEHLER", r["status"]))
        with open(os.path.join(d, "test_range_sum.py"), "a") as f:
            f.write("\n")
        diff = state_diff(before, file_state(d), ["range_sum.py"])
        good = not diff["ok"] and diff["violations"] == ["test_range_sum.py"]
        ok += good
        total += 1
        print("%-30s %s  %s" % ("Testaenderung erkannt", "ok" if good else "FEHLER", diff["violations"]))
        open(os.path.join(d, "conftest.py"), "w").close()
        diff = state_diff(before, file_state(d), ["range_sum.py"])
        good = "conftest.py" in diff["new"] and not diff["ok"]
        ok += good
        total += 1
        print("%-30s %s  neu=%s" % ("neue Datei erkannt", "ok" if good else "FEHLER", diff["new"]))
        r = run_pytest(d, ["../x.py"])
        good = r["status"] == "INFRA"
        ok += good
        total += 1
        print("%-30s %s  %s" % ("Testpfad ausserhalb", "ok" if good else "FEHLER", r["summary"]))
    finally:
        shutil.rmtree(base, ignore_errors=True)
    print("SANDBOX-SELFTEST %d/%d ok (v%s)" % (ok, total, VERSION))
    return ok == total


def main(argv):
    if len(argv) >= 2 and argv[1] == "selftest":
        return 0 if selftest() else 1
    if len(argv) >= 3 and argv[1] == "gate":
        with open(argv[2], encoding="utf-8") as f:
            print(json.dumps(ast_gate(f.read()), ensure_ascii=False))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
