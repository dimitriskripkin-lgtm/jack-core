#!/usr/bin/env python3
"""JACK Nacht-Waechter: regelbasierte Selbstueberwachung.
NUR: Zustand lesen, tote JACK-Dienste neustarten, Dima per Telegram melden.
NIE: LLM-Entscheidungen, loeschen, bauen. Erster Lauf = nur Baseline, keine Meldung."""
import os, json, subprocess, time, urllib.request, datetime, sqlite3
H=os.path.expanduser("~/jack")
STATE=os.path.join(H,".waechter_state")
EDB=os.path.join(H,"jack_errors.db")
SEC=os.path.expanduser("~/.jack_secrets")
DIENSTE=["jack_cortex","jack_telegram","jack_autolearn","ollama","jack_publisher"]
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
    except Exception: pass

def _up(n):
    try: return subprocess.run(["sv","status",n],capture_output=True,text=True,timeout=8).stdout.strip().startswith("run:")
    except Exception: return False

def _xi():
    try:
        return subprocess.run(["ssh","-i",os.path.expanduser("~/.ssh/id_jack"),"-o","BatchMode=yes",
          "-o","StrictHostKeyChecking=no","-o","ConnectTimeout=6","-p","8022","root@10.234.166.131","true"],
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

def main():
    import jack_log; jack_log.log_decision("WAECHTER-START","Nacht-Ueberwachung laeuft")
    while True:
        try: cycle()
        except Exception as e:
            try:
                import jack_log; jack_log.log_decision("WAECHTER-FEHLER",str(e)[:100])
            except Exception: pass
        _maybe_audit()
        time.sleep(HEARTBEAT)

if __name__=="__main__":
    import sys
    print(json.dumps(cycle(dry=True),indent=2,ensure_ascii=False) if (len(sys.argv)>1 and sys.argv[1]=="dry") else main())
