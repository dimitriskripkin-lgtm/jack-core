#!/usr/bin/env python3
"""JACK Nacht-Waechter: regelbasierte Selbstueberwachung.
NUR: Zustand lesen, tote JACK-Dienste neustarten, Dima per Telegram melden.
NIE: LLM-Entscheidungen, loeschen, bauen. Erster Lauf = nur Baseline, keine Meldung."""
import os, json, subprocess, time, urllib.request, datetime, sqlite3
H=os.path.expanduser("~/jack")
STATE=os.path.join(H,".waechter_state")
EDB=os.path.join(H,"jack_errors.db")
SEC=os.path.expanduser("~/.jack_secrets")
DIENSTE=["jack_cortex","jack_telegram","ollama","jack_waechter"]
HEARTBEAT=300

def _sec(k):
    try:
        for l in open(SEC):
            if k in l and "=" in l:
                return l.split('"')[1] if '"' in l else l.split("=",1)[1].strip()
    except Exception:
        pass
    return None

def notify(t):
    tok=_sec("TELEGRAM_BOT_TOKEN"); cid=_sec("TELEGRAM_CHAT_ID")
    if not tok or not cid: return
    try:
        d=json.dumps({"chat_id":cid,"text":"[JACK Waechter] "+t}).encode()
        r=urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",data=d,headers={"Content-Type":"application/json"})
        urllib.request.urlopen(r,timeout=10)
    except Exception as e:
        try: import jack_log; jack_log.log_decision('NOTIFY-FEHLER', str(e)[:100])
        except: pass

def _up(n):
    try: return subprocess.run(["sv","status",n],capture_output=True,text=True,timeout=8).stdout.strip().startswith("run:")
    except Exception: return False

def _xi():
    try:
        import jack_config as _jc
        ip = _jc.get_param('NETWORK','xiaomi_ip')
        return subprocess.run(["ssh","-i",os.path.expanduser("~/.ssh/id_jack"),"-o","BatchMode=yes",
          "-o","StrictHostKeyChecking=no","-o","ConnectTimeout=6","-p","8022",f"root@{ip}","true"],
          capture_output=True,timeout=12).returncode==0
    except Exception: return False

def _err():
    try:
        c=sqlite3.connect(EDB); n=c.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]; c.close(); return n
    except Exception: return 0

def _state():
    try: return json.load(open(STATE))
    except Exception: return {}

def cycle(dry=False):
    import jack_log
    first=not os.path.exists(STATE)
    alt=_state(); dienste={d:_up(d) for d in DIENSTE}; xi=_xi(); err=_err(); akt=[]
    if not first:
        for d,u in dienste.items():
            if not u and alt.get("dienste",{}).get(d,True):
                akt.append(f"Dienst {d} tot -> Neustart")
                if not dry:
                    subprocess.run(["sv","up",d],capture_output=True,timeout=10)
                    jack_log.log_decision("WAECHTER-NEUSTART",d); notify(f"Dienst {d} war tot, hab ihn neugestartet.")
        if not xi and alt.get("xiaomi",True):
            akt.append("Xiaomi weg")
            if not dry: jack_log.log_decision("WAECHTER-MELDUNG","Xiaomi weg"); notify("Xiaomi ist nicht mehr erreichbar.")
        if err>alt.get("errors",0)+3:
            akt.append(f"Fehler auf {err}")
            if not dry: jack_log.log_decision("WAECHTER-MELDUNG",f"Fehler {err}"); notify(f"Offene Fehler auf {err} gestiegen. /errors zeigt sie.")
    if not dry:
        json.dump({"dienste":dienste,"xiaomi":xi,"errors":err},open(STATE,"w"))
    return {"erster_lauf":first,"dienste":dienste,"xiaomi":xi,"errors":err,"wuerde_tun":akt}

def _maybe_audit():
    try:
        import jack_audit, time as _t
        lf = os.path.expanduser("~/jack/.last_audit")
        try: last = float(open(lf).read().strip())
        except Exception: last = 0.0
        if _t.time() - last >= 604800:
            notify("Woechentlicher Audit:" + chr(10) + jack_audit.report())
            open(lf,"w").write(str(_t.time()))
            import jack_log; jack_log.log_decision("WAECHTER-AUDIT","woechentlich verschickt")
    except Exception as e:
        try:
            import jack_log; jack_log.log_decision("WAECHTER-AUDIT-FEHLER", str(e)[:100])
        except Exception: pass


def _maybe_self_improve():
    try:
        import time as _t, datetime as _dt
        _h = _dt.datetime.now().hour
        if 16 <= _h < 22:
            return
        lf = os.path.expanduser("~/jack/.last_self_improve")
        try: last = float(open(lf).read().strip())
        except Exception: last = 0.0
        if _t.time() - last >= 86400:
            import sys; sys.path.insert(0, os.path.expanduser("~/jack"))
            import jack_self_improve
            result = jack_self_improve.run()
            if result and "Keine" not in result:
                notify(result[:1000])
            open(lf,"w").write(str(_t.time()))
            import jack_log; jack_log.log_decision("SELF-IMPROVE","Tagescheck abgeschlossen")
    except Exception as e:
        try:
            import jack_log; jack_log.log_decision("SELF-IMPROVE-FEHLER", str(e)[:100])
        except Exception: pass

def main():
    import jack_log; jack_log.log_decision("WAECHTER-START","Nacht-Ueberwachung laeuft")
    while True:
        try: cycle()
        except Exception as e:
            try:
                import jack_log; jack_log.log_decision("WAECHTER-FEHLER",str(e)[:100])
            except Exception: pass
        _maybe_audit()
        _maybe_self_improve()
        time.sleep(HEARTBEAT)


import threading as _th, time as _tm

def _autolearn_loop():
    while True:
        try:
            import jack_learn; jack_learn.run_once()
        except Exception as e:
            try: import jack_log; jack_log.log_decision("AUTOLEARN-ERR",str(e)[:80])
            except: pass
        _tm.sleep(7200)

def _publisher_loop():
    while True:
        try:
            import jack_publish; jack_publish.push()
        except Exception as e:
            try: import jack_log; jack_log.log_decision("PUBLISHER-ERR",str(e)[:80])
            except: pass
        _tm.sleep(180)


def _missions_loop():
    while True:
        try:
            import jack_missions
            r = jack_missions.dispatch_once()
            if r and r.get("status") in ("fertig","blockiert","fehler","wartet_freigabe"):
                notify("Mission #" + str(r["id"]) + " [" + r["typ"] + "] " + r["status"] + ":" + chr(10) + str(r.get("text",""))[:600])
        except Exception as e:
            try:
                import jack_log; jack_log.log_decision("MISSIONS-ERR", str(e)[:80])
            except Exception: pass
        _tm.sleep(300)

def _scout_loop():
    """Laeuft einmal taeglich, erzeugt Fingerabdruck und loggt Aenderungen."""
    _tm.sleep(60)
    while True:
        try:
            import jack_scout as _js
            fp = _js.erstelle_fingerabdruck()
            import jack_log; jack_log.log_decision('SCOUT-LAUF', fp['hash'])
            try:
                import jack_skill_builder as _sb
                neue = _sb.run()
                if neue:
                    notify("Skill-Builder: " + str(len(neue)) + " neue Skills: " + ", ".join(neue))
            except Exception as _sbe:
                try: jack_log.log_decision("SKILL-BUILDER-ERR", str(_sbe)[:80])
                except: pass
        except Exception as e:
            try: import jack_log; jack_log.log_decision('SCOUT-ERR', str(e)[:80])
            except: pass
        _tm.sleep(86400)

def _monitor_loop():
    """Event-driven Monitor: prueft alle 5 Min auf kritische Zustandsaenderungen."""
    _tm.sleep(30)
    while True:
        try:
            import jack_monitor as _mon
            events = _mon.event_check()
            if events:
                import jack_log; jack_log.log_decision('MONITOR-EVENT', str(len(events)) + ' Events')
        except Exception as e:
            try: import jack_log; jack_log.log_decision('MONITOR-ERR', str(e)[:80])
            except: pass
        _tm.sleep(120)
def start_consolidated():
    _th.Thread(target=_autolearn_loop,daemon=True,name="autolearn").start()
    _th.Thread(target=_publisher_loop,daemon=True,name="publisher").start()
    _th.Thread(target=_missions_loop,daemon=True,name="missions").start()
    _th.Thread(target=_scout_loop,daemon=True,name="scout").start()
    _th.Thread(target=_monitor_loop,daemon=True,name="monitor").start()
    print("[Konsolidiert] Autolearn+Publisher+Missionen als Threads gestartet")

if __name__=="__main__":
    start_consolidated()
    import sys
    print(json.dumps(cycle(dry=True),indent=2,ensure_ascii=False) if (len(sys.argv)>1 and sys.argv[1]=="dry") else main())
