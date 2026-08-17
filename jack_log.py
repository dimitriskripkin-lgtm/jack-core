#!/usr/bin/env python3
import os, datetime
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
LOG=os.path.expanduser("~/jack/jack_decisions.log")
def log_decision(aktion, detail="", ergebnis=""):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    zeile=f"[{ts}] {aktion} | {detail} | {ergebnis}".rstrip(" |")
    try:
        with open(LOG,"a") as f: f.write(zeile+chr(10))
    except Exception as e:
        import sys; print(f"[jack_log FEHLER] {e}", file=sys.stderr)
def recent(n=15):
    try:
        with open(LOG,"rb") as f:
            f.seek(0,2); size=f.tell()
            f.seek(-min(size,n*200),2)
            lines=f.read().decode("utf-8",errors="replace").strip().split(chr(10))
            return chr(10).join(lines[-n:]) if lines and lines[0] else "(Logbuch leer)"
    except Exception:
        return "(Logbuch leer)"

_log_decision_orig = log_decision
def log_decision(tag, text=''):
    _log_decision_orig(tag, text)
    try:
        t = str(tag).upper()
        if any(k in t for k in ('ERR', 'FEHLER', 'FAIL')):
            import sqlite3 as _sq, os as _os
            _db = _os.path.expanduser('~/jack/jack_errors.db')
            with _sq.connect(_db, timeout=5) as _con:
                _con.execute("INSERT INTO errors (module,error_type,error_msg,file_path,line_num,context,resolved,timestamp) VALUES (?,?,?,?,?,?,0,datetime('now'))", (str(tag)[:40], 'LOGGED_ERR', str(text)[:300], '', 0, 'via jack_log Spiegel'))
    except Exception:
        pass
