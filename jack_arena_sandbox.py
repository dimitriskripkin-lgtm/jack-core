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
import builtins
import collections
import hashlib
import itertools
import json
import math
import os
import re
import resource
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time

VERSION = "5"  # 5: lambda erlaubt als Syntax (Koerper verzoegert, Defaults sofort geprueft), ChatGPT 12.10. 02:20. 4: 4: unbekannte Nicht-Builtin-Namen = Programmierfehler (NameError), kein Policy-Block. 3: Kodierungs-Cookie, Zustand waehrend pytest eingefroren (ChatGPT-Review 2). 2: 2: ChatGPT-Review 11.10. (Scope-Vergiftung, Attribut-Schreiben, Annotationen, Ausgabeflut)
MAX_SOURCE = 20000
MAX_NODES = 5000
SUMMARY_MAX = 1500
OUT_MAX = 1024 * 1024  # harte Grenze fuer pytest-Ausgabe, schon beim Lesen (C-SEC-22)
OUT_TAIL = 16384

# ---------- Schicht 1: AST-Tor ----------
STMT_OK = {"FunctionDef", "Return", "If", "For", "While", "Break", "Continue", "Pass", "Assign",
           "AugAssign", "AnnAssign", "Expr", "Raise", "Try", "Assert", "Delete", "Import", "ImportFrom"}
EXPR_OK = {"Lambda", "BoolOp", "BinOp", "UnaryOp", "IfExp", "Dict", "Set", "ListComp", "SetComp", "DictComp",
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


# Kein Name aus der Python-Builtin-Menge darf gebunden werden, ausser er ist erlaubt (C-SEC-20):
# sonst "legitimiert" ein Parameter open in Funktion A das echte open in Funktion B (Bindungen werden modulweit gesammelt).
FORBIDDEN_BIND = set(dir(builtins)) - ALLOWED_BUILTINS
CODING_RE = re.compile(r"^[ \t\f]*#.*?coding[:=]")  # PEP 263, nur Zeile 1-2 relevant (C-SEC-24)
ANNOT_OK = (ast.Name, ast.Attribute, ast.Subscript, ast.Tuple, ast.List, ast.Load, ast.BinOp, ast.BitOr)


class Block(Exception):
    pass


def _bad_ident(name):
    # Nicht-ASCII-Bezeichner fail-closed (Homoglyphen, C-SEC-10b); Vollbreite normalisiert der Parser schon zu ASCII.
    return not isinstance(name, str) or not name.isascii() or name.startswith("__") or name in FORBIDDEN_BIND


def _eager(node):
    """Alle Knoten, die beim Erzeugen sofort ausgewertet werden: Lambda-Koerper wird uebersprungen (laeuft erst beim Aufruf),
    Lambda-Defaults werden dagegen sofort ausgewertet und mitgeprueft."""
    todo = [node]
    while todo:
        n = todo.pop()
        yield n
        if isinstance(n, ast.Lambda):
            todo.extend(n.args.defaults + [d for d in n.args.kw_defaults if d is not None])
            continue
        todo.extend(ast.iter_child_nodes(n))


def _check_annotation(a):
    if a is None:
        return
    for x in ast.walk(a):
        if isinstance(x, ast.Constant) and x.value is None:
            continue
        if not isinstance(x, ANNOT_OK) or (isinstance(x, ast.BinOp) and not isinstance(x.op, ast.BitOr)):
            raise Block("Annotation zu komplex: %s" % type(x).__name__)


def ast_gate(source):
    """Prueft Quelltext. Rueckgabe {"ok": bool, "code": OK|POLICY_BLOCK|SYNTAX_ERROR, "reason": str}."""
    if not isinstance(source, str) or len(source) > MAX_SOURCE:
        return {"ok": False, "code": "POLICY_BLOCK", "reason": "Quelltext fehlt oder groesser als %d Zeichen" % MAX_SOURCE}
    if source.startswith("\ufeff") or any(CODING_RE.match(l) for l in source.splitlines()[:2]):
        return {"ok": False, "code": "POLICY_BLOCK", "reason": "Kodierungsangabe/BOM nicht erlaubt (nur UTF-8 ohne Cookie)"}
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


def gate_file(path):
    """Tor auf die gespeicherten Bytes: strikt UTF-8 dekodieren, dann ast_gate. So sehen Tor und Interpreter denselben Text."""
    try:
        with open(path, "rb") as f:
            raw = f.read(MAX_SOURCE * 4 + 1)
        text = raw.decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as e:
        return {"ok": False, "code": "POLICY_BLOCK", "reason": "Datei nicht strikt UTF-8 lesbar: %s" % type(e).__name__}
    return ast_gate(text)


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
                if any(isinstance(x, ast.Call) for x in _eager(d)):
                    raise Block("Aufruf in Default-Wert nicht erlaubt")
            allargs = n.args.posonlyargs + n.args.args + n.args.kwonlyargs + [x for x in (n.args.vararg, n.args.kwarg) if x]
            for x in allargs:
                _check_annotation(x.annotation)
            _check_annotation(n.returns)
            bound.add(n.name)
        elif isinstance(n, ast.Lambda):
            for d in n.args.defaults + [x for x in n.args.kw_defaults if x is not None]:
                if any(isinstance(x, ast.Call) for x in _eager(d)):
                    raise Block("Aufruf in lambda-Default nicht erlaubt")
        elif isinstance(n, ast.arg):
            if _bad_ident(n.arg):
                raise Block("Bezeichner nicht erlaubt: %s" % n.arg)
            bound.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            if _bad_ident(n.name):
                raise Block("Bezeichner nicht erlaubt: %s" % n.name)
            bound.add(n.name)
        elif isinstance(n, ast.keyword) and n.arg is not None and n.arg.startswith("__"):  # Schluesselwort bindet nichts
            raise Block("Bezeichner nicht erlaubt: %s" % n.arg)
        elif isinstance(n, ast.Name):
            if _bad_ident(n.id):
                raise Block("Bezeichner nicht erlaubt: %s" % n.id)
            if isinstance(n.ctx, (ast.Store, ast.Del)):
                bound.add(n.id)
        elif isinstance(n, ast.Attribute):
            if n.attr.startswith("_"):
                raise Block("Attribut mit _ nicht erlaubt: %s" % n.attr)
            if not isinstance(n.ctx, ast.Load):
                raise Block("Attribut schreiben/loeschen nicht erlaubt: %s" % n.attr)
        elif isinstance(n, ast.AnnAssign):
            _check_annotation(n.annotation)
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
            elif n.id in FORBIDDEN_BIND:
                # Binden verbotener Builtins ist ueberall gesperrt, also kann dieser Name nur das echte Builtin sein.
                raise Block("Name nicht erlaubt: %s" % n.id)
            # sonst: eigener Name oder undefiniert. Undefiniert ergibt zur Laufzeit NameError, ohne Sicherheitsfolge
            # (kein globals/setattr/Stern-Import, Modulnamen nur aus geprueften Anweisungen).
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
            if any(isinstance(x, (ast.Call, ast.GeneratorExp, ast.ListComp, ast.SetComp, ast.DictComp)) for x in _eager(st)):
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
    """Fuehrt die festen Testdateien aus. Rueckgabe dict mit status PASSED|FAILED|ERROR|TIMEOUT|KILLED|OUTPUT_LIMIT|STATE_CHANGED|NO_TESTS|INFRA.
    STATE_CHANGED: waehrend des Laufs hat sich eine Datei im Run-Ordner geaendert (auch das Zielmodul) = immer Fehlschlag."""
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
    before = file_state(run_dir)  # C-SEC-25: waehrend pytest darf sich im Run-Ordner gar nichts aendern
    try:
        p = subprocess.Popen(cmd, cwd=run_dir, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, start_new_session=True,
                             preexec_fn=_limiter(cpu_s, mem_mb * 1024 * 1024 if mem_mb else 0, fsize_kb * 1024))
        raw, total = bytearray(), 0
        deadline = t0 + timeout_s
        fd = p.stdout.fileno()
        while True:
            left = deadline - time.time()
            if left <= 0:
                status = "TIMEOUT"
                break
            r, _, _ = select.select([fd], [], [], min(left, 0.5))
            if not r:
                continue
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total += len(chunk)
            raw = (raw + chunk)[-OUT_TAIL:]  # nur das Ende behalten, Speicher bleibt begrenzt
            if total > OUT_MAX:
                status = "OUTPUT_LIMIT"
                break
        if status is not None:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        p.stdout.close()
        try:
            rc = p.wait(timeout=max(1.0, deadline - time.time()))
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            rc = p.wait()
            status = status or "TIMEOUT"
        out = raw.decode("utf-8", errors="replace")
    except OSError as e:
        status, out = "INFRA", "Start fehlgeschlagen: %s" % type(e).__name__
    finally:
        shutil.rmtree(side, ignore_errors=True)
    changed = state_diff(before, file_state(run_dir))
    if not changed["ok"]:
        status = "STATE_CHANGED"
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
    res = {"status": status, "rc": rc, "seconds": round(time.time() - t0, 2), "summary": tail[-SUMMARY_MAX:]}
    if not changed["ok"]:
        res["state_violations"] = changed["violations"][:10]
    return res


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
    ("C-SEC-20 Scope-Vergiftung", "def a(open):\n    return open\ndef b(p):\n    return open(p)\n"),
    ("C-SEC-20b Comprehension-Ziel", "def f():\n    xs = [open for open in [1]]\n    return open('x')\n"),
    ("C-SEC-20c Default-Capture", "def a(getattr):\n    return 1\ndef b(x, g=getattr):\n    return g(x, 'real')\n"),
    ("C-SEC-20d Import-Alias", "from math import floor as open\ndef f(p):\n    return open(p)\n"),
    ("C-SEC-20e except-Name", "def f():\n    try:\n        pass\n    except ValueError as eval:\n        pass\n"),
    ("C-SEC-21 Attribut schreiben", "import collections\ndef f():\n    collections.Counter.most_common = None\n"),
    ("C-SEC-21b Attribut loeschen", "import re\ndef f():\n    del re.sub\n"),
    ("C-SEC-21c Attribut AugAssign", "def f(xs):\n    xs.real += 1\n"),
    ("C-SEC-23 Annotation-Aufruf", "def f(x: len('a')) -> int:\n    return x\n"),
    ("C-SEC-23b Return-Comprehension", "def f(x) -> [i for i in [1]]:\n    return x\n"),
    ("C-SEC-23c Annotation-String", "def f(x: 'open(1)'):\n    return x\n"),
    ("C-SEC-23d AnnAssign-Aufruf", "def f():\n    y: len('a') = 1\n    return y\n"),
    ("C-SEC-26 lambda-Koerper mit open", "def f():\n    g = lambda p: open(p)\n    return g\n"),
    ("C-SEC-26b lambda-Default mit Call", "def f():\n    g = lambda x=len('a'): x\n    return g\n"),
    ("C-SEC-26c lambda-Parameter open", "def f():\n    return lambda open: open\n"),
    ("C-SEC-26d lambda sofort auf Modulebene", "X = (lambda: 1)()\ndef f():\n    return X\n"),
    ("C-SEC-26e lambda verschachtelt eval", "def f():\n    return lambda: (lambda: eval)()\n"),
    ("C-SEC-26f def-Default ruft lambda", "def f(g=(lambda: 1)()):\n    return g\n"),
    ("C-SEC-26g lambda-Default auf Modulebene", "F = lambda x=len('a'): x\ndef f():\n    return F\n"),
    ("C-SEC-26h lambda Dunder", "def f():\n    return lambda x: x.__class__\n"),
    ("C-SEC-24 coding-Cookie", "# -*- coding: utf-7 -*-\ndef f():\n    return 1\n"),
    ("C-SEC-24b fileencoding Zeile 2", "#!/usr/bin/env python3\n# vim: set fileencoding=latin-1 :\ndef f():\n    return 1\n"),
    ("C-SEC-24c BOM", "\ufeffdef f():\n    return 1\n"),
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
    ("P-14 erlaubter Builtin als Name", "def f(xs):\n    sum = 0\n    for x in xs:\n        sum += x\n    return sum\n"),
    ("P-19 lambda auf Modulebene", "f = lambda x: len(x)\ndef g(xs):\n    return sorted(xs, key=lambda t: -t[1])\n"),
    ("P-20 def-Default ist lambda", "def f(key=lambda t: t):\n    return key\n"),
    ("P-21 lambda in Funktion sofort", "def f():\n    return (lambda: 1)()\n"),
    ("P-18 undefinierter Name (NameError, kein Angriff)", "def f():\n    return helfer(1) + rest\n"),
    ("P-17 Kommentar spaeter", "def f(s):\n    return s\n# encoding: nur Kommentar in Zeile 3\n"),
    ("P-16 Schluesselwort type=", "def f():\n    return dict(type=1, id=2)\n"),
    ("P-15 einfache Annotationen", "from typing import Optional\ndef f(x: int | None, ys: list[int]) -> Optional[dict[str, int]]:\n    return None\n"),
]

RES = [  # Schicht 2: muessen durch Limits enden, nicht durch das Tor
    ("C-SEC-17 Endlosschleife", "def f():\n    while True:\n        pass\n", ("TIMEOUT", "KILLED", "FAILED")),
    ("C-SEC-18 Speicherbombe", "def f():\n    x = [0] * (10 ** 10)\n    return len(x)\n", ("FAILED", "KILLED")),
    ("C-SEC-18b wachsender Speicher", "def f():\n    x = []\n    for i in range(5000):\n        x.append('a' * 10 ** 6)\n    return len(x)\n", ("FAILED", "KILLED")),
    ("C-SEC-19 tiefe Rekursion", "def f(n=0):\n    return f(n + 1)\n", ("FAILED",)),
    ("C-SEC-22 Ausgabeflut", "def f():\n    raise ValueError('x' * 10 ** 7)\n", ("OUTPUT_LIMIT", "FAILED", "KILLED")),
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
        # C-SEC-25: Datei aendert sich waehrend pytest (simulierter Ausbruch ueber eine Testdatei) -> STATE_CHANGED
        with open(os.path.join(d, "range_sum.py"), "w") as f:
            f.write("def sum_to(n):\n    return sum(range(1, n + 1))\n")
        os.remove(os.path.join(d, "conftest.py"))
        with open(os.path.join(d, "test_range_sum.py"), "w") as f:
            f.write("def test_schreibt():\n    open('range_sum.py', 'a').write('# nachher\\n')\n")
        r = run_pytest(d, ["test_range_sum.py"])
        good = r["status"] == "STATE_CHANGED" and r.get("state_violations") == ["range_sum.py"]
        ok += good
        total += 1
        print("%-30s %s  %s %s" % ("C-SEC-25 Zustand eingefroren", "ok" if good else "FEHLER", r["status"], r.get("state_violations")))
        with open(os.path.join(d, "x.py"), "wb") as f:
            f.write("def f():\n    return 'caf\xe9'\n".encode("latin-1"))
        g = gate_file(os.path.join(d, "x.py"))
        good = g["code"] == "POLICY_BLOCK"
        ok += good
        total += 1
        print("%-30s %s  %s" % ("C-SEC-24d kein UTF-8", "ok" if good else "FEHLER", g["reason"]))
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
