#!/usr/bin/env python3
"""JACK Waechter-Daemon: Dienste-Heilung + Hintergrund-Loops.
Threads: Autolearn(2h), Publisher(3min), Missionen(5min), Scout(taeglich), Monitor(2min).
Self-Improve 1x taeglich ausserhalb 16-22 Uhr. Erster Lauf = Baseline ohne Meldung."""
import os, json, subprocess, time, urllib.request, sqlite3
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
H=os.path.expanduser("~/jack")
STATE=os.path.join(H,".waechter_state")
EDB=os.path.join(H,"jack_errors.db")
SEC=os.path.expanduser("~/.jack_secrets")
DIENSTE=["jack_cortex","jack_telegram","jack_waechter"]  # ollama entfernt (Qwen 21.08. - Hitze-Problem)
HEARTBEAT=120

def _sec(k):
    try:
        for l in open(SEC):
            if k in l and "=" in l:
                return l.split('"')[1] if '"' in l else l.split("=",1)[1].strip()
    except Exception as _le:
        _jlog and _jlog.fehler("autonomous","unbenannt",_le)
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
        except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)

def _up(n):
    try: return subprocess.run(["sv","status",n],capture_output=True,text=True,timeout=8).stdout.strip().startswith("run:")
    except Exception: return False

def _xi():
    try:
        import jack_config as _jc
        ip = _jc.get_param('NETWORK','xiaomi_ip')
        # FIX (Qwen 22.08.): Nutze SSH-Config Alias statt manueller Optionen
        return subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=8","xiaomi-jack","true"],
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

def _maybe_self_audit():
    try:
        import jack_scheduler as _js, jack_self_audit as _jsa
        ok,_=_js.can_run_heavy()
        if ok:
            _jsa.run()
    except Exception as e:
        try: import jack_log; jack_log.log_decision("SELF-AUDIT-FEHLER",str(e)[:80])
        except Exception: pass

def _maybe_ingest_schedule():
    """Placeholder: schwere Ingest-Jobs nur in Power-Time."""
    try:
        import jack_scheduler as _js
        if not _js.is_power_time(): return
        import jack_log; jack_log.log_decision("SCHEDULER","Power-Time aktiv - schwere Jobs erlaubt")
    except Exception: pass

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


def _heartbeat_sv_check():
    """HEARTBEAT_SV_CHECK: tote Dienste per is_alive -> sv restart."""
    try:
        import jack_heartbeat
        import subprocess
        dienste = [
            ("jack_telegram", 180),
            ("jack_cortex", 300),
            ("jack_publisher", 400),
            ("jack_autolearn", 900),
        ]
        for name, max_age in dienste:
            try:
                if not jack_heartbeat.is_alive(name, max_age=max_age):
                    age = jack_heartbeat.age(name)
                    subprocess.run(
                        ["sv", "restart", name],
                        capture_output=True, timeout=30,
                    )
                    try:
                        import jack_log
                        jack_log.log_decision("HB_RESTART", name, "age=%s" % age)
                    except Exception:
                        pass
            except Exception:
                pass
    except Exception:
        pass



def _adb_heal_if_needed():
    """ADB_HEAL_HOOK: wenn SSH ok und adb nicht device -> jack_adb_heal.py"""
    try:
        import subprocess, os
        r = subprocess.run(
            ["adb", "devices"], capture_output=True, text=True, timeout=8
        )
        text = (r.stdout or "") + (r.stderr or "")
        ok = any(
            "10.229.239.131" in ln and ln.split()[1] == "device"
            for ln in text.splitlines()
            if "10.229.239.131" in ln and len(ln.split()) >= 2
        )
        if ok:
            return
        heal = "/data/data/com.termux/files/home/jack/jack_adb_heal.py"
        if not os.path.isfile(heal):
            return
        subprocess.run(["python3", heal], capture_output=True, text=True, timeout=60)
    except Exception:
        pass


def main():
    import jack_log; jack_log.log_decision("WAECHTER-START", "Nacht-Ueberwachung mit Queue")
    import jack_queue
    q = jack_queue.TaskQueue(min_ram_mb=800)
    while True:
        q.add_task(1, "cycle", cycle)
        q.add_task(2, "audit", _maybe_audit)
        q.add_task(2, "self_improve", _maybe_self_improve)
        q.add_task(2, "self_audit", _maybe_self_audit)
        q.add_task(2, "ingest_schedule", _maybe_ingest_schedule)

        def _run_db_opt():
            import jack_db_optimizer as _dbo
            _dbo.enforce_pragmas()
            _dbo.optimize_wal()

        q.add_task(2, "db_optimizer", _run_db_opt)
        
        def _run_explore():
            import jack_xiaomi as _jx
            _xr = _jx.explore_next()
            import jack_log
            jack_log.log_decision('EXPLORE', f"Xiaomi: CPU={_xr.get('cpu_user','?')} RAM={_xr.get('ram','?')} Akku={_xr.get('battery','?')} Temp={_xr.get('temp_c','?')}C")
        
        def _run_autofixer():
            # HEAT-PROTECT (Qwen 21.08.): Shadow-Fixer nur bei < 55°C
            try:
                import jack_heat_protection
                if not jack_heat_protection.check_heat("shadow"):
                    print("Shadow-Fixer übersprungen (Hitze)")
                    return
            except Exception as e:
                print(f"Heat-Check-Fehler: {e}")
            import jack_autofixer_shadow as _afs
            # Phase 3+P4 (Qwen 22.08.): worker_target() entscheidet wo Shadow-Fixer laeuft
            import subprocess, jack_heat_protection as _hp
            
            # NIGHT-FIX (Qwen 23.08.): Xiaomi-Online-Check VOR SSH-Call
            # Wenn Xiaomi offline → skippen, kein Error, kein Fallback
            try:
                _r = subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=8","xiaomi-jack","true"], capture_output=True, timeout=12)
                if _r.returncode != 0:
                    print("Shadow-Fixer übersprungen (Xiaomi offline)")
                    return
            except Exception:
                print("Shadow-Fixer übersprungen (Xiaomi nicht erreichbar)")
                return
            
            if _hp.worker_target() == "xiaomi":
                try:
                    result = subprocess.run(
                        ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=8","xiaomi-jack", "cd ~/jack && python3 jack_autofixer_shadow.py"],
                        capture_output=True, text=True, timeout=120
                    )
                    if result.returncode == 0:
                        print(f"Shadow-Fixer auf Xiaomi: {result.stdout[:100]}")
                    else:
                        print(f"Shadow-Fixer auf Xiaomi FEHLER: {result.stderr[:100]}")
                except Exception as e:
                    print(f"SSH-Aufruf Shadow-Fixer fehlgeschlagen: {e}")
                    _afs.run(limit=3)
            else:
                print("P4: Honor kuehl - Shadow-Fixer laeuft lokal (LLM-Inferenz trotzdem via Tunnel auf Xiaomi)")
                _afs.run(limit=3)
            import jack_autofixer_shadow as _afs
            _afs.run(limit=3)

        q.add_task(3, "explore_next", _run_explore)
        q.add_task(3, "autofixer_shadow", _run_autofixer)
        
        results = q.execute()
        for name, res in results.items():
            if res.get("status") == "skipped":
                import jack_log
                jack_log.log_decision("QUEUE-SKIPPED", res.get("reason", name))
        
        import jack_heartbeat; jack_heartbeat.beat("jack_waechter")
        _adb_heal_if_needed()
        _heartbeat_sv_check()
        import jack_heartbeat; jack_heartbeat.beat('jack_waechter')
        try:
            import jack_graceful
            jack_graceful.main()
        except Exception:
            pass
        time.sleep(HEARTBEAT)



import threading as _th, time as _tm

def _autolearn_loop():
    while True:
        try:
            import jack_learn; jack_learn.run_once()
        except Exception as e:
            try: import jack_log; jack_log.log_decision("AUTOLEARN-ERR",str(e)[:80])
            except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        _tm.sleep(7200)

def _publisher_loop():
    while True:
        try:
            import jack_publish; jack_publish.push()
        except Exception as e:
            try: import jack_log; jack_log.log_decision("PUBLISHER-ERR",str(e)[:80])
            except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        _tm.sleep(180)


def _missions_loop():
    """Arbeitet die Queue leer statt nach jeder Mission 5 Minuten zu pennen.
    Nur bei leerer Queue lange schlafen. Vorher: 5 Missionen = 25 Minuten."""
    _leerlauf = 300
    _aktiv = 2
    _max_runde = 20
    while True:
        gearbeitet = 0
        try:
            import jack_missions
            jack_missions.recover_stale()
            while gearbeitet < _max_runde:
                r = jack_missions.dispatch_once()
                if not r:
                    break
                gearbeitet += 1
                if r.get("status") in ("fertig","blockiert","fehler","wartet_freigabe"):
                    notify("Mission #" + str(r["id"]) + " [" + r["typ"] + "] " +
                           r["status"] + ":" + chr(10) + str(r.get("text",""))[:600])
                if r.get("status") == "verschoben":
                    break
                _tm.sleep(_aktiv)
            if gearbeitet >= _max_runde:
                try:
                    import jack_log
                    jack_log.log_decision("MISSIONS-DROSSEL",
                        "Rundenlimit " + str(_max_runde) + " erreicht, Pause")
                except Exception: pass
        except Exception as e:
            try:
                import jack_log; jack_log.log_decision("MISSIONS-ERR", str(e)[:80])
            except Exception: pass
        _tm.sleep(_leerlauf if gearbeitet == 0 else 10)

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
                except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        except Exception as e:
            try: import jack_log; jack_log.log_decision('SCOUT-ERR', str(e)[:80])
            except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
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
            except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        _tm.sleep(120)

def _reflexion_loop():
    """Laeuft nachts, reflektiert JACK-Aktionen und lernt daraus."""
    import time as _t
    _tm.sleep(3600)  # Erst nach 1h starten
    while True:
        try:
            stunde = __import__("datetime").datetime.now().hour
            if 2 <= stunde <= 6:  # Nur nachts
                import jack_reflexion as _jr
                ergebnis = _jr.nacht_loop()
                if ergebnis["reflektiert"] > 0:
                    import jack_log; jack_log.log_decision("REFLEXION",
                        str(ergebnis["reflektiert"]) + " reflektiert, " +
                        str(ergebnis["ins_gedaechtnis"]) + " ins Gedaechtnis")
        except Exception as _e:
            try: import jack_log; jack_log.log_decision("REFLEXION-ERR", str(_e)[:80])
            except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        _tm.sleep(3600)

def _sanity_loop():
    """Prueft Config-Falle und Git-Stand alle 6h."""
    import time as _t2
    _t2.sleep(120)
    while True:
        try:
            import jack_sanity as _js
            _js.check()
        except Exception as _e:
            try: import jack_log; jack_log.log_decision("SANITY-ERR", str(_e)[:80])
            except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        _t2.sleep(21600)


def _proaktiv_loop():
    """Meldet sich proaktiv bei interessanten Ereignissen."""
    import time as _t2, datetime as _dt2
    _t2.sleep(300)  # 5min nach Start warten
    _last_moin = 0
    while True:
        try:
            _h = _dt2.datetime.now().hour
            # Moin nach Nachtschicht (6-9 Uhr, max einmal pro Tag)
            if 6 <= _h <= 9 and _t2.time() - _last_moin > 86400:
                try:
                    import jack_chains as _jc3
                    _r = _jc3.run('morgen_briefing')
                    notify("Moin Dima." + chr(10) + chr(10) + _r['text'])
                except Exception:
                    notify("Moin Dima. Nachtschicht rum?")
                _last_moin = _t2.time()
            # Akku-Warnung
            try:
                import subprocess as _sp2, json as _j2
                r = _sp2.run(['termux-battery-status'], capture_output=True, text=True, timeout=8)
                d = _j2.loads(r.stdout)
                pct = d.get('percentage', 100)
                if pct < 20 and d.get('status') != 'CHARGING':
                    notify(f"Akku bei {pct}%. Laden oder Ollama pausieren?")
            except Exception as _le:
                _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        except Exception as _e:
            try: import jack_log; jack_log.log_decision("PROAKTIV-ERR", str(_e)[:80])
            except Exception as _le: _jlog and _jlog.fehler("autonomous","unbenannt",_le)
        _t2.sleep(1800)  # alle 30min

def _lerner_stop():
    """Not-Aus per Datei. Anlegen stoppt, loeschen erlaubt wieder."""
    return os.path.exists(os.path.expanduser("~/.jack_lerner_stop"))

def _lerner_loop():
    if _lerner_stop():
        try:
            import jack_log
            jack_log.log_decision("LERNER", "gestoppt per ~/.jack_lerner_stop")
        except Exception: pass
        return
    """Autonomer Lerner: 1 Runde pro Stunde, nur 16-22 Uhr, mit Hardware-Drosselung."""
    import time as _tm
    _tm.sleep(300)  # 5 Min nach Start warten
    while True:
        try:
            import datetime as _dt
            h = _dt.datetime.now().hour
            # Zeitfenster: nur 16-22 Uhr (Dimas Schlafzeit)
            if not (16 <= h < 22):
                _tm.sleep(3600)
                continue
            # Hardware-Drosselung: Akku
            import subprocess as _sp, json as _j
            try:
                _b = _j.loads(_sp.run(['termux-battery-status'], capture_output=True, text=True, timeout=8).stdout)
                if _b.get('percentage', 100) < 30:
                    import jack_log; jack_log.log_decision('LERNER-SKIP', 'Akku unter 30%')
                    _tm.sleep(3600)
                    continue
                if float(_b.get('temperature', 0)) > 45:
                    import jack_log; jack_log.log_decision('LERNER-SKIP', 'Temp ueber 45C')
                    _tm.sleep(3600)
                    continue
            except Exception:
                pass
            # Hardware-Drosselung: RAM
            try:
                for _l in open('/proc/meminfo'):
                    if 'MemAvailable' in _l:
                        if int(_l.split()[1]) // 1024 < 800:
                            import jack_log; jack_log.log_decision('LERNER-SKIP', 'RAM unter 800MB')
                            _tm.sleep(3600)
                            break
                else:
                    # RAM OK, Lernrunde starten
                    import jack_lerner
                    ergebnis = jack_lerner.runde()
                    if ergebnis:
                        import jack_log
                        jack_log.log_decision('LERNER-RUNDE', str(ergebnis)[:80])
            except Exception:
                pass
        except Exception as e:
            try:
                import jack_log; jack_log.log_decision('LERNER-ERR', str(e)[:80])
            except Exception:
                pass
        _tm.sleep(3600)  # 1 Stunde Pause

def start_consolidated():
    _th.Thread(target=_autolearn_loop,daemon=True,name="autolearn").start()
    _th.Thread(target=_publisher_loop,daemon=True,name="publisher").start()
    _th.Thread(target=_missions_loop,daemon=True,name="missions").start()
    _th.Thread(target=_scout_loop,daemon=True,name="scout").start()
    _th.Thread(target=_monitor_loop,daemon=True,name="monitor").start()
    _th.Thread(target=_sanity_loop,daemon=True,name="sanity").start()
    _th.Thread(target=_lerner_loop,daemon=True,name="lerner").start()

    _th.Thread(target=_proaktiv_loop,daemon=True,name="proaktiv").start()
    print("[Konsolidiert] Autolearn+Publisher+Missionen als Threads gestartet")

if __name__=="__main__":
    start_consolidated()
    import sys
    print(json.dumps(cycle(dry=True),indent=2,ensure_ascii=False) if (len(sys.argv)>1 and sys.argv[1]=="dry") else main())

# JACK_TUNE_R01
