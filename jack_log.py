#!/usr/bin/env python3
"""JACK Entscheidungs-Logbuch: was hat JACK wann getan. Nachvollziehbarkeit."""
import os, datetime
LOG=os.path.expanduser("~/jack/jack_decisions.log")

def log_decision(aktion, detail="", ergebnis=""):
    ts=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    zeile=f"[{ts}] {aktion} | {detail} | {ergebnis}".rstrip(" |")
    try:
        with open(LOG,"a") as f: f.write(zeile+"\n")
    except Exception as e:
        import sys; print(f'[jack_log FEHLER] {e}', file=sys.stderr)

def recent(n=15):
    try:
        lines=open(LOG).read().strip().split("\n")
        return "\n".join(lines[-n:]) if lines and lines[0] else "(Logbuch leer)"
    except Exception:
        return "(Logbuch leer)"
