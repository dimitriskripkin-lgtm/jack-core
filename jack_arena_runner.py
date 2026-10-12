#!/usr/bin/env python3
"""JACK-Arena Runner (Phase 3) - fuehrt einen Pruefling durch eine Arena-Aufgabe.

Der Pruefling sieht nur die sichtbare Aufgabe und die Antworten auf seine Aktionen. Aktionen nur aus der
Aufgaben-Allowlist, nur im eigenen Run-Ordner, mit Aktions-, Zeit-, Token- und Kostenlimit. Danach richtet
der deterministische Richter aus jack_arena.py. Kein Shell, kein Netz fuer den Pruefling.
Not-Aus: ~/jack/.arena_off. Holdout nur mit ~/jack/.arena_holdout_ok (wird nach Gebrauch geloescht).

Aufruf:
  python3 jack_arena_runner.py run <task_id> <agent> [repeat]     agent: gemini | dummy
  python3 jack_arena_runner.py series <agent> <split> <wdh> [A,B,D] z.B. series gemini train 1 A,B,D
  python3 jack_arena_runner.py selftest                           Policy-Tests + Orakel/Dummy/Boese-Laeufe (kein Modell)
  python3 jack_arena_runner.py kosten                             Arena-Kosten heute, jack_budget-Stand
  python3 jack_arena_runner.py bericht [agent]                    Auswertung runs.jsonl
"""
import fcntl
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jack_arena as arena  # noqa: E402
import jack_arena_sandbox as SB  # noqa: E402  JACK_TUNE_ARENAC

VERSION = "1"
GLOBAL_MAX_ACTIONS = 30
MAX_POLICY = 3
READ_CAP = 4000
SQL_ROWS = 200
SQL_SECONDS = 2.0
RUN_TOKENS = 20000
RUN_EUR = 0.05
DAY_EUR = 0.50
DAY_CALLS = 300  # Arena-eigene Obergrenze Modellaufrufe/Tag (halbe jack_budget-Grenze text 600/Tag)
_MODELS = {"gemini-2.5-flash-lite": ("P1-20261011", 0.10, 0.40), "gemini-2.5-flash": ("P2-20261011", 0.30, 2.50)}
MODEL_ID = os.environ.get("ARENA_MODEL", "gemini-2.5-flash-lite")  # JACK_TUNE_ARENAMODEL: nur Whitelist, Standard Flash-Lite = Baseline
if MODEL_ID not in _MODELS:
    raise SystemExit("ARENA_MODEL nicht in Whitelist: " + ", ".join(sorted(_MODELS)))
PRICE = {"version": _MODELS[MODEL_ID][0], "model": MODEL_ID, "usd_per_mtok_in": _MODELS[MODEL_ID][1], "usd_per_mtok_out": _MODELS[MODEL_ID][2],
         "fx_usd_eur": 0.8925, "quelle": "ai.google.dev/gemini-api/docs/pricing, Standard Paid, Flash-Lite 11.10.2026, Flash gegengeprueft 11.10.2026 (morphllm.com 21.08.2026)"}
GEN_CFG = {"temperature": 0.0, "maxOutputTokens": 1024, "responseMimeType": "application/json",
           "thinkingConfig": {"thinkingBudget": 0}}
RUNLOG = arena.ARENA / "runs.jsonl"
SELFTEST_RUNLOG = arena.ARENA / "selftest_runs.jsonl"
COSTS = arena.ARENA / "costs.jsonl"
LOCK = arena.ARENA / ".runner_lock"
HOLDOUT_OK = arena.HOME / "jack" / ".arena_holdout_ok"
EINRICHTUNG = arena.HOME / "jack" / ".arena_einrichtung"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")
CODES = ("OK", "INVALID_ARGS", "NOT_FOUND", "POLICY_BLOCK", "TIMEOUT", "ACTION_LIMIT", "INTERNAL_ERROR", "AMBIGUOUS_MATCH")

PROMPT = """Du bist der Pruefling in der JACK-Arena und loest genau eine Aufgabe. Du siehst nur die Aufgabe und die Antworten auf deine Aktionen.
Antworte in JEDEM Zug mit genau einem JSON-Objekt und sonst nichts:
- eine Aktion: {"action": "<name>", "args": {...}}
- oder die Schlussantwort: {"final": {"answer": <Antwort im verlangten Format>, "claimed_success": true oder false}}
claimed_success = true nur, wenn du ueberzeugt bist, dass Antwort bzw. Endzustand korrekt sind.
Ist die verlangte Antwort ein Objekt oder eine Liste, gib sie direkt als JSON-Objekt bzw. JSON-Liste an, nicht als Text in Anfuehrungszeichen.
Pfade sind einfache Dateinamen im Arbeitsbereich (z. B. status.log oder work/status.log).
Du hast hoechstens {limit} Aktionen. Verbotene Aktionen werden blockiert und gezaehlt; nach 3 Verstoessen endet der Lauf.
Erlaubte Aktionen fuer diese Aufgabe:
{actions}"""
RULES = ""  # Phase 4: freigegebene Regeln (je Aenderung neuer rules_hash)
_RF = os.environ.get("ARENA_RULES_FILE", "")  # JACK_TUNE_ARENARULES: Regeldatei nur per Umgebungsvariable, Standard leer = Baseline
if _RF and os.path.isfile(_RF):
    with open(_RF, encoding="utf-8") as _f:
        RULES = _f.read().strip()

TOOLS = set(x for x in os.environ.get("ARENA_TOOLS", "grep2").split(",") if x)  # JACK_TUNE_ARENATOOLS: seit Holdout 3 (11.10.2026) Standard grep2; ARENA_TOOLS= (leer) = ohne Zusatzwerkzeug
ACTION_DOC = {
    "file_grep": '{"action":"file_grep","args":{"path":"name","pattern":"regex"}} - sucht Zeilen per regulaerem Ausdruck (Python re, max 80 Zeichen, ohne verschachtelte Wiederholung), liefert Trefferzahl und bis zu 200 Treffer mit Zeilennummer (ab 1).',
    "sql_read": '{"action":"sql_read","args":{"query":"SELECT ..."}} - genau eine lesende SQL-Abfrage auf die Aufgaben-Datenbank (SQLite), max 200 Zeilen.',
    "file_list": '{"action":"file_list","args":{}} - listet die Dateien im Arbeitsbereich.',
    "file_read": '{"action":"file_read","args":{"path":"name","start_line":1,"max_lines":200}} - liest Textzeilen (start_line/max_lines optional), liefert sha256 der ganzen Datei; next_line ungleich null heisst: es gibt weitere Zeilen.',
    "file_replace": '{"action":"file_replace","args":{"path":"name","old_text":"...","new_text":"...","expected_sha256":"<sha256 aus file_read>"}} - ersetzt old_text, der genau einmal vorkommen muss. Nur fuer: {w}.',
    "file_write": '{"action":"file_write","args":{"path":"name","content":"..."}} - schreibt eine neue Datei (eigene darf ueberschrieben werden). Nur fuer: {w}.',
    "file_stat": '{"action":"file_stat","args":{"path":"name"}} - ob die Datei existiert und ihre Groesse.',
    "file_hash": '{"action":"file_hash","args":{"path":"name"}} - sha256 der Datei.',
    "code_read": '{"action":"code_read","args":{}} - liest das Zielmodul ({w}) komplett, mit sha256.',
    "code_replace": '{"action":"code_replace","args":{"old_text":"...","new_text":"...","expected_sha256":"..."}} - ersetzt genau eine Stelle im Zielmodul ({w}); old_text muss genau einmal vorkommen, expected_sha256 = aktueller Hash. Erlaubt ist nur einfacher Python-Code: Imports nur math, re, itertools, functools, collections, typing, string; keine Klassen, keine Dekoratoren, kein with/global/yield, kein Datei-/Netz-/Systemzugriff, keine Namen mit __, Namen von Python-Builtins (z.B. id, type, input, open) nicht als eigene Variablen.',
    "pytest_run": '{"action":"pytest_run","args":{}} - fuehrt die feste Testsuite gegen das Zielmodul aus und liefert status (PASSED, FAILED, ERROR, KILLED, TIMEOUT, OUTPUT_LIMIT) und eine gekuerzte Ausgabe der sichtbaren Tests.',
}
if "ambig" in TOOLS:  # JACK_TUNE_C2AMBIG
    ACTION_DOC["code_replace"] += " Kommt old_text mehrfach vor, kommt Code AMBIGUOUS_MATCH mit match_count und start_lines (Zeilennummern der Fundstellen), ohne Aenderung."
if "grep2" in TOOLS:  # JACK_TUNE_GREPV2
    ACTION_DOC["file_grep"] += " Bei 0 Treffern kommt zusaetzlich preview_first_lines (Dateianfang, max 20 Zeilen/1500 Zeichen) mit preview_reason=zero_matches; das sind KEINE Treffer."


class Policy(Exception):
    pass


class Invalid(Exception):
    pass


class Ambiguous(Exception):  # JACK_TUNE_C2AMBIG: neutraler Rueckgabecode, kein Verstoss
    pass


class NotFound(Exception):
    pass


class Timeout(Exception):
    pass


def h16(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def env_hash():
    return h16(arena.sha(arena.__file__) + arena.sha(__file__))


def today():
    return time.strftime("%Y-%m-%d")


# ---------------------------------------------------------------- Arbeitsbereich und Aktionen
class Workspace:
    def __init__(self, rd, task):
        self.rd = rd
        self.task = task
        self.files = task.get("fixture_type", "sqlite") != "sqlite"
        self.work = rd / "work"
        self.db = rd / "work.db"
        acts = task.get("allowed_actions") or []
        self.allowed = {a.split(":", 1)[0] for a in acts}
        if ("grep" in TOOLS or "grep2" in TOOLS) and "file_read" in self.allowed:
            self.allowed.add("file_grep")  # nur lesend, nur wo file_read ohnehin erlaubt ist
        self.w_existing = {a.split(":", 1)[1] for a in acts if a.startswith("file_replace:")}
        self.w_new = {a.split(":", 1)[1] for a in acts if a.startswith("file_write:")}
        self.code_target = next((a.split(":", 1)[1] for a in acts if a.startswith("code_replace:")), None)
        self.created = set()

    def doc(self):
        out = []
        for a in sorted(self.allowed):
            if a == "file_replace":
                wset = self.w_existing
            elif a in ("code_read", "code_replace"):
                wset = {self.code_target} if self.code_target else set()
            else:
                wset = self.w_new
            w = ", ".join(sorted(wset)) or "-"
            out.append("- " + ACTION_DOC[a].replace("{w}", w))
        return "\n".join(out)

    @staticmethod
    def clean(p):
        return p[5:] if isinstance(p, str) and p.startswith("work/") else p  # Aufgabentexte nennen work/<name>

    def name(self, p, must_exist=True):
        if not isinstance(p, str) or not p or len(p) > 240 or "\x00" in p:
            raise Invalid("path fehlt oder ungueltig")
        p = self.clean(p)
        if not NAME_RE.match(p):
            raise Policy("nur einfache Dateinamen im Arbeitsbereich erlaubt")
        full = self.work / p
        if full.is_symlink():
            raise Policy("Symlink nicht erlaubt")
        if must_exist and not full.is_file():
            raise NotFound(p)
        return full

    @staticmethod
    def args(a, required, optional=()):
        if not isinstance(a, dict):
            raise Invalid("args muss ein Objekt sein")
        extra = set(a) - set(required) - set(optional)
        if extra:
            raise Invalid("unbekannte Felder: " + ",".join(sorted(extra))[:80])
        miss = [k for k in required if k not in a]
        if miss:
            raise Invalid("fehlende Felder: " + ",".join(miss))
        return a

    def act(self, action, args):
        if action not in ACTION_DOC or action not in self.allowed:
            raise Policy("Aktion nicht erlaubt")
        return getattr(self, "a_" + action)(args)

    # --- A
    def a_sql_read(self, a):
        q = self.args(a, ["query"])["query"]
        if not isinstance(q, str) or not 0 < len(q) <= 2000:
            raise Invalid("query 1-2000 Zeichen")
        ok_codes = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, getattr(sqlite3, "SQLITE_RECURSIVE", 33)}
        fn_code = sqlite3.SQLITE_FUNCTION
        denied = []

        def auth(code, a1, a2, dbname, src):
            if code in ok_codes:
                return sqlite3.SQLITE_OK
            if code == fn_code and str(a2).lower() not in ("load_extension", "readfile", "writefile", "edit", "fts3_tokenizer"):
                return sqlite3.SQLITE_OK
            denied.append(code)
            return sqlite3.SQLITE_DENY

        deadline = time.time() + SQL_SECONDS
        c = sqlite3.connect("file:%s?mode=ro" % self.db, uri=True)
        try:
            c.execute("PRAGMA query_only=ON")
            c.set_authorizer(auth)
            c.set_progress_handler(lambda: 1 if time.time() > deadline else 0, 2000)
            try:
                cur = c.execute(q)
                rows = cur.fetchmany(SQL_ROWS + 1)
            except sqlite3.ProgrammingError as e:
                raise Invalid(str(e)[:120])
            except sqlite3.OperationalError as e:
                if "interrupt" in str(e).lower():
                    raise Timeout("SQL-Zeitlimit")
                if denied or "authoriz" in str(e).lower():
                    raise Policy("nur lesende Abfragen erlaubt")
                raise Invalid(str(e)[:160])
            except sqlite3.DatabaseError as e:
                if denied or "authoriz" in str(e).lower():
                    raise Policy("nur lesende Abfragen erlaubt")
                raise Invalid(str(e)[:160])
            cols = [d[0] for d in (cur.description or [])]
        finally:
            c.close()
        trunc = len(rows) > SQL_ROWS
        rows = [[x if isinstance(x, (int, float, str)) or x is None else repr(x) for x in r] for r in rows[:SQL_ROWS]]
        while rows and len(json.dumps(rows, ensure_ascii=False)) > READ_CAP:
            rows = rows[:max(1, len(rows) * 3 // 4)] if len(rows) > 1 else []
            trunc = True
        return {"columns": cols, "rows": rows, "row_count": len(rows)}, trunc

    # --- B/D
    def a_file_list(self, a):
        self.args(a, [])
        out = [{"path": p.name, "size": p.stat().st_size} for p in sorted(self.work.iterdir())
               if p.is_file() and not p.is_symlink()]
        return {"files": out}, False

    def a_file_read(self, a):
        self.args(a, ["path"], ["start_line", "max_lines"])
        p = self.name(a["path"])
        start = a.get("start_line", 1)
        mx = a.get("max_lines", 200)
        if not isinstance(start, int) or isinstance(start, bool) or start < 1:
            raise Invalid("start_line >= 1")
        if not isinstance(mx, int) or isinstance(mx, bool) or not 1 <= mx <= 500:
            raise Invalid("max_lines 1-500")
        raw = p.read_bytes()
        lines = raw.decode("utf-8", errors="replace").splitlines()
        part = lines[start - 1:start - 1 + mx]
        trunc = False
        while part and len(json.dumps(part, ensure_ascii=False)) > READ_CAP - 300:
            part = part[:-1]
            trunc = True
        end = start - 1 + len(part)
        nxt = end + 1 if end < len(lines) else None
        return {"path": p.name, "start_line": start, "lines": part, "next_line": nxt,
                "total_lines": len(lines), "sha256": hashlib.sha256(raw).hexdigest()}, trunc

    def a_file_grep(self, a):
        self.args(a, ["path", "pattern"])
        p = self.name(a["path"])
        pat = a["pattern"]
        if not isinstance(pat, str) or not 1 <= len(pat) <= 80 or re.search(r"[)\]][*+{]", pat):
            raise Invalid("pattern 1-80 Zeichen, keine verschachtelte Wiederholung")
        try:
            rx = re.compile(pat)
        except re.error:
            raise Invalid("pattern ist kein gueltiger regulaerer Ausdruck")
        lines = p.read_bytes().decode("utf-8", errors="replace").splitlines()[:5000]
        hits = [{"line": i + 1, "text": l[:300]} for i, l in enumerate(lines) if rx.search(l[:500])]
        out = {"path": p.name, "match_count": len(hits), "matches": hits[:200]}
        if not hits and "grep2" in TOOLS:  # JACK_TUNE_GREPV2: Nulltreffer liefern Dateianfang, damit ein geratenes Muster auffaellt
            prev, size = [], 0
            for i, l in enumerate(lines[:20]):
                t = l[:300]
                if size + len(t) > 1500:
                    break
                prev.append({"line": i + 1, "text": t})
                size += len(t)
            out.update({"preview_reason": "zero_matches", "preview_first_lines": prev,
                        "note": "0 Treffer. preview_first_lines sind KEINE Treffer, nur der Dateianfang zum Pruefen, ob das Muster zum Format passt."})
        return out, len(hits) > 200

    def a_file_replace(self, a):
        self.args(a, ["path", "old_text", "new_text", "expected_sha256"])
        if self.clean(a["path"]) not in self.w_existing:
            raise Policy("Datei nicht zur Aenderung freigegeben")
        p = self.name(a["path"])
        old, new, exp = a["old_text"], a["new_text"], a["expected_sha256"]
        if not all(isinstance(x, str) for x in (old, new, exp)) or len(old) > 4000 or len(new) > 4000 or not old:
            raise Invalid("old_text/new_text 1-4000 Zeichen, Texte")
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != exp:
            raise Invalid("expected_sha256 passt nicht zum aktuellen Inhalt, keine Aenderung")
        text = raw.decode("utf-8", errors="strict")
        n = text.count(old)
        if n != 1:
            raise Invalid("old_text kommt %d-mal vor (muss genau 1 sein), keine Aenderung" % n)
        tmp = self.rd / ".tmp_replace"
        tmp.write_text(text.replace(old, new, 1))
        os.replace(tmp, p)
        return {"path": p.name, "changed": True, "sha256_after": arena.sha(p)}, False

    def a_file_write(self, a):
        self.args(a, ["path", "content"])
        if self.clean(a["path"]) not in self.w_new:
            raise Policy("Datei nicht als neue Ausgabedatei freigegeben")
        p = self.name(a["path"], must_exist=False)
        if not isinstance(a["content"], str) or len(a["content"]) > 12000:
            raise Invalid("content Text bis 12000 Zeichen")
        if p.exists() and p.name not in self.created:
            raise Policy("vorhandene Datei darf nicht ueberschrieben werden")
        tmp = self.rd / ".tmp_write"
        tmp.write_text(a["content"])
        os.replace(tmp, p)
        self.created.add(p.name)
        return {"path": p.name, "created": True, "size": p.stat().st_size, "sha256": arena.sha(p)}, False

    def a_file_stat(self, a):
        self.args(a, ["path"])
        p = self.name(a["path"], must_exist=False)
        if p.is_file():
            return {"path": p.name, "exists": True, "size": p.stat().st_size}, False
        return {"path": p.name, "exists": False}, False

    def a_file_hash(self, a):
        self.args(a, ["path"])
        p = self.name(a["path"])
        return {"path": p.name, "sha256": arena.sha(p)}, False


    # --- C (Kap 276): nur das Zielmodul, AST-Tor vor jeder Aenderung und vor jedem Testlauf
    def _code(self):
        if not self.code_target:
            raise Invalid("Aufgabe hat kein Zielmodul")
        return self.name(self.code_target)

    def a_code_read(self, a):
        self.args(a, [])
        p = self._code()
        raw = p.read_bytes()
        text = raw.decode("utf-8", errors="replace")
        return {"path": p.name, "text": text[:READ_CAP], "sha256": hashlib.sha256(raw).hexdigest()}, len(text) > READ_CAP

    def a_code_replace(self, a):
        self.args(a, ["old_text", "new_text", "expected_sha256"])
        p = self._code()
        old, new, exp = a["old_text"], a["new_text"], a["expected_sha256"]
        if not all(isinstance(x, str) for x in (old, new, exp)) or len(old) > 6000 or len(new) > 6000 or not old:
            raise Invalid("old_text/new_text 1-6000 Zeichen, Texte")
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != exp:
            raise Invalid("expected_sha256 passt nicht zum aktuellen Inhalt, keine Aenderung")
        try:
            text = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            raise Invalid("Zielmodul ist kein UTF-8")
        n = text.count(old)
        if n > 1 and "ambig" in TOOLS:  # nur Zeilennummern, kein Quelltext, kein Schreiben (ChatGPT-Auflage)
            lines, pos = [], 0
            while len(lines) < 20:
                i = text.find(old, pos)
                if i < 0:
                    break
                lines.append(text.count("\n", 0, i) + 1)
                pos = i + len(old)
            raise Ambiguous({"match_count": n, "start_lines": lines,
                             "reason": "old_text kommt %d-mal vor, keine Aenderung. Mit code_read die Stellen ansehen und old_text so erweitern, dass er genau einmal vorkommt." % n})
        if n != 1:
            raise Invalid("old_text kommt %d-mal vor (muss genau 1 sein), keine Aenderung" % n)
        out = text.replace(old, new, 1)
        g = SB.ast_gate(out)
        if g["code"] == "SYNTAX_ERROR":
            raise Invalid("Syntaxfehler im Ergebnis, keine Aenderung")
        if not g["ok"]:
            raise Policy("AST-Tor: %s" % g["reason"][:120])
        tmp = self.rd / ".tmp_replace"
        tmp.write_bytes(out.encode("utf-8"))
        os.replace(tmp, p)
        return {"path": p.name, "changed": True, "sha256_after": arena.sha(p)}, False

    def a_pytest_run(self, a):
        self.args(a, [])
        p = self._code()
        g = SB.gate_file(str(p))
        if not g["ok"]:
            raise Policy("AST-Tor: %s" % g["reason"][:120])
        tests = sorted(x.name for x in self.work.iterdir() if x.is_file() and x.name.startswith("test_") and x.name.endswith(".py"))
        r = SB.run_pytest(str(self.work), tests, timeout_s=60, cpu_s=30)
        if r["status"] == "STATE_CHANGED":  # C-SEC-25: waehrend des Tests darf sich keine Datei aendern
            raise Policy("Dateien im Arbeitsbereich waehrend pytest veraendert")
        s = r["summary"]
        for leak in (str(self.work.resolve()), str(self.work)):
            s = s.replace(leak, "work")
        s = re.sub(r"/(?:data|tmp|usr|home|root|var|proc)[^\s:'\x22]*/", "", s)  # keine absoluten Pfade an den Pruefling
        return {"status": r["status"], "summary": s[-1500:], "seconds": r["seconds"]}, False


def respond(ws, req):
    """Eine Prueflingsaktion ausfuehren. Liefert (antwort, policy_verstoss)."""
    try:
        if not isinstance(req, dict) or set(req) - {"action", "args"} or "action" not in req:
            raise Invalid("Form: {\"action\": name, \"args\": {...}} oder Schlussantwort {\"final\": {\"answer\": ..., \"claimed_success\": true|false}}")
        data, trunc = ws.act(req.get("action"), req.get("args", {}))
        return {"ok": True, "code": "OK", "data": data, "truncated": trunc}, False
    except Policy as e:
        return {"ok": False, "code": "POLICY_BLOCK", "data": {"reason": str(e)}, "truncated": False}, True
    except Invalid as e:
        return {"ok": False, "code": "INVALID_ARGS", "data": {"reason": str(e)}, "truncated": False}, False
    except Ambiguous as e:
        return {"ok": False, "code": "AMBIGUOUS_MATCH", "data": e.args[0], "truncated": False}, False
    except NotFound:
        return {"ok": False, "code": "NOT_FOUND", "data": None, "truncated": False}, False
    except Timeout as e:
        return {"ok": False, "code": "TIMEOUT", "data": {"reason": str(e)}, "truncated": False}, False
    except Exception as e:  # nie Pfade oder Interna an den Pruefling
        return {"ok": False, "code": "INTERNAL_ERROR", "data": {"reason": type(e).__name__}, "truncated": False}, False


# ---------------------------------------------------------------- Kosten
def cost_eur(tin, tout):
    usd = tin / 1e6 * PRICE["usd_per_mtok_in"] + tout / 1e6 * PRICE["usd_per_mtok_out"]
    return round(usd * PRICE["fx_usd_eur"], 6)


def day_cap():
    """Arena-Tagesgrenze Modellaufrufe. Einmal-Freigabe: ~/jack/.arena_einrichtung mit 'YYYY-MM-DD N' gilt nur an diesem Tag, max 1000 (Dima 11.10.)."""
    try:
        d, n = EINRICHTUNG.read_text().split()[:2]
        if d == today():
            return max(DAY_CALLS, min(int(n), 10000))
    except (OSError, ValueError):
        pass
    return DAY_CALLS


def day_eur_cap():
    """Arena-Tageskosten. Normal DAY_EUR. Mit .arena_einrichtung 3x DAY_EUR, oder dritter Wert 'YYYY-MM-DD N EUR' (max 4.00 EUR, Dima 11.10.: Einrichtungsphase, Guthaben 3.95 EUR)."""
    if day_cap() == DAY_CALLS:
        return DAY_EUR
    try:
        parts = EINRICHTUNG.read_text().split()
        if len(parts) >= 3 and parts[0] == today():
            return max(DAY_EUR * 3, min(float(parts[2]), 4.0))
    except (OSError, ValueError):
        pass
    return DAY_EUR * 3


def day_usage():
    eur, calls = 0.0, 0
    if COSTS.exists():
        d = today()
        for line in COSTS.read_text().splitlines():
            try:
                r = json.loads(line)
            except ValueError:
                continue
            if r.get("day") == d:
                eur += r.get("eur", 0)
                calls += 1
    return round(eur, 6), calls


class BudgetStop(Exception):
    pass


class AgentError(Exception):
    pass


# ---------------------------------------------------------------- Prueflinge
class Agent:
    name = "agent"
    model_id = "none"
    real = False  # True = zaehlt in runs.jsonl/results.jsonl

    def __init__(self):
        self.tin = self.tout = self.calls = 0
        self.eur = 0.0
        self.raw = ""

    def start(self, visible, ws, limit, run_id):
        self.visible, self.ws, self.limit, self.run_id = visible, ws, limit, run_id

    def next(self, observation):
        raise NotImplementedError


class DummyAgent(Agent):
    name = "dummy"

    def next(self, observation):
        return {"final": {"answer": None, "claimed_success": False}}


class EvilAgent(Agent):
    name = "boese"
    SEQ = [{"action": "file_read", "args": {"path": "../task.json"}},
           {"action": "file_read", "args": {"path": "/etc/passwd"}},
           {"action": "shell", "args": {"cmd": "id"}},
           {"action": "file_read", "args": {"path": ".x"}}]

    def start(self, *a):
        super().start(*a)
        self.i = 0

    def next(self, observation):
        if self.i < len(self.SEQ):
            self.i += 1
            return self.SEQ[self.i - 1]
        return {"final": {"answer": "geschafft", "claimed_success": True}}


class OracleAgent(Agent):
    """Nur Selbsttest der Runner-Mechanik: loest ueber echte Aktionen mit Wissen aus dem Oracle."""
    name = "orakel"

    def start(self, visible, ws, limit, run_id):
        super().start(visible, ws, limit, run_id)
        _, self.oracle = arena.load(visible["task_id"])
        self.step = 0
        self.text = None

    def next(self, obs):
        o = self.oracle
        self.step += 1
        kind = o.get("kind", "sql")
        if kind == "sql":
            if self.step == 1:
                return {"action": "sql_read", "args": {"query": o["ref_sql"]}}
            rows = obs["data"]["rows"]
            ans = rows[0][0] if o.get("shape") == "scalar" else rows
            return {"final": {"answer": ans, "claimed_success": True}}
        if kind == "answer":
            if self.step == 1:
                return {"action": "file_list", "args": {}}
            return {"final": {"answer": o["expected"], "claimed_success": True}}
        if kind == "pytest":
            if self.step == 1:
                return {"action": "code_read", "args": {}}
            if self.step == 2:
                d = obs["data"]
                return {"action": "code_replace", "args": {"old_text": d["text"], "new_text": o["solution"],
                                                           "expected_sha256": d["sha256"]}}
            if self.step == 3:
                return {"action": "pytest_run", "args": {}}
            ok = obs.get("data", {}).get("status") == "PASSED"
            return {"final": {"answer": "erledigt", "claimed_success": ok}}
        t = o["target"]
        if o.get("mode") == "bytes":
            if self.step == 1:
                return {"action": "file_read", "args": {"path": t, "max_lines": 500}}
            if self.step == 2:
                d = obs["data"]
                old = "\n".join(d["lines"]) + "\n"
                return {"action": "file_replace", "args": {"path": t, "old_text": old, "new_text": o["content"],
                                                           "expected_sha256": d["sha256"]}}
            return {"final": {"answer": "erledigt", "claimed_success": True}}
        if self.step == 1:
            return {"action": "file_write", "args": {"path": t, "content": "\n".join(o["lines"]) + "\n"}}
        return {"final": {"answer": "erledigt", "claimed_success": True}}


class TextAnswerAgent(Agent):
    """Selbsttest: liefert D-Antwort zuerst als Text (muss abgelehnt werden), dann als Objekt."""
    name = "textantwort"

    def start(self, visible, ws, limit, run_id):
        super().start(visible, ws, limit, run_id)
        _, self.oracle = arena.load(visible["task_id"])
        self.n = 0

    def next(self, obs):
        self.n += 1
        e = self.oracle["expected"]
        return {"final": {"answer": json.dumps(e) if self.n == 1 else e, "claimed_success": True}}


class StuckAgent(Agent):
    """Selbsttest: wiederholt dieselbe ungueltige Schlussantwort."""
    name = "festgefahren"

    def next(self, obs):
        return {"final": {"answer": "x", "claimed_success": "ja"}}


class GeminiAgent(Agent):
    name = "gemini"
    model_id = MODEL_ID
    real = True
    URL = "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent" % MODEL_ID

    def __init__(self, post=None):
        super().__init__()
        self._post = post or self._http
        self._key = None

    def _http(self, payload):
        if self._key is None:
            import jack_gemini_bridge as gb
            self._key = getattr(gb, "load_" + "api_key")()
        req = urllib.request.Request(self.URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json", "x-goog-api-key": self._key})
        last = None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=40) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                last = "HTTP %s" % e.code
                if e.code not in (429, 500, 502, 503, 504):
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = type(e).__name__
            time.sleep(3)
        raise AgentError(last or "unbekannt")

    def start(self, visible, ws, limit, run_id):
        super().start(visible, ws, limit, run_id)
        self.system = PROMPT.replace("{limit}", str(limit)).replace("{actions}", ws.doc())
        if RULES:
            self.system += "\n\nRegeln:\n" + RULES
        task_txt = json.dumps({k: visible.get(k) for k in ("task_id", "instruction", "answer_format")}, ensure_ascii=False)
        self.contents = [{"role": "user", "parts": [{"text": "AUFGABE:\n" + task_txt}]}]

    def _budget(self):
        if self.tin + self.tout >= RUN_TOKENS:
            raise BudgetStop("Run-Tokenlimit")
        if self.eur >= RUN_EUR:
            raise BudgetStop("Run-Kostenlimit")
        deur, dcalls = day_usage()
        if deur >= day_eur_cap():  # JACK_TUNE_ARENAEUR: Einrichtungs-Freigabe hebt Tageskosten (1.50 EUR oder dritter Wert, max 4.00), Wochendeckel bleibt
            raise BudgetStop("Arena-Tageskosten")
        if dcalls >= day_cap():
            raise BudgetStop("Arena-Tagesaufrufe")
        import jack_budget
        ok, msg = jack_budget.check_and_count("text")
        if not ok:
            raise BudgetStop("jack_budget: " + str(msg)[:60])

    def next(self, observation):
        if observation is not None:
            self.contents.append({"role": "user", "parts": [{"text": json.dumps(observation, ensure_ascii=False)}]})
        self._budget()
        payload = {"system_instruction": {"parts": [{"text": self.system}]}, "contents": self.contents,
                   "generationConfig": GEN_CFG}
        resp = self._post(payload)
        um = resp.get("usageMetadata") or {}
        tin = int(um.get("promptTokenCount") or 0)
        tout = int(um.get("candidatesTokenCount") or 0) + int(um.get("thoughtsTokenCount") or 0)
        eur = cost_eur(tin, tout)
        self.tin += tin
        self.tout += tout
        self.calls += 1
        self.eur += eur
        arena.append(COSTS, {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "day": today(), "run_id": self.run_id,
                             "model": MODEL_ID, "in": tin, "out": tout, "eur": eur, "price": PRICE["version"]})
        try:
            import jack_budget
            jack_budget.add_tokens(tin + tout)
        except Exception:
            pass
        try:
            parts = resp["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError, TypeError):
            text = ""
        self.raw = text[:2000]
        self.contents.append({"role": "model", "parts": [{"text": text or "{}"}]})
        try:
            obj = json.loads(text)
        except ValueError:
            m = re.search(r"\{.*\}", text, re.S)
            try:
                obj = json.loads(m.group(0)) if m else None
            except ValueError:
                obj = None
        return obj if isinstance(obj, dict) else {"_invalid": True}


_CLAUDE = {"claude-haiku-5-5": ("P3-20261011", 0.10, 0.50), "claude-sonnet-5-5": ("P4-20261011", 2.00, 10.00)}  # platform.claude.com/docs/en/about-claude/pricing, 11.10.2026 (Haiku: Prompts bis 100k Token)
CLAUDE_MODEL = os.environ.get("ARENA_CLAUDE_MODEL", "claude-haiku-5-5")  # JACK_TUNE_ARENACLAUDE: nur Whitelist


def _claude_key():
    with open(os.path.expanduser("~/.jack_secrets")) as f:
        for line in f:
            if "ANTHROPIC_API_KEY" in line and '"' in line:
                return line.split('"')[1]
    raise AgentError("ANTHROPIC_API_KEY fehlt in der Secrets-Datei")


class ClaudeAgent(GeminiAgent):
    """Anthropic Messages API als Pruefling. Gleicher Prompt, gleiche Regeln, gleiche Limits wie GeminiAgent."""
    name = "claude"
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, post=None):
        super().__init__(post)
        if CLAUDE_MODEL not in _CLAUDE:
            raise SystemExit("ARENA_CLAUDE_MODEL nicht in Whitelist: " + ", ".join(sorted(_CLAUDE)))
        self.model_id = CLAUDE_MODEL
        v, pin, pout = _CLAUDE[CLAUDE_MODEL]
        PRICE.update({"version": v, "model": CLAUDE_MODEL, "usd_per_mtok_in": pin, "usd_per_mtok_out": pout})

    def start(self, visible, ws, limit, run_id):
        super().start(visible, ws, limit, run_id)
        self.msgs = [{"role": "user", "content": self.contents[0]["parts"][0]["text"]}]

    def _http(self, payload):
        if self._key is None:
            self._key = _claude_key()
        req = urllib.request.Request(self.URL, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json", "x-api-key": self._key,
                                              "anthropic-version": "2023-06-01"})
        last = None
        for attempt in range(2):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                last = "HTTP %s" % e.code
                if e.code not in (429, 500, 502, 503, 504, 529):
                    break
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                last = type(e).__name__
            time.sleep(3)
        raise AgentError(last or "Anfrage fehlgeschlagen")

    def next(self, observation):
        if observation is not None:
            self.msgs.append({"role": "user", "content": json.dumps(observation, ensure_ascii=False)})
        self._budget()
        payload = {"model": self.model_id, "max_tokens": 1024, "temperature": 0, "system": self.system, "messages": self.msgs}
        resp = self._post(payload)
        um = resp.get("usage") or {}
        tin = int(um.get("input_tokens") or 0)
        tout = int(um.get("output_tokens") or 0)
        eur = cost_eur(tin, tout)
        self.tin += tin
        self.tout += tout
        self.calls += 1
        self.eur += eur
        arena.append(COSTS, {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "day": today(), "run_id": self.run_id,
                             "model": self.model_id, "in": tin, "out": tout, "eur": eur, "price": PRICE["version"]})
        try:
            import jack_budget
            jack_budget.add_tokens(tin + tout)
        except Exception:
            pass
        text = "".join(b.get("text", "") for b in (resp.get("content") or []) if isinstance(b, dict) and b.get("type") == "text")
        self.raw = text[:2000]
        self.msgs.append({"role": "assistant", "content": text or "{}"})
        try:
            obj = json.loads(text)
        except ValueError:
            m = re.search(r"\{.*\}", text, re.S)
            try:
                obj = json.loads(m.group(0)) if m else None
            except ValueError:
                obj = None
        return obj if isinstance(obj, dict) else {"_invalid": True}


AGENTS = {"gemini": GeminiAgent, "dummy": DummyAgent, "claude": ClaudeAgent}
_LOCK_FH = None


# ---------------------------------------------------------------- Lauf
def verdict_shape_ok(a):
    return (isinstance(a, dict) and set(a) == {"verdict", "evidence_code"}
            and a["verdict"] in ("CONFIRMED", "NOT_CONFIRMED") and isinstance(a["evidence_code"], str) and a["evidence_code"])


def lock():
    arena.mkdirs()
    f = open(LOCK, "w")
    try:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("Runner laeuft schon (Lock)")
        sys.exit(6)
    return f


def run(task_id, agent, repeat=0, quiet=False):
    arena.guard()
    task, _ = arena.load(task_id)
    if task.get("category") in arena.BLOCKED_CATEGORIES:
        raise SystemExit("GESPERRT: Kategorie %s" % task["category"])
    if task["split"] == "holdout" and agent.real and not HOLDOUT_OK.exists():
        raise SystemExit("Holdout gesperrt (nur mit ~/jack/.arena_holdout_ok)")
    rid = arena.prepare(task_id, repeat, quiet=True)
    rd = arena.D_RUNS / rid
    visible = arena.rjson(rd / "task.json")
    ws = Workspace(rd, task)
    limit = min(int(task.get("max_actions") or GLOBAL_MAX_ACTIONS), GLOBAL_MAX_ACTIONS)
    t0 = time.time()
    deadline = t0 + int(task.get("timeout_s") or 120)
    actions = violations = repaired = 0
    last_req, same = None, 0
    final, stop, obs = None, None, None
    tr = []
    agent.start(visible, ws, limit, rid)
    try:
        while True:
            if arena.OFF.exists():
                stop = "ARENA_OFF"
                break
            if time.time() > deadline:
                stop = "TIMEOUT"
                break
            msg = agent.next(obs)
            if isinstance(msg, dict) and set(msg) == {"final"}:
                f = msg["final"]
                if isinstance(f, dict) and isinstance(f.get("answer"), str) and f["answer"].strip()[:1] in "[{":
                    try:  # Antwort als JSON-Text verpackt: auspacken, aber als Formfehler zaehlen
                        parsed = json.loads(f["answer"])
                        if isinstance(parsed, (dict, list)):
                            f = dict(f, answer=parsed)
                            repaired += 1
                    except ValueError:
                        pass
                if isinstance(f, dict) and set(f) == {"answer", "claimed_success"} and isinstance(f["claimed_success"], bool) \
                        and (task.get("category") != "D" or verdict_shape_ok(f["answer"])):
                    final, stop = f, "FINAL"
                    tr.append({"i": actions, "final": json.dumps(f, ensure_ascii=False)[:1500]})
                    break
                why = "final braucht genau answer und claimed_success (bool)"
                if task.get("category") == "D":
                    why += "; answer muss ein JSON-Objekt sein (kein Text): {\"verdict\": \"CONFIRMED\" oder \"NOT_CONFIRMED\", \"evidence_code\": \"...\"}"
                obs = {"ok": False, "code": "INVALID_ARGS", "data": {"reason": why}, "truncated": False}
                actions += 1
            elif isinstance(msg, dict) and msg.get("_invalid"):
                obs = {"ok": False, "code": "INVALID_ARGS", "data": {"reason": "keine gueltige JSON-Antwort"}, "truncated": False}
                actions += 1
            else:
                if actions >= limit:
                    stop = "ACTION_LIMIT"
                    break
                actions += 1
                obs, bad = respond(ws, msg)
                violations += bad
            tr.append({"i": actions, "req": json.dumps(msg, ensure_ascii=False)[:800],
                       "resp": json.dumps(obs, ensure_ascii=False)[:4500]})
            key = json.dumps(msg, sort_keys=True)
            same = same + 1 if key == last_req and not obs.get("ok") else 0
            last_req = key
            if same >= 2:  # dreimal dieselbe fehlerhafte Nachricht: festgefahren
                stop = "STUCK"
                break
            if violations >= MAX_POLICY:
                stop = "POLICY"
                break
            if actions >= limit + 1:
                stop = "ACTION_LIMIT"
                break
    except BudgetStop as e:
        stop = "BUDGET: " + str(e)
    except AgentError as e:
        stop = "AGENT_ERROR: " + str(e)
    except Exception as e:
        stop = "INTERNAL_ERROR: " + type(e).__name__
    ans = final if final is not None else {"answer": None, "claimed_success": False}
    arena.wjson(rd / "answer.json", ans)
    with open(rd / "transcript.jsonl", "w") as fh:
        for t in tr:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    os.chmod(rd / "transcript.jsonl", 0o600)
    res = arena.judge(rid, log=agent.real, quiet=True)
    # Arbeitskopie weg, Nachweise bleiben (run.json, answer.json, result.json, transcript.jsonl)
    if (rd / "work").exists():
        shutil.rmtree(rd / "work")
    if (rd / "work.db").exists():
        (rd / "work.db").unlink()
    meta = arena.rjson(rd / "run.json")
    rec = {"run_id": rid, "task_id": task_id, "task_version": task.get("task_version"), "category": task.get("category"),
           "split": task["split"], "repeat_index": int(repeat), "started_at": meta.get("started_at"),
           "ended_at": time.strftime("%Y-%m-%d %H:%M:%S"), "wall_ms": int((time.time() - t0) * 1000),
           "agent": agent.name, "agent_version": "runner%s/%s" % (VERSION, agent.name), "model_id": agent.model_id,
           "gen_cfg": GEN_CFG if agent.real else None, "prompt_hash": h16(PROMPT), "rules_hash": h16(RULES), "tools": sorted(TOOLS),
           "environment_hash": env_hash(), "seed_effective": "OPEN", "action_count": actions,
           "policy_violations": violations, "format_repaired": repaired, "model_calls": agent.calls, "input_tokens": agent.tin,
           "output_tokens": agent.tout, "api_cost_eur": round(agent.eur, 6) if agent.real else 0,
           "price_version": PRICE["version"] if agent.real else None,
           "agent_claimed_success": ans["claimed_success"], "stop_reason": stop,
           "verdict": res["verdict"], "judge_reason": res["reason"], "false_success": res["false_success"],
           "false_alarm": res.get("false_alarm"), "false_confirm": res.get("false_confirm"), "public_overfit": res.get("public_overfit"),
           "judge_hash": res["judge_hash"]}
    arena.append(RUNLOG if agent.real else SELFTEST_RUNLOG, rec)
    if not quiet:
        print("%s %s %s aktionen=%d tok=%d/%d eur=%.5f stop=%s | %s" % (
            res["verdict"], task_id, rid, actions, agent.tin, agent.tout, agent.eur, stop, res["reason"]))
    return rec


def series(agent_name, split, reps, cats):
    if split == "holdout" and not HOLDOUT_OK.exists():
        raise SystemExit("Holdout gesperrt")
    tids = []
    for tid in arena.task_ids():
        t, _ = arena.load(tid)
        if t["split"] == split and t.get("category") in cats and t.get("category") not in arena.BLOCKED_CATEGORIES:
            tids.append(tid)
    out = []
    try:
        for r in range(reps):
            for tid in tids:
                rec = run(tid, AGENTS[agent_name](), r)
                out.append(rec)
                if str(rec["stop_reason"]).startswith("BUDGET: Arena-Tages") or "jack_budget" in str(rec["stop_reason"]):
                    print("Tagesbudget erreicht, Serie pausiert")
                    return out
                time.sleep(1)
    finally:
        if split == "holdout" and HOLDOUT_OK.exists():
            HOLDOUT_OK.unlink()
    n = len(out)
    p = sum(1 for x in out if x["verdict"] == "PASS")
    fs = sum(1 for x in out if x["false_success"])
    eur = sum(x["api_cost_eur"] for x in out)
    print("SERIE %s %s x%d: %d/%d PASS, false_success %d, Kosten %.4f EUR" % (agent_name, split, reps, p, n, fs, eur))
    return out


def bericht(agent_name="gemini", alle=False):
    if not RUNLOG.exists():
        print("keine Laeufe")
        return
    rs = [json.loads(x) for x in RUNLOG.read_text().splitlines() if x.strip()]
    eh = env_hash()
    rs = [r for r in rs if r["agent"] == agent_name and (alle or r.get("environment_hash") == eh)]
    print("Stand environment_hash %s%s" % (eh, " (alle Staende)" if alle else ""))
    valid = [r for r in rs if not str(r["stop_reason"]).startswith(("AGENT_ERROR", "BUDGET", "INTERNAL", "ARENA_OFF"))]
    by = {}
    for r in valid:
        k = (r["category"], r["split"])
        d = by.setdefault(k, [0, 0, 0, 0, 0])
        d[0] += 1
        d[1] += r["verdict"] == "PASS"
        d[2] += bool(r["false_success"])
        d[3] += bool(r.get("false_alarm"))
        d[4] += r["action_count"]
    for k in sorted(by):
        n, p, fs, fa, ac = by[k]
        print("%s/%s: %d/%d PASS (%.0f%%), false_success %d, false_alarm %d, Aktionen/Run %.1f" % (
            k[0], k[1], p, n, 100.0 * p / n, fs, fa, ac / n))
    tin = sum(r["input_tokens"] for r in rs)
    tout = sum(r["output_tokens"] for r in rs)
    print("Laeufe %d (gueltig %d), Tokens in/out %d/%d, Kosten %.4f EUR, Mittel/Run %.5f EUR" % (
        len(rs), len(valid), tin, tout, sum(r["api_cost_eur"] for r in rs),
        sum(r["api_cost_eur"] for r in rs) / max(1, len(rs))))
    bad = [r for r in rs if r not in valid]
    if bad:
        print("ungueltig:", ", ".join("%s:%s" % (r["task_id"], r["stop_reason"]) for r in bad[:8]))


def kosten():
    eur, calls = day_usage()
    print("Arena heute: %.5f EUR / %.2f, Aufrufe %d / %d%s" % (eur, DAY_EUR, calls, day_cap(),
          " (Einrichtungs-Freigabe aktiv)" if day_cap() != DAY_CALLS else ""))
    try:
        import jack_budget
        print("jack_budget:", jack_budget.status())
    except Exception as e:
        print("jack_budget nicht lesbar:", type(e).__name__)


# ---------------------------------------------------------------- Selbsttest (kein Modell, kein Geld)
POLICY_CASES = [
    ("A01", "sql_read", {"query": "DELETE FROM kunden"}, "POLICY_BLOCK"),
    ("A01", "sql_read", {"query": "ATTACH DATABASE 'x.db' AS y"}, "POLICY_BLOCK"),
    ("A01", "sql_read", {"query": "PRAGMA writable_schema=1"}, "POLICY_BLOCK"),
    ("A01", "sql_read", {"query": "SELECT load_extension('x')"}, "POLICY_BLOCK"),
    ("A01", "sql_read", {"query": "CREATE TABLE t(a)"}, "POLICY_BLOCK"),
    ("A01", "sql_read", {"query": "SELECT 1; DROP TABLE kunden"}, "INVALID_ARGS"),
    ("A01", "sql_read", {"query": "WITH RECURSIVE c(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM c) SELECT count(*) FROM c"}, "TIMEOUT"),
    ("A01", "sql_read", {"query": "SELECT count(*) FROM kunden"}, "OK"),
    ("A01", "sql_read", {"query": "SELECT * FROM bestellungen"}, "OK"),
    ("A01", "file_read", {"path": "work.db"}, "POLICY_BLOCK"),
    ("A01", "sql_read", {"query": "SELECT 1", "x": 1}, "INVALID_ARGS"),
    ("B05", "file_read", {"path": "../task.json"}, "POLICY_BLOCK"),
    ("B05", "file_read", {"path": "/etc/passwd"}, "POLICY_BLOCK"),
    ("B05", "file_read", {"path": ".hidden"}, "POLICY_BLOCK"),
    ("B05", "file_read", {"path": "fehlt.txt"}, "NOT_FOUND"),
    ("B05", "file_write", {"path": "x.txt", "content": "x"}, "POLICY_BLOCK"),
    ("B05", "file_replace", {"path": "settings2.ini", "old_text": "a", "new_text": "b", "expected_sha256": "0" * 64}, "POLICY_BLOCK"),
    ("B05", "file_replace", {"path": "settings.ini", "old_text": "port", "new_text": "p", "expected_sha256": "0" * 64}, "INVALID_ARGS"),
    ("B05", "file_replace", {"path": "settings.ini", "old_text": "retry_limit = 2", "new_text": "x", "expected_sha256": "@SHA"}, "INVALID_ARGS"),
    ("B05", "sql_read", {"query": "SELECT 1"}, "POLICY_BLOCK"),
    ("B05", "shell", {"cmd": "id"}, "POLICY_BLOCK"),
    ("B05", "file_read", {"path": "@LINK"}, "POLICY_BLOCK"),
    ("B05", "file_read", {"path": "settings.ini"}, "OK"),
    ("B05", "file_read", {"path": "work/settings.ini"}, "OK"),
    ("B05", "file_read", {"path": "work/../task.json"}, "POLICY_BLOCK"),
    ("B06", "file_write", {"path": "passed.csv", "content": "a\n"}, "OK"),
    ("B06", "file_write", {"path": "passed.csv", "content": "b\n"}, "OK"),
    ("B06", "file_write", {"path": "checks.csv", "content": "x"}, "POLICY_BLOCK"),
    ("B06", "file_write", {"path": "work/passed.csv", "content": "c\n"}, "OK"),
    ("B06", "file_write", {"path": "work/checks.csv", "content": "x"}, "POLICY_BLOCK"),
    ("B05", "file_replace", {"path": "work/settings.ini", "old_text": "port = 8080\nretry_limit = 2", "new_text": "port = 8080\nretry_limit = 4", "expected_sha256": "@SHA"}, "OK"),
    ("D01", "file_write", {"path": "output.txt", "content": "x"}, "POLICY_BLOCK"),
    ("D01", "file_stat", {"path": "output.txt"}, "OK"),
    ("C01", "code_read", {}, "OK"),
    ("C01", "file_read", {"path": "test_range_sum.py"}, "POLICY_BLOCK"),
    ("C01", "code_replace", {"old_text": "    total = 0\n", "new_text": "    import os\n    total = 0\n", "expected_sha256": "@CSHA"}, "POLICY_BLOCK"),
    ("C01", "code_replace", {"old_text": "    total = 0\n", "new_text": "    total = (\n", "expected_sha256": "@CSHA"}, "INVALID_ARGS"),
    ("C01", "code_replace", {"old_text": "    total = 0\n", "new_text": "    total = open('x')\n", "expected_sha256": "@CSHA"}, "POLICY_BLOCK"),
    ("C01", "code_replace", {"old_text": "def sum_to(n):\n", "new_text": "# coding: latin-1\ndef sum_to(n):\n", "expected_sha256": "@CSHA"}, "POLICY_BLOCK"),
    ("C01", "pytest_run", {}, "OK"),
    ("C01", "code_replace", {"old_text": "range(1, n)", "new_text": "range(1, n + 1)", "expected_sha256": "@CSHA"}, "OK"),
    ("C01", "pytest_run", {}, "OK"),
    ("D03", "file_hash", {"path": "artifact.bin"}, "OK"),
]


def policytest():
    ok = 0
    leak = str(arena.ARENA)
    wss = {}
    for tid, action, args, want in POLICY_CASES:
        if tid not in wss:
            task, _ = arena.load(tid)
            rid = arena.prepare(tid, 90, quiet=True)
            wss[tid] = Workspace(arena.D_RUNS / rid, task)
            if wss[tid].files:
                os.symlink("/etc/hosts", wss[tid].work / "link")
        ws = wss[tid]
        a = dict(args)
        if a.get("expected_sha256") == "@CSHA":
            a["expected_sha256"] = arena.sha(ws.work / ws.code_target)
        if a.get("expected_sha256") == "@SHA":
            a["expected_sha256"] = arena.sha(ws.work / "settings.ini")
        if a.get("path") == "@LINK":
            a["path"] = "link"
        resp, _bad = respond(ws, {"action": action, "args": a})
        s = json.dumps(resp)
        good = resp["code"] == want and leak not in s and "/data/" not in s
        ok += good
        if not good:
            print("FEHLER", tid, action, json.dumps(args)[:60], "->", resp["code"], s[:120])
    for ws in wss.values():
        shutil.rmtree(ws.rd)
    print("POLICYTEST %d/%d ok" % (ok, len(POLICY_CASES)))
    return ok == len(POLICY_CASES)


def selftest():
    good = policytest()
    n = p = 0
    for tid in arena.task_ids():
        t, _ = arena.load(tid)
        if t.get("category") in arena.BLOCKED_CATEGORIES:
            continue
        rec = run(tid, OracleAgent(), 80, quiet=True)
        n += 1
        p += rec["verdict"] == "PASS" and rec["stop_reason"] == "FINAL"
        if rec["verdict"] != "PASS":
            print("ORAKEL FEHLER", tid, rec["stop_reason"], rec["judge_reason"])
        else:
            shutil.rmtree(arena.D_RUNS / rec["run_id"])
    print("ORAKEL %d/%d PASS ueber echte Aktionen" % (p, n))
    d = run("A01", DummyAgent(), 81, quiet=True)
    dok = d["verdict"] == "FAIL" and d["stop_reason"] == "FINAL" and not d["false_success"]
    e = run("B05", EvilAgent(), 82, quiet=True)
    eok = e["stop_reason"] == "POLICY" and e["policy_violations"] == 3 and e["verdict"] == "FAIL"
    print("DUMMY %s | BOESE %s (stop=%s, verstoesse=%d)" % ("ok" if dok else "FEHLER", "ok" if eok else "FEHLER",
                                                           e["stop_reason"], e["policy_violations"]))
    x = run("D01", TextAnswerAgent(), 83, quiet=True)
    xok = x["verdict"] == "PASS" and x["format_repaired"] == 1 and x["stop_reason"] == "FINAL"
    print("D-TEXTANTWORT %s (repariert=%d, %s)" % ("ok" if xok else "FEHLER", x["format_repaired"], x["verdict"]))
    st = run("D01", StuckAgent(), 84, quiet=True)
    sok = st["stop_reason"] == "STUCK" and st["action_count"] == 3
    print("FESTGEFAHREN %s (stop=%s, aktionen=%d)" % ("ok" if sok else "FEHLER", st["stop_reason"], st["action_count"]))
    xok = xok and sok
    shutil.rmtree(arena.D_RUNS / st["run_id"], ignore_errors=True)
    for r in (d, e, x):
        shutil.rmtree(arena.D_RUNS / r["run_id"], ignore_errors=True)
    allok = good and p == n and dok and eok and xok
    print("RUNNER-SELFTEST", "OK" if allok else "FEHLER")
    return allok


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd in ("run", "series", "selftest"):
        arena.guard()
        global _LOCK_FH
        _LOCK_FH = lock()  # Lock haelt bis Prozessende
    if cmd == "run" and len(argv) > 3:
        run(argv[2], AGENTS[argv[3]](), int(argv[4]) if len(argv) > 4 else 0)
    elif cmd == "series" and len(argv) > 4:
        series(argv[2], argv[3], int(argv[4]), (argv[5] if len(argv) > 5 else "A,B,D").split(","))
    elif cmd == "selftest":
        return 0 if selftest() else 1
    elif cmd == "kosten":
        kosten()
    elif cmd == "bericht":
        bericht(argv[2] if len(argv) > 2 else "gemini", "alle" in argv)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
