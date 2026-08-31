# JACK_TUNE_CBH
MODULE_VERSION = 1
def handle(callback_data, callback_id):
    import jack_telegram as tg
    """Verarbeitet Inline-Button-Klicks."""
    if callback_data == 'run_exec':
        c=tg.PENDING_EXEC.get('cmd')
        if not c:
            tg.answer_callback(callback_id,'Nichts offen'); return
        tg.answer_callback(callback_id,'Laeuft...')
        tg.send('Fuehre aus...')
        def _r(cmd=c):
            out=jack_exec.run(cmd)
            tg.PENDING_EXEC.clear()
            tg.send(out)
            if not out.startswith('rc=0') and not out.startswith('BLOCKIERT'):
                try:
                    import jack_react
                    tg.send('Analysiere Fehler...')
                    tg.send('VORSCHLAG:' + chr(10) + str(jack_react.analysiere(cmd, out))[:1500])
                except Exception as _e:
                    tg.send('Analyse-Fehler: ' + str(_e)[:120])
        import threading as _th
        _th.Thread(target=_r, daemon=True).start()
        return
    if callback_data == 'cancel_exec':
        tg.PENDING_EXEC.clear()
        tg.answer_callback(callback_id,'Abgebrochen')
        tg.send('Befehl verworfen.')
        return
    if callback_data.startswith("confirm_write:"):
        fn=callback_data[14:]
        if tg.PENDING_WRITE and tg.PENDING_WRITE.get("filename")==fn:
            try:
                ok,msg=jack_write.commit_write(tg.PENDING_WRITE["filename"],tg.PENDING_WRITE["content"])
                tg.PENDING_WRITE.clear()
                tg.answer_callback(callback_id,"Gespeichert" if ok else "Fehler")
                tg.send("✅ "+msg if ok else "❌ "+msg)
            except Exception as e:
                tg.answer_callback(callback_id,"Fehler")
                tg.send("Fehler beim Schreiben: "+str(e)[:100])
        else:
            tg.answer_callback(callback_id,"Kein Vorschlag offen")
        return
    if callback_data.startswith("cancel_write:"):
        tg.PENDING_WRITE.clear()
        tg.answer_callback(callback_id,"Abgebrochen")
        tg.send("❌ Abgebrochen.")
        return
    if callback_data.startswith("mem_save:"):
        fact=callback_data[9:]
        try:
            import jack_memory as _jm; _jm.save(fact,"Dima erwaehnte",intent="dima_fact")
            tg.answer_callback(callback_id,"Gespeichert")
        except Exception as e:
            tg.answer_callback(callback_id,"Fehler: "+str(e)[:50])
        return
    if callback_data=="mem_skip":
        tg.answer_callback(callback_id,"Ok")
        return
    # Kategorie-Menu - sofort pruefen
    if callback_data.startswith("cmd:"):
        _befehl = callback_data[4:]
        tg.answer_callback(callback_id, _befehl[:30])
        import threading as _cth
        def _crun():
            try:
                _r = tg.handle(_befehl)
                if _r: tg.send(str(_r))
            except Exception as _ce:
                tg.send('Button-Fehler: ' + str(_ce)[:150])
        _cth.Thread(target=_crun, daemon=True).start()
        return None
    if callback_data.startswith("menu:") and callback_data != "menu:hauptmenu":
        key = callback_data[5:]
        if key in tg.MENU:
            _kat = tg.MENU[key]
            _btns = []
            for _bef, _desc, _bsp in _kat["befehle"]:
                _payload = ("cmd:" + _bsp)[:62]
                _btns.append([(_bef + " - " + _desc[:28], _payload)])
            _btns.append([("<< Hauptmenue", "menu:hauptmenu")])
            tg.answer_callback(callback_id, _kat["label"])
            tg.send_keyboard(_kat["label"] + " (antippen = ausfuehren):", _btns)
            return None
        tg.answer_callback(callback_id, "Unbekannt")
        return "Unbekannte Kategorie"
    # Zurueck zum Hauptmenu
    if callback_data == "menu:hauptmenu":
        tg.answer_callback(callback_id, "Hauptmenu")
        tg.send_keyboard("JACK Befehlszentrale:", tg.menu_hauptseite())
        return None
    # Gedanken-Popup: was macht JACK gerade
    try:
        import datetime as _dt
        _lines = open(os.path.expanduser("~/jack/jack_decisions.log")).readlines()
        _last = _lines[-1].split("|")[-1].strip()[:30] if _lines else "..."
        tg.answer_callback(callback_id, _last)
    except Exception:
        tg.answer_callback(callback_id)
    import jack_log

    if callback_data.startswith("approve:"):
        fix_id = callback_data[8:]
        try:
            fixes = json.load(open(os.path.expanduser("~/jack/jack_fixes.json")))
            fix = fixes.get(fix_id)
            if not fix:
                return f"Fix nicht gefunden: {fix_id}"
            import subprocess
            r = subprocess.run(["python3", fix["pfad"]],
                capture_output=True, text=True, timeout=0)
            output = (r.stdout + r.stderr).strip()[:400]
            jack_log.log_decision("APPROVE-FIX-BUTTON", f"{fix_id}: {output[:80]}")
            return f"Fix ausgefuehrt:\n{output}"
        except Exception as _e:
            return f"Fehler: {str(_e)[:200]}"

    if callback_data.startswith("reject:"):
        fix_id = callback_data[7:]
        try:
            neg = {}
            neg_path = os.path.expanduser("~/jack/negative_patterns.json")
            try: neg = json.load(open(neg_path))
            except Exception: pass
            neg[fix_id] = {"rejected": True, "count": neg.get(fix_id, {}).get("count", 0) + 1}
            json.dump(neg, open(neg_path, "w"), indent=2)
            jack_log.log_decision("REJECT-FIX-BUTTON", f"{fix_id} abgelehnt")
            return f"Verstanden. Merke mir: {fix_id} ist unerwuenscht."
        except Exception as _e:
            return f"Fehler: {str(_e)[:200]}"

    if callback_data.startswith("status:"):
        import sqlite3 as _sq
        try:
            con = _sq.connect(os.path.expanduser("~/jack/jack_errors.db"))
            n = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
            con.close()
        except Exception:
            n = "?"
        from kortex_memory import get_recent
        mem = get_recent(limit=2)
        mem_str = "\n".join([f'  [{r["category"]}] {r["content"][:150]}' for r in mem])
        lines = open(os.path.expanduser("~/jack/jack_decisions.log")).readlines()
        letzter = lines[-1].strip() if lines else "-"
        return f"📊 Status | Fehler offen: {n}\n\nLetzte Aktion:\n{letzter[:150]}\n\nGedaechtnis:\n{mem_str}"
    if callback_data.startswith("suche:"):
        q = callback_data.split(":",1)[1]
        from kortex_memory import search_memory
        results = search_memory(q, limit=3)
        if not results or isinstance(results, dict):
            return f"Nichts gefunden fuer: {q}"
        return "\n".join([f'[{r["category"]}] {r["content"][:80]}' for r in results])
    if callback_data.startswith("bugfix_deploy:"):
        bug_id = int(callback_data.split(":")[1])
        import jack_bugfix_loop as _bl
        _bl.markiere_resolved(bug_id, "manuell freigegeben")
        # Backup loeschen
        import glob as _gl
        for bak in _gl.glob(os.path.expanduser("~/jack/*.bugfix_bak")):
            try: os.remove(bak)
            except Exception: pass
        import jack_log; jack_log.log_decision("BUGFIX-DEPLOYED", f"Bug #{bug_id} gefixt und freigegeben")
        return f"Bug #{bug_id} als geloest markiert. Backup entfernt."

    if callback_data.startswith("bugfix_rollback:"):
        bug_id = int(callback_data.split(":")[1])
        import jack_bugfix_loop as _bl, glob as _gl
        count = 0
        for bak in _gl.glob(os.path.expanduser("~/jack/*.bugfix_bak")):
            _bl.rollback(bak.replace(".bugfix_bak",""))
            count += 1
        return f"Rollback durchgefuehrt ({count} Dateien). Bug #{bug_id} bleibt offen."

    if callback_data.startswith("intent:"):
        akt = callback_data[7:]
        if akt == "abbruch":
            return "Alles klar, lass ich."
        try:
            import jack_intent as _ji
            res = _ji.execute({'intent': akt, 'methode': 'button', 'confidence': 1.0, '_text': 'Button'})
            return res
        except Exception as _e:
            return "Fehler: " + str(_e)[:150]

    if callback_data == "scan_now":
        import jack_monitor as _mon
        return _mon.vollscan()
    if callback_data == "oracle_result":
        try:
            import json as _j, os as _o
            r = _j.load(open(_o.path.expanduser("~/jack-commands/jack_result.json")))
            return "Ergebnis (" + r.get("uuid","?") + "):" + chr(10) + r.get("result","?")[:3000]
        except Exception as e:
            return "Kein Ergebnis: " + str(e)
    if callback_data.startswith("oracle:"):
        import subprocess as _sp, datetime as _dt, sqlite3 as _sq, os as _o2
        cmd = callback_data[7:]
        try:
            if cmd == "dienste":
                svcs = ["jack_cortex","jack_telegram","jack_waechter","ollama"]
                paths = ["/data/data/com.termux/files/usr/var/service/"+s for s in svcs]
                r = _sp.run(["sv","status"]+paths, capture_output=True, text=True, timeout=10)
                return "Oracle [dienste]:" + chr(10) + r.stdout.strip()
            elif cmd == "ram":
                lines = [l.strip() for l in open("/proc/meminfo") if "MemTotal" in l or "MemAvailable" in l or "SwapFree" in l]
                return "Oracle [ram]:" + chr(10) + chr(10).join(lines)
            elif cmd == "fehler":
                con = _sq.connect(_o2.path.expanduser("~/jack/jack_errors.db"))
                rows = con.execute("SELECT error_msg, timestamp FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 5").fetchall()
                con.close()
                if not rows: return "Oracle [fehler]: Keine offenen Fehler"
                zeilen = ["[" + r[1][:16] + "] " + r[0][:80] for r in rows]
                return "Oracle [fehler]:" + chr(10) + chr(10).join(zeilen)
            elif cmd == "budget":
                import jack_budget
                return "Oracle [budget]:" + chr(10) + jack_budget.status()
            elif cmd == "log":
                import jack_log
                return "Oracle [log]:" + chr(10) + jack_log.recent(10)
            elif cmd == "datum":
                return "Oracle [datum]:" + chr(10) + _dt.datetime.now().strftime("%A, %d.%m.%Y %H:%M:%S")
            elif cmd == "modelle":
                r = _sp.run(["ollama","list"], capture_output=True, text=True, timeout=10)
                return "Oracle [modelle]:" + chr(10) + r.stdout.strip()
            else:
                return "Unbekannter Oracle-Befehl: " + cmd
        except Exception as _e:
            return "Oracle [" + cmd + "] Fehler: " + str(_e)[:200]
    if callback_data.startswith("intent:"):
        akt=callback_data[7:]
        if akt=="abbruch": return "Abgebrochen."
        try:
            import jack_intent as _ji
            res=_ji.execute({'intent':akt,'methode':'button','confidence':1.0,'_text':'Button'})
            return str(res) if res else "Erledigt."
        except Exception as e: return "Fehler: "+str(e)[:100]
    if callback_data.startswith("oracle:"):
        cmd=callback_data[7:]
        import subprocess as _sp, sqlite3 as _sq, os as _o2
        if cmd=="dienste":
            svcs=["jack_cortex","jack_telegram","jack_waechter","ollama"]
            r=_sp.run(["sv","status"]+["/data/data/com.termux/files/usr/var/service/"+s for s in svcs],capture_output=True,text=True,timeout=10)
            return "Dienste:"+chr(10)+r.stdout.strip()
        if cmd=="ram":
            lines=[l.strip() for l in open("/proc/meminfo") if "MemAvailable" in l or "MemTotal" in l]
            return "RAM:"+chr(10)+chr(10).join(lines)
    if callback_data=="selfsee_go":
        try:
            import signal as _sig; _sig.alarm(0)
        except Exception:
            pass
        tg.answer_callback(callback_id,"Laeuft...")
        def _go():
            try:
                import jack_selfsee as _ss
                tg.send(_ss.deep())
            except Exception as e:
                tg.send("Selfsee-Fehler: "+str(e)[:160])
        import threading as _th
        _th.Thread(target=_go, daemon=True).start()
        return
    if callback_data=="selfsee_no":
        try:
            import os
            _p="/data/data/com.termux/files/home/jack/.selfsee_pending"
            if os.path.isfile(_p): os.remove(_p)
        except Exception:
            pass
        return "Ok, beendet. Kein Fix."
    return f"Unbekannter Button: {callback_data}"
