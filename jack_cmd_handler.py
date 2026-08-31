#!/usr/bin/env python3
"""jack_cmd_handler.py — einfache /Slash-Commands ohne Threading."""
import os, sys
sys.path.insert(0, "/data/data/com.termux/files/home/jack")

def handle(rt: str, text: str, send) -> str:
    if rt in ('/akku','/sensor'):
        try:
            import jack_sensors as _js
            return _js.get_battery()+' | '+_js.get_motion()
        except Exception as e: return 'Sensor-Fehler: '+str(e)[:80]
    if rt == '/log':
        try:
            import jack_log as _jl
            return 'JACKs Logbuch:'+chr(10)+_jl.recent(15)
        except Exception as e: return 'Log-Fehler: '+str(e)[:80]
    if rt == '/level':
        try:
            import jack_intent as _ji
            return f'Autonomie-Level: {_ji.get_level()}/4'
        except Exception as e: return 'Level-Fehler: '+str(e)[:80]
    if rt == '/errors':
        try:
            import sqlite3 as _sq
            con=_sq.connect(os.path.expanduser('~/jack/jack_errors.db'),timeout=5)
            rows=con.execute('SELECT module,error_msg,timestamp FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 5').fetchall()
            con.close()
            return ('Keine offenen Fehler.' if not rows else
                chr(10).join(f'[{r[2][:16]}] {r[0]}: {r[1][:60]}' for r in rows))
        except Exception as e: return 'Errors-Fehler: '+str(e)[:80]
    if rt == '/budget':
        try:
            import jack_budget as _jb; return _jb.status()
        except Exception as e: return 'Budget-Fehler: '+str(e)[:80]
    if rt == '/missionen':
        try:
            import glob
            p='/data/data/com.termux/files/home/jack/missions'
            pend=len(glob.glob(p+'/pending/*.json'))
            done=len(glob.glob(p+'/done/*.json'))
            fail=len(glob.glob(p+'/fail/*.json'))
            return f'Missions: {pend} pending | {done} done | {fail} fail'
        except Exception as e: return 'Missions-Fehler: '+str(e)[:80]
    return None
