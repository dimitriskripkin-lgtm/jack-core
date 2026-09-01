#!/usr/bin/env python3
MODULE_VERSION = 1
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

    if rt.startswith('/approve_') or rt.startswith('/reject_'):
        try:
            import json, os, shutil
            J = "/data/data/com.termux/files/home/jack"
            APPROVALS = os.path.join(J, "pending_approvals.json")
            if not os.path.exists(APPROVALS):
                return "Keine ausstehenden Freigaben."
            approvals = json.load(open(APPROVALS))
            mission_id = rt.split("_",1)[1]
            match = [a for a in approvals if a.get("id") == mission_id]
            if not match:
                return f"Kein Fix mit ID {mission_id} gefunden."
            approval = match[0]
            staged = approval.get("staged","")
            live = approval.get("file","")
            if rt.startswith('/approve_'):
                if not os.path.exists(staged):
                    return f"Staged-Datei fehlt: {staged}"
                shutil.copy2(staged, live)
                os.remove(staged)
                approval["status"] = "approved"
                approvals = [a for a in approvals if a.get("id") != mission_id]
                json.dump(approvals, open(APPROVALS,"w"), indent=2)
                # Mission done markieren
                DONE = os.path.join(J, "missions", "done", mission_id + ".json")
                FAIL_SRC = os.path.join(J, "missions", "fail", mission_id + ".json")
                PEND_SRC = os.path.join(J, "missions", "pending", mission_id + ".json")
                for src in [FAIL_SRC, PEND_SRC]:
                    if os.path.exists(src):
                        shutil.move(src, DONE)
                return f"✅ Fix angewendet: {os.path.basename(live)}"
            else:  # reject
                if os.path.exists(staged):
                    os.remove(staged)
                approval["status"] = "rejected"
                approvals = [a for a in approvals if a.get("id") != mission_id]
                json.dump(approvals, open(APPROVALS,"w"), indent=2)
                return f"❌ Fix abgelehnt: {os.path.basename(live)}"
        except Exception as e:
            return f"Approve-Fehler: {str(e)[:100]}"


    if cmd == "/approve_all":
        import json, os, shutil
        J=os.path.expanduser("~/jack")
        APPROVALS=os.path.join(J,"pending_approvals.json")
        try:
            entries=json.load(open(APPROVALS)) if os.path.exists(APPROVALS) else []
            if not entries:
                return "Keine Approvals pending."
            results=[]
            for entry in list(entries):
                eid=entry.get("id","?")
                src=os.path.join(J,"shadow",os.path.basename(entry.get("file",""))+".staged")
                dst=entry.get("file","").replace("~/jack",J)
                if os.path.exists(src):
                    import shutil as _sh
                    _sh.copy2(dst, dst+".fix.bak")
                    _sh.copy2(src, dst)
                    os.remove(src)
                    results.append(f"✅ {os.path.basename(dst)}")
                else:
                    results.append(f"⚠️ {eid} — staged fehlt")
            open(APPROVALS,'w').write('[]')
            # Health-Check
            try:
                import jack_health_monitor as _hm
                _hm.check_after_approve()
            except Exception: pass
            return f"✅ {len(entries)} Fixes angewendet:\n" + "\n".join(results[:20])
        except Exception as e:
            return f"Fehler approve_all: {e}"

    if cmd == "/reject_all":
        import json, os
        J=os.path.expanduser("~/jack")
        APPROVALS=os.path.join(J,"pending_approvals.json")
        try:
            entries=json.load(open(APPROVALS)) if os.path.exists(APPROVALS) else []
            n=len(entries)
            # Staged Files löschen
            for entry in entries:
                src=os.path.join(J,"shadow",os.path.basename(entry.get("file",""))+".staged")
                if os.path.exists(src): os.remove(src)
            open(APPROVALS,'w').write('[]')
            return f"❌ {n} Fixes abgelehnt."
        except Exception as e:
            return f"Fehler reject_all: {e}"

    return None
