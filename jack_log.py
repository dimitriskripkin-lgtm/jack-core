#!/usr/bin/env python3
"""jack_log.py — Zentraler Logger für alle JACK-Module.

Usage:
    from jack_log import get_logger
    log = get_logger("jack_cortex")
    log.info("Gestartet")
    log.warn("Verbindung langsam")
    log.error("Kritischer Fehler")
    log.debug("Detail-Info")
"""
MODULE_VERSION = 1

import os, sys, time, threading
from enum import IntEnum

J = os.path.expanduser("~/jack")
MAIN_LOG = os.path.join(J, "jack_main.log")
MAX_LOG_BYTES = 5 * 1024 * 1024  # 5MB dann rotieren

_lock = threading.Lock()

class Level(IntEnum):
    DEBUG = 0
    INFO  = 1
    WARN  = 2
    ERROR = 3

LEVEL_LABELS = {
    Level.DEBUG: "DEBUG",
    Level.INFO:  "INFO ",
    Level.WARN:  "WARN ",
    Level.ERROR: "ERROR",
}

def _rotate_if_needed():
    try:
        if os.path.exists(MAIN_LOG) and os.path.getsize(MAIN_LOG) > MAX_LOG_BYTES:
            old = MAIN_LOG + ".1"
            if os.path.exists(old): os.remove(old)
            os.rename(MAIN_LOG, old)
    except Exception: pass

def _write(module, level, msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    label = LEVEL_LABELS.get(level, "?????")
    line = f"{ts} [{label}] [{module:<22}] {msg}\n"
    with _lock:
        _rotate_if_needed()
        try:
            with open(MAIN_LOG, "a") as f:
                f.write(line)
        except Exception: pass
    # ERROR immer auch auf stderr
    if level >= Level.ERROR:
        sys.stderr.write(line)

class JackLogger:
    """Logger-Instanz pro Modul."""
    def __init__(self, module: str, min_level: Level = Level.INFO):
        self.module = module[:22]
        self.min_level = min_level

    def debug(self, msg): self._log(Level.DEBUG, msg)
    def info(self,  msg): self._log(Level.INFO,  msg)
    def warn(self,  msg): self._log(Level.WARN,  msg)
    def error(self, msg): self._log(Level.ERROR, msg)

    def _log(self, level, msg):
        if level >= self.min_level:
            _write(self.module, level, str(msg))

    def exception(self, msg, exc):
        """Fehler mit Exception-Info loggen."""
        self._log(Level.ERROR, f"{msg} | {type(exc).__name__}: {exc}")

_loggers: dict = {}

def get_logger(module: str, min_level: Level = Level.INFO) -> JackLogger:
    """Gibt Logger-Instanz zurück. Pro Modul nur eine Instanz."""
    if module not in _loggers:
        _loggers[module] = JackLogger(module, min_level)
    return _loggers[module]

def tail(n=50) -> list:
    """Letzte n Zeilen aus jack_main.log."""
    try:
        lines = open(MAIN_LOG).readlines()
        return lines[-n:]
    except Exception: return []

if __name__ == "__main__":
    log = get_logger("jack_log_test")
    log.debug("Debug-Nachricht")
    log.info("System gestartet")
    log.warn("Warnung Test")
    log.error("Fehler Test")
    print("Letzten 4 Zeilen:")
    for l in tail(4): print(" ", l.rstrip())

def log_decision(key: str, value: str = "", extra: str = ""):
    """Kompatibilitäts-Shim — ersetzt alte jack_log.log_decision() Aufrufe."""
    msg = f"{key}: {value}"
    if extra: msg += f" | {extra}"
    _write("jack_autonomous", Level.INFO, msg)

def prune_old_logs(max_days: int = 7):
    """Löscht Logzeilen die älter als max_days sind."""
    import time
    cutoff = time.time() - (max_days * 86400)
    for logfile in [MAIN_LOG, MAIN_LOG + ".1"]:
        if not os.path.exists(logfile): continue
        try:
            lines = open(logfile).readlines()
            kept = []
            for l in lines:
                try:
                    ts_str = l[:19]
                    import datetime
                    ts = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S").timestamp()
                    if ts >= cutoff: kept.append(l)
                except Exception: kept.append(l)
            open(logfile, 'w').writelines(kept)
            removed = len(lines) - len(kept)
            if removed > 0:
                _write("jack_log", Level.INFO, f"Prune: {removed} Zeilen älter als {max_days}d entfernt aus {os.path.basename(logfile)}")
        except Exception: pass


# JACK_CORR_WRAP
try:
    import jack_corr as _jcorr
    _log_decision_raw = log_decision
    def log_decision(*a, **k):
        if a: a=(_jcorr.tag(str(a[0])),)+a[1:]
        return _log_decision_raw(*a, **k)
except Exception:
    pass

# ---------------------------------------------------------------
# Entscheidungs-Log — append-only JSONL, eine Zeile pro Entscheidung
# Zweck: Trainingsdaten fuer spaeteres lokales Routing.
# Regel: LLM-Begruendungen sind Behauptungen, keine Fakten.
# ---------------------------------------------------------------
DECISION_LOG = os.path.join(J, "reports", "decisions.jsonl")
SCHEMA_V = 1

def log_decision_event(msg, route_by, chosen, available=None,
                       tool=None, claim=None, ok=None, raw=None,
                       err=None, ms=None, reply_by=None,
                       correction_of=None, is_test=False):
    """Schreibt eine Entscheidung als JSONL-Zeile.

    msg           : Original-Nachricht wortwoertlich
    route_by      : "keyword" | "graph" | "llm" | "fallback"
    chosen        : "tool" | "graph" | "groq"
    available     : Liste der zur Wahl stehenden Werkzeuge
    tool          : gewaehltes Werkzeug oder None
    claim         : Begruendung des Modells — BEHAUPTUNG, kein Fakt
    ok            : True/False ob die Ausfuehrung geklappt hat
    raw           : Rohergebnis, ungekuerzt wenn kurz
    err           : Fehlertext falls vorhanden
    ms            : Dauer in Millisekunden
    reply_by      : "groq" | "template" | "graph"
    correction_of : id einer frueheren Zeile, wenn dies eine Korrektur ist
    is_test       : True bei Testnachrichten, damit filterbar
    """
    import json, uuid, time as _t
    try:
        os.makedirs(os.path.dirname(DECISION_LOG), exist_ok=True)
        row = {
            "v": SCHEMA_V,
            "id": uuid.uuid4().hex[:12],
            "ts": _t.strftime("%Y-%m-%dT%H:%M:%S"),
            "msg": str(msg)[:2000],
            "route": {
                "by": route_by,
                "chosen": chosen,
                "tool": tool,
                "available": available or [],
                "claim": claim,
                "claim_is_fact": False
            },
            "exec": {
                "ok": ok,
                "raw": str(raw)[:1000] if raw is not None else None,
                "err": str(err)[:300] if err else None,
                "ms": ms
            },
            "reply_by": reply_by,
            "correction_of": correction_of,
            "is_test": bool(is_test)
        }
        with _lock:
            with open(DECISION_LOG, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row["id"]
    except Exception:
        return None


def decisions_read(limit=200, skip_tests=True):
    """Liest die letzten Entscheidungen zurueck. Fuer Auswertung."""
    import json
    out = []
    try:
        for line in open(DECISION_LOG, encoding="utf-8"):
            try:
                r = json.loads(line)
                if skip_tests and r.get("is_test"):
                    continue
                out.append(r)
            except Exception:
                continue
    except Exception:
        return []
    return out[-limit:]


def decisions_stats():
    """Kurzauswertung: wie oft welcher Pfad, wie oft Fehler."""
    rows = decisions_read(limit=100000)
    if not rows:
        return {"n": 0}
    paths, tools, fails, corrections = {}, {}, 0, 0
    for r in rows:
        p = r.get("route", {}).get("chosen", "?")
        paths[p] = paths.get(p, 0) + 1
        t = r.get("route", {}).get("tool")
        if t:
            tools[t] = tools.get(t, 0) + 1
        if r.get("exec", {}).get("ok") is False:
            fails += 1
        if r.get("correction_of"):
            corrections += 1
    return {"n": len(rows), "pfade": paths, "werkzeuge": tools,
            "fehler": fails, "korrekturen": corrections}
