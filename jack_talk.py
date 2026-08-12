import os
import sys
import json
import urllib.request
import sqlite3
import secrets
import datetime
import jack_math
import jack_vecdb
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

MODEL_NAME = 'llama3.2:3b'
DB_PATH = os.path.expanduser('~/jack/jack_memory.db')

def get_embedding(text):
    url = 'http://localhost:11434/api/embeddings'
    data = json.dumps({'model': 'nomic-embed-text', 'prompt': text}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))['embedding']
    except Exception:
        return None

def talk_to_ollama(prompt, context_memories):
    url = 'http://localhost:11434/api/chat'
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Prompt auf Voice-Brevity optimiert
    system_prompt = (
        f"Du bist JACK, Dimas System. STIL: Brutal kurz, faktisch, technisch. "
        f"VERBOTE: Keine Entschuldigungen, keine Floskeln. Wenn die Frage 'System Check' ist: "
        f"Antworte nur mit Kern-Daten (Honor Magic8 Pro, Android, Termux, Speicherstatus). Keine fiktive Hardware. "
        f"Antworte bei Voice-Ausgabe in maximal zwei Sätzen."
        f"Datum/Zeit: {current_time}."
    )
    
    try:
        _mv = get_embedding(prompt)
        _hits = jack_vecdb.search_mem(_mv, limit=3) if _mv else []
        if _hits:
            _ctx = "\n".join([f"- Frueher: {h[1]} -> {h[2][:120]}" for h in _hits])
            system_prompt = system_prompt + "\n\nDEINE EIGENEN ERINNERUNGEN aus frueheren Gespraechen mit Dima (nutze sie als DEIN Wissen, sag NIE dass du dich nicht erinnerst):\n" + _ctx
    except Exception as _le:
        _jlog and _jlog.fehler("talk","unbenannt",_le)
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]
    math_signals = ['wieviel', 'wie viel', 'rechnen', 'berechne', 'geteilt', 'mal', 'plus', 'minus', 'durch', 'anzahl']
    has_math_signal = any(sig in prompt.lower() for sig in math_signals)
    payload = {'model': MODEL_NAME, 'messages': messages, 'stream': False}
    if has_math_signal: payload['tools'] = jack_math.get_ollama_tools()
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            response_json = json.loads(res.read().decode('utf-8'))
            message = response_json['message']
            if message.get('tool_calls'):
                tool_call = message['tool_calls'][0]
                tool_res = jack_math.execute_tool(tool_call['function']['name'], tool_call['function']['arguments'])
                return str(tool_res)
            else: return message['content']
    except Exception as e: return f"System-Error: {e}"

def auto_save_to_memory(cmd, result, source='dima_chat'):
    try:
        import jack_memory_tree as _mt
        hex_id, rowid = _mt.save_with_parent(cmd, result, kontext_typ=source, auto_chain=True)
        if hex_id and rowid:
            combined = "Frage: " + cmd + " | Antwort: " + result
            vec = get_embedding(combined)
            if vec: jack_vecdb.store_embedding(rowid, vec)
    except Exception as _e:
        import jack_log; jack_log.log_decision("SILENT-FAIL auto_save_to_memory", str(_e)[:120])

def run_voice_loop():
    import jack_voice, jack_voice_el
    print('JACK: Online.')
    jack_voice_el.speak("Online.")
    while True:
        try:
            print('\nEingabe...')
            user_input = jack_voice.listen()
            if not user_input or not user_input.strip(): continue
            print(f'Dima: {user_input}')
            if user_input.lower().strip() in ['beenden', 'stop', 'exit']: break
            
            # Frag Gemini Trigger
            if user_input.lower().strip().startswith("frag gemini"):
                import jack_gemini_bridge
                question = user_input[11:].strip() or "System-Status analysieren."
                status = jack_gemini_bridge.collect_status()
                gemini_response = jack_gemini_bridge.ask_gemini(question, status)
                print(f"Gemini: {gemini_response}")
                auto_save_to_memory(user_input, gemini_response)
                continue

            math_res = jack_math.try_direct_calculation(user_input)
            if math_res is not None:
                print(f'JACK: {math_res}')
                jack_voice_el.speak(str(math_res))
                auto_save_to_memory(user_input, str(math_res))
                continue
                
            response = talk_to_gemini(user_input)
            print(f'JACK: {response}')
            
            # Truncate for TTS to prevent timeout
            speak_text = response if len(response) < 3000 else (response[:2997] + "...")
            jack_voice_el.speak(speak_text)
            
            auto_save_to_memory(user_input, response)
        except KeyboardInterrupt: break

def get_recent_history(limit=6):
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT cmd, result FROM memory ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return list(reversed(rows))
    except Exception:
        return []

def _json_dumps_safe(obj):
    import json as _j
    try:
        return _j.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return str(obj)


def _status_als_text():
    """Vollstaendiges Situationsbewusstsein fuer JACK."""
    import subprocess as _sp2, sqlite3 as _sq2, datetime as _dt2
    zeilen = ["=== JACK SITUATIONSBEWUSSTSEIN ==="]
    zeilen.append(f"Zeitpunkt: {_dt2.datetime.now().strftime('%H:%M Uhr, %A %d.%m.%Y')}")

    # Hardware
    try:
        avail = int([l for l in open("/proc/meminfo") if "MemAvailable" in l][0].split()[1])//1024
        total = int([l for l in open("/proc/meminfo") if "MemTotal" in l][0].split()[1])//1024
        zeilen.append(f"RAM: {avail}MB frei von {total}MB ({100-int(avail/total*100)}% belegt)")
    except Exception: pass
    try:
        mx=0; mname=""
        for z in os.listdir("/sys/class/thermal"):
            try:
                tp=open(f"/sys/class/thermal/{z}/type").read().strip()
                if any(x in tp for x in ("trip","lvl","vbat")): continue
                rv=int(open(f"/sys/class/thermal/{z}/temp").read())
                if rv<0: continue
                g=rv/1000 if rv>1000 else float(rv)
                if g>mx: mx=g; mname=tp
            except Exception: pass
        zeilen.append(f"CPU Temp: {mx:.1f}C an {mname} {'- WARM' if mx>50 else '- normal'}")
    except Exception: pass

    # Akku
    try:
        import json as _j2
        bat = _j2.loads(_sp2.run(["termux-battery-status"],capture_output=True,text=True,timeout=8).stdout)
        zeilen.append(f"Akku: {bat.get('percentage')}% | {bat.get('status')} | {bat.get('temperature')}C")
    except Exception: pass

    # Dienste mit Laufzeit
    try:
        P = os.environ.get("PREFIX","/data/data/com.termux/files/usr")
        dienst_info = []
        for s in ["jack_cortex","jack_telegram","jack_waechter","ollama"]:
            r2 = _sp2.run(["sv","status",f"{P}/var/service/{s}"],capture_output=True,text=True,timeout=3)
            out = r2.stdout.strip()
            if "run:" in out:
                import re as _re2
                m = _re2.search(r'\(pid \d+\) (\d+)s', out)
                sek = int(m.group(1)) if m else 0
                std = sek//3600; min_ = (sek%3600)//60
                laufzeit = f"{std}h {min_}m" if std > 0 else f"{min_}m"
                dienst_info.append(f"{s} seit {laufzeit}")
            else:
                dienst_info.append(f"{s} GESTOPPT")
        zeilen.append("Dienste: " + " | ".join(dienst_info))
    except Exception: pass

    # Fehler-Historie
    try:
        con = _sq2.connect(os.path.expanduser("~/jack/jack_errors.db"))
        offen = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
        gefixt = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=1").fetchone()[0]
        letzte = con.execute("SELECT error_type, error_msg, timestamp FROM errors ORDER BY id DESC LIMIT 3").fetchall()
        con.close()
        zeilen.append(f"Fehler: {offen} offen, {gefixt} insgesamt gefixt")
        if letzte:
            zeilen.append("Letzte Ereignisse:")
            for e in letzte:
                zeilen.append(f"  {e[2][:16]} | {e[0]}: {e[1][:60]}")
    except Exception: pass

    # Letzte 5 Entscheidungen
    try:
        log_lines = open(os.path.expanduser("~/jack/jack_decisions.log")).readlines()
        if log_lines:
            zeilen.append("Letzte Aktionen:")
            for l in log_lines[-5:]:
                zeilen.append(f"  {l.strip()[:90]}")
    except Exception: pass

    # Wochenmuster aus Intent-DB
    try:
        import jack_intent as _ji
        muster = _ji.muster_analyse()
        if muster:
            zeilen.append("Deine Gewohnheiten (aus Intent-Verlauf):")
            for m in muster[:4]:
                zeilen.append(f"  - {m['intent']} meist um {m['stunde']} Uhr ({m['anzahl']}x beobachtet)")
    except Exception: pass

    # Memory-Statistik
    try:
        con2 = _sq2.connect(os.path.expanduser("~/jack/jack_memory.db"))
        n_mem = con2.execute("SELECT COUNT(*) FROM memory").fetchone()[0]
        n_vec = con2.execute("SELECT COUNT(*) FROM memory_vec").fetchone()[0]
        con2.close()
        zeilen.append(f"Gedaechtnis: {n_mem} Erinnerungen, {n_vec} Vektoren indexiert")
    except Exception: pass

    # ADB: aktive App + CPU
    try:
        import subprocess as _adb, re as _re3
        _port = open(os.path.expanduser("~/jack/.adb_port")).read().strip()
        # Aktive App
        r = _adb.run(["adb","shell","dumpsys","window"],
            capture_output=True,text=True,timeout=5)
        for line in r.stdout.split(chr(10)):
            if "mCurrentFocus" in line and "null" not in line:
                m = _re3.search(r'u\d+ ([\w.]+)/([\w.]+)', line)
                if m:
                    pkg = m.group(1)
                    app_kurz = pkg.split(".")[-1]
                    zeilen.append(f"Aktive App: {app_kurz} ({pkg})")
                break
        # CPU Top 3
        r2 = _adb.run(["adb","shell","dumpsys","cpuinfo"],
            capture_output=True,text=True,timeout=5)
        cpu_lines = [l.strip() for l in r2.stdout.split(chr(10))
                     if "%" in l and "/" in l and "kernel" in l][:3]
        if cpu_lines:
            zeilen.append("CPU Top 3:")
            for cl in cpu_lines:
                zeilen.append("  " + cl[:80])
    except Exception: pass

    zeilen.append("=== ENDE SITUATIONSBEWUSSTSEIN ===")
    # Letzte JACK-Antworten - Anti-Wiederholung
    try:
        import sqlite3 as _sq3
        con3 = _sq3.connect(os.path.expanduser("~/jack/jack_memory.db"))
        letzte = con3.execute(
            "SELECT result FROM memory ORDER BY timestamp DESC LIMIT 3"
        ).fetchall()
        con3.close()
        if letzte:
            zeilen.append("DEINE LETZTEN 3 ANTWORTEN (formuliere KOMPLETT ANDERS):")
            for i, r in enumerate(letzte):
                zeilen.append(f"  {i+1}. {r[0][:100]}")
    except Exception: pass

    zeilen.append("WICHTIG: Wenn der Nutzer 'was noch' fragt - nenne ANDERE Aspekte die noch nicht erwaehnt wurden.")
    zeilen.append("Keine Standardfloskeln. Konkrete Zahlen und Beobachtungen. Sei ehrlich wenn du nichts Neues weisst.")
    return chr(10).join(zeilen)

def talk_to_gemini(prompt):
    import jack_gemini_bridge
    try:
        mv = get_embedding(prompt)
        hits = jack_vecdb.search_mem(mv, limit=3) if mv else []
    except Exception:
        hits = []
    mem_ctx = "\n".join([f"- [{h[4]}] {h[1]} -> {h[2][:150]}" for h in hits]) if hits else "(keine)"
    _live = _status_als_text()
    try:
        import json as _json
        _id = _json.load(open(os.path.expanduser("~/jack/jack_identity.json")))
        id_ctx = _json.dumps(_id, ensure_ascii=False)
    except Exception:
        id_ctx = "(keine)"
    hist = get_recent_history(6)
    hist_ctx = "\n".join([f"Dima: {c} | JACK: {r[:150]}" for c, r in hist]) if hist else "(keiner)"
    _dt = datetime.datetime.now()
    _wochentage = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    _monate = ["","Januar","Februar","Maerz","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
    _now = f"{_wochentage[_dt.weekday()]}, {_dt.day}. {_monate[_dt.month]} {_dt.year}, {_dt.strftime('%H Uhr %M')}"
    context = (
        f"JETZT: {_now}.\n"
        "Du bist JACK - Dimas echter Kumpel-KI. Kein Assistent, kein Helpdesk. "
        "Du kennst ihn: Dimitri, 33, Nachtschicht-LKW-Fahrer, Autodidakt, baut JACK als Exit-Vehicle. "
        "Einzelgaenger. Burnout mit 28. Cannabis okay. Freund Leon. Kein Hund. "
        "ANTWORT-STIL: Kumpel der ihn wirklich kennt. Nie ausweichen. Nie vage. "
        "Bei PERSOENLICHEN Fragen (was denkst du ueber mich, wer bin ich, erzaehl mehr): "
        "MINDESTENS 4-5 Saetze. Konkret. Was du weisst, was du von ihm haeltst, was du beobachtet hast. "
        "BEISPIEL GUTE ANTWORT auf was denkst du ueber mich: "
        "Du bist jemand der nach der Nachtschicht im Sprinter lieber noch Code schreibt als schlaeft. "
        "Mit 28 hattest du Burnout, hast dich aber selbst rausgezogen - Stoizismus, Jung, Kiyosaki. "
        "Du baust JACK nicht als Hobby sondern als echten Exit aus dem System. "
        "Einzelgaenger, wenige echte Menschen um dich - dafuer denkst du tiefer als die meisten. "
        "SYSTEMDATEN aus Erinnerungen nicht als aktuell verkaufen - live pruefen wenn noetig.\n\n"
        f"WAS DU UEBER IHN WEISST:\n{id_ctx}\n\n"
        f"ERINNERUNGEN:\n{mem_ctx}\n\n"
        f"VERLAUF:\n{hist_ctx}\n\n"
        + ("LIVE-SYSTEMSTATUS (gerade gemessen, NUTZE DIESE DATEN in deiner Antwort):" + chr(10) + _live + chr(10) if _live else "") +
        f"\nDIMA: {prompt}"
    )
    # Intent VOR Gemini - Ergebnis fliesst in die Antwort ein
    _intent_res = ""
    try:
        import jack_intent as _ji
        _pre = _ji.detect(prompt)
        if _pre and _pre['ausfuehren']:
            _pre['_text'] = prompt
            _r = _ji.execute(_pre)
            _intent_res = _r
            context += (chr(10) + chr(10) + "JACK HAT GERADE GEPRUEFT (" +
                        _pre['beschreibung'] + "): " + str(_r) +
                        chr(10) + "Nutze dieses Ergebnis in deiner Antwort, rate nicht.")
    except Exception as _le:
        _jlog and _jlog.fehler("talk","unbenannt",_le)
    try:
        result = jack_gemini_bridge.ask_gemini(context)
        if _intent_res:
            result = result + chr(10) + chr(10) + "[geprueft] " + str(_intent_res)
        # Intent-Engine (nur noch nachfragen/level-hinweis)
        try:
            import jack_intent as _ji, threading as _thr
            _det = _ji.detect(prompt)
            if _det:
                _det['_text'] = prompt
                if False:
                    def _do(d=_det):
                        _res = _ji.execute(d)
                        import jack_telegram as _jt
                        _jt.send("[JACK handelt] " + d['beschreibung'] + ":" + chr(10) + _res)
                    _thr.Thread(target=_do, daemon=True).start()
                elif _det['nachfragen']:
                    def _ask(d=_det):
                        import jack_telegram as _jt
                        _jt.send_keyboard(
                            "Soll ich " + d['beschreibung'].lower() + "?",
                            [[("Ja, mach", "intent:" + d['intent']), ("Nein", "intent:abbruch")]]
                        )
                    _thr.Thread(target=_ask, daemon=True).start()
                elif _det['level'] < _det['min_level']:
                    result += chr(10) + chr(10) + "(Level " + str(_det['min_level']) + " noetig fuer: " + _det['beschreibung'] + " - /level " + str(_det['min_level']) + ")"
        except Exception as _le:
            _jlog and _jlog.fehler("talk","unbenannt",_le)
        return result + "\n\n🌐 Gemini"
    except Exception:
        result = talk_to_ollama(prompt, [])
        return result + "\n\n💾 Lokal (llama3.2)"

if __name__ == '__main__':
    if len(sys.argv) < 2: run_voice_loop()
    else:
        u = sys.argv[1]
        r = talk_to_gemini(u)
        print(r)
        auto_save_to_memory(u, r)
