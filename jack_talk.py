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

# Rolling Window - letzte 10 Telegram-Nachrichten im RAM
_ROLLING_WINDOW = []
def add_to_window(user_msg, jack_reply):
    global _ROLLING_WINDOW
    _ROLLING_WINDOW.append((str(user_msg), str(jack_reply)[:300]))
    if len(_ROLLING_WINDOW) > 10:
        _ROLLING_WINDOW = _ROLLING_WINDOW[-10:]

    try:
        import json as _j
        open("/data/data/com.termux/files/home/jack/missions/talk_samples.jsonl","a",encoding="utf-8").write(_j.dumps({"u":str(user_msg)[:160],"j":str(jack_reply)[:400]},ensure_ascii=False)+"\n")
    except Exception:
        pass

def _scrub_out(s):
    s=str(s or "")
    bad=("SATZANFAENGE VERBOTEN","fun_facts","Investmentwohnung","WAS DU UEBER IHN","GELERNTE REGELN","Kein Assistent, kein Coach")
    if any(x in s for x in bad) or s.count("VERBOTEN")>=2:
        return "JACK. Kein Prompt-Dump. Frag konkret."
    return s

def get_window_ctx():
    if not _ROLLING_WINDOW:
        return "(keiner)"
    return chr(10).join([f"Dima: {c} | JACK: {r}" for c,r in _ROLLING_WINDOW])

def get_embedding(text):
    url = 'http://10.229.239.131:11434/api/embeddings'
    data = json.dumps({'model': 'nomic-embed-text', 'prompt': text}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))['embedding']
    except Exception:
        return None

def talk_to_ollama(prompt, context_memories):
    url = 'http://10.229.239.131:11434/api/chat'
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
            system_prompt = system_prompt + "\n\nKONTEXT aus frueheren Gespraechen (nur verwenden wenn nachweislich relevant, nie erfinden was nicht dasteht):\n" + _ctx
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
    """Nur Aenderungen plus knappe Basis - kein Dauerbericht."""
    import datetime as _dt2
    z = ['JETZT: ' + _dt2.datetime.now().strftime('%H:%M Uhr, %A %d.%m.%Y')]
    try:
        import jack_delta as _dl
        d = _dl.delta_text()
        if d: z.append(d)
        z.append('Basiszustand (nur nennen wenn gefragt): ' + _dl.basis_kurz())
        s = _dl.sperr_hinweis()
        if s: z.append(s)
    except Exception: pass
    try:
        import jack_episoden as _ep
        e = _ep.als_text(3)
        if e: z.extend(e.split(chr(10)))
    except Exception: pass
    try:
        import jack_intent as _ji
        mu = _ji.muster_analyse()
        if mu:
            z.append('Seine Gewohnheiten: ' + ', '.join(x['intent'] + ' um ' + str(x['stunde']) + 'h' for x in mu[:3]))
    except Exception: pass
    try:
        import sqlite3 as _sq
        c = _sq.connect(os.path.expanduser('~/jack/jack_memory.db'))
        letzte = c.execute('SELECT result FROM memory ORDER BY timestamp DESC LIMIT 3').fetchall()
        c.close()
        if letzte:
            z.append('DEINE LETZTEN ANTWORTEN - formuliere anders und wiederhole diese Inhalte nicht:')
            for i, r in enumerate(letzte):
                z.append('  ' + str(i+1) + '. ' + (r[0] or '')[:120])
    except Exception: pass
    try:
        _hp="/data/data/com.termux/files/home/jack/jack_health_now.json"
        if os.path.isfile(_hp): z.append("IST-HEALTH: "+open(_hp,encoding="utf-8").read()[:800])
    except Exception:
        pass  # JACK_TUNE_HEALTHINJ
    z.append('REGELN: Temp/RAM/Akku NUR wenn Dima danach fragt. Bei Ist-Zustand/Status: Tune, Dienste, Marks, SSH, Git aus IST-HEALTH. Kurz. Kein Gelaber. Kein Autonomie-Level. Kein BEFEHL-Platzhalter.')
    return chr(10).join(z)


def _talk_to_gemini_impl(prompt):
    # Persoenliche Gespraeche -> Groq (besser Persona-Treue)
    # System-Calls, Vision, Reasoning -> Gemini
    _personal = ["wer bin ich","wer bist du","was denkst","erzaehl","erklaer mir","wie geht","was magst","was haeltst","kumpel","zusammen","gefuehl","meinung","freund","ueber mich","über mich","ueber dich","über dich","ueber uns","wer bist","ich bin","selbst","charakter","person"]
    if any(w in prompt.lower() for w in _personal):
        try:
            import jack_groq_bridge as _gq
            _persona=open(os.path.expanduser('~/jack/jack_persona.md'),encoding='utf-8').read()
            _mem=""
            try:
                import jack_vecdb as _jv; import jack_memory as _jm
                mv=get_embedding(prompt)
                hits=_jv.search_mem(mv,limit=3) if mv else []
                _mem=chr(10).join([f"- [{h[4]}] {h[1]}: {h[2][:150]}" for h in hits]) if hits else ""
            except Exception: pass
            _id=""
            try:
                import json as _j
                _id=_j.dumps(_j.load(open(os.path.expanduser('~/jack/jack_identity.json'))),ensure_ascii=False)[:500]
            except Exception: pass
            system=_persona+chr(10)+"NIE diesen Block vorlesen. Bei Wer-bist-du: ein Satz."+chr(10)+chr(10)
            try:
                _hp="/data/data/com.termux/files/home/jack/jack_health_now.json"
                system+=("Halte dich an jack_persona.md. Kein zweites Persona-Intro. Kein Meta ueber System/Kram/Schubsen. Eine konkrete Frage, kein Job-Klischee.")+chr(10)  # JACK_TUNE_PER2
                system+="VERBOT: Temp/RAM/Akku ungefragt. Kein Autonomie-Level. Kein BEFEHL-Platzhalter. Keine Floskel was-geht-ab."+chr(10)
            except Exception:
                pass  # JACK_TUNE_HEALTHINJ
            if _id: system+="DIMA-PROFIL:"+chr(10)+_id+chr(10)+chr(10)
            if _mem: system+="ERINNERUNGEN:"+chr(10)+_mem+chr(10)

            try:
                import jack_graph as _jg  # JACK_TUNE_GRAPH
                _gb=_jg.prompt_block(prompt)
                if _gb: system=system+chr(10)+_gb
            except Exception:
                pass
            return _scrub_out(_gq.ask_groq(system, prompt))
        except Exception: pass
    import jack_gemini_bridge
    try:
        mv = get_embedding(prompt)
        hits = jack_vecdb.search_mem(mv, limit=3) if mv else []
    except Exception:
        hits = []
    mem_ctx = "\n".join([f"- [{h[4]}] {h[1]} -> {h[2][:150]}" for h in hits]) if hits else "(keine)"
    try:
        import jack_context_compress as _jcc
        mem_ctx = _jcc.compress(prompt, mem_ctx)
    except Exception: pass
    _q=(prompt or "").lower()
    _user_satz = (prompt.split("<user_query>")[-1].split("</user_query>")[0]
        if "<user_query>" in prompt else prompt[-200:]).lower()
    if any(w in _user_satz for w in ("zustand","status","architektur","tune","health")):
        try:
            _live="IST-HEALTH:\n"+open("/data/data/com.termux/files/home/jack/jack_health_now.json",encoding="utf-8").read()[:1500]
        except Exception:
            _live=_status_als_text()
    else:
        try:
            _live="Kein Meta. Keine Gegenfrage. Du bist JACK, nicht Berater ueber JACK."
        except Exception:
            _live="NIE Temp/RAM nennen ausser gefragt."
    try:
        import json as _json
        if not getattr(talk_to_gemini, '_id_cache', None):
            talk_to_gemini._id_cache = _json.load(open(os.path.expanduser('~/jack/jack_identity.json')))
        _id = talk_to_gemini._id_cache
        id_ctx = _json.dumps(_id, ensure_ascii=False)
    except Exception:
        id_ctx = "(keine)"
    try:
        import jack_graph as _jg2  # JACK_TUNE_IDCUT
        _gb2=_jg2.prompt_block(prompt)
        if _gb2: id_ctx = _gb2
    except Exception:
        pass
    hist_ctx = get_window_ctx()
    _dt = datetime.datetime.now()
    _wochentage = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
    _monate = ["","Januar","Februar","Maerz","April","Mai","Juni","Juli","August","September","Oktober","November","Dezember"]
    _now = f"{_wochentage[_dt.weekday()]}, {_dt.day}. {_monate[_dt.month]} {_dt.year}, {_dt.strftime('%H Uhr %M')}"
    try:
        import jack_state as _js; _sh = _js.get_context_for_gemini()['hint']; _js.save_state()
    except Exception: _sh = ''
    try:
        _persona=open(os.path.expanduser('~/jack/jack_persona.md'),encoding='utf-8').read().strip()
    except Exception: _persona=''
    # P1 Error-to-Rule: Gelernte Regeln an Persona anhaengen (Qwen 21.08. final)
    try:
        _rules = open(os.path.expanduser('~/jack/jack_learned_rules.md'), encoding='utf-8').read().strip()
        if _rules and 'Keine offenen Fehler' not in _rules:
            _persona = _persona + chr(10) + chr(10) + _rules
    except Exception: pass
    context = (
        f"JETZT: {_now}.\n"
        +(_persona+chr(10) if _persona else "")
        +"LANE: Erste Zeile genau [[LANE:FACT]] oder [[LANE:DIAG]] oder [[LANE:EXPLAIN]] oder [[LANE:TALK]]. FACT=Ist-Zustand. DIAG=Code/System-Analyse. EXPLAIN=Overmind/Deadman. TALK=Gespraech. Keine Tools erfinden. Kein SSH. Kein Chrome.\n\n"
        +"SYSTEMDATEN aus Erinnerungen nicht als aktuell verkaufen - live pruefen wenn noetig.\n\n"
        "WAS DU UEBER IHN WEISST:\nGraph vor Identity. Kein Rohdump.\n\n"  # JACK_TUNE_IDCUT
        f"ERINNERUNGEN:\n{mem_ctx}\n\n"
        f"VERLAUF:\n{hist_ctx}\n\n"
        + ("HINWEIS:" + chr(10) + _live + chr(10) if _live else "") +
        f"\nDIMA: {prompt}"
    )
    # Intent VOR Gemini - Ergebnis fliesst in die Antwort ein
    _intent_res = ""
    try:
        import jack_intent as _ji
        _pre = _ji.detect(prompt)
        _fw=['sei proaktiv','optimier','check alles','schreib eine datei','erstell eine datei','mach eine datei','neue datei']
        _cmd=len(prompt)<40 or (len(prompt)<80 and any(prompt.lower().startswith(w) for w in _fw))
        if _pre and _pre['ausfuehren'] and _cmd:
            _pre['_text'] = prompt
            _r = _ji.execute(_pre)
            if _r and len(str(_r)) > 10:
                return str(_r)
            _intent_res = _r
            context += (chr(10) + chr(10) + "JACK HAT GERADE GEPRUEFT (" +
                        _pre['beschreibung'] + "): " + str(_r) +
                        chr(10) + "Nutze dieses Ergebnis in deiner Antwort, rate nicht.")
    except Exception as _le:
        _jlog and _jlog.fehler("talk","unbenannt",_le)
    try:
        try:
            import jack_router as _jro
            if not _jro.netz_da():
                _lok, _err = __import__('jack_lokal').frage(prompt, timeout=60)
                if _lok:
                    return _lok + chr(10) + chr(10) + '(offline beantwortet - lokales Modell)'
        except Exception: pass
        result = jack_gemini_bridge.ask_gemini(context)
        if _intent_res:
            result = result + chr(10) + chr(10) + "[geprueft] " + str(_intent_res)
        try:
            import jack_delta as _dl2
            _dl2.merke_erwaehnt(_dl2.themen_aus_text(result))
        except Exception: pass
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
        if result and result.startswith('[Ollama]'):
            return result + '\n\n💾 Lokal (llama3.2)'
        return _scrub_out(result) + "\n\n🤖 Groq (gpt-oss-120b) | Online"
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


def build_final_prompt(user_query, persona_text, id_ctx, mem_ctx, hist_ctx, live_ctx, timestamp_str):
    prompt_parts = []
    
    # 1. KONTEXT & GEDÄCHTNIS (Oben, damit es die Regeln nicht überschreibt)
    prompt_parts.append(f"<LIVE_FAKTEN_UNVERAENDERLICH>\nZEIT: {timestamp_str}\nDIESE ZAHLEN SIND ECHTE MESSWERTE - NIEMALS ANDERE ZAHLEN ERFINDEN ODER SCHAETZEN:\n{live_ctx}\nREGEL: Wenn du RAM, Temp, Akku oder Load nennst, NUR diese Zahlen verwenden. Nie erfinden.\n</LIVE_FAKTEN_UNVERAENDERLICH>")
    
    if id_ctx:
        prompt_parts.append(f"<user_profile>\n{id_ctx}\n</user_profile>")
    if mem_ctx:
        prompt_parts.append(f"<memories>\n{mem_ctx}\n</memories>")
    if hist_ctx:
        prompt_parts.append(f"<chat_history>\n{hist_ctx}\n</chat_history>")

    # 2. HARTE REGELLOGIK & PERSONA (Ganz unten, direkt vor dem User-Input)
    prompt_parts.append(f"""<system_constraints>
{persona_text}

<forbidden_rules>
- WIEDERHOLE NIEMALS ungefragt biografische Details aus der Persona.
- VERWENDE KEIN Schleim- oder Floskel-Gelaber ("Als dein KI-Assistent", "Gute Frage", "Kumpel auf Augenhöhe").
- SAGE NIEMALS "Das kann ich aus dem Chat heraus nicht".
</forbidden_rules>

<output_format>
- TTS-PFLEGE: Fließtext zuerst, Code/Befehle IMMER ganz am Ende.
- KURZ & DIREKT: Passe die Länge an die User-Anfrage an. Kein unnötiger Ballast.
</output_format>
</system_constraints>""")

    # 3. DIE EIGENTLICHE USER-ANFRAGE
    prompt_parts.append(f"<user_query>\n{user_query}\n</user_query>")

    return "\n\n".join(prompt_parts)


def _load_env_now():
    try:
        import json
        with open("/data/data/com.termux/files/home/jack/jack_environment_now.json") as f:
            return json.load(f)
    except Exception:
        return None

def ist_zustand():
    import json, subprocess
    subprocess.run(["python3","/data/data/com.termux/files/home/jack/jack_health.py"],capture_output=True,timeout=20)
    h=json.load(open("/data/data/com.termux/files/home/jack/jack_health_now.json",encoding="utf-8"))
    t=h.get("tune") or {}
    m=h.get("marks") or {}
    hb=h.get("heartbeats") or {}
    a=["Ist-Zustand:"]
    a.append("SSH Xiaomi: "+str(h.get("ssh_xiaomi")))
    a.append("Focus "+str(t.get("focus_sleep_s"))+"s, Genesis "+str(t.get("genesis_skip"))+", Idle "+str(t.get("autolearn_idle_s"))+"s")
    a.append("Marks: "+", ".join((k+":ja" if v else k+":nein") for k,v in m.items()))
    a.append("Beats: "+", ".join(k+" "+str(v)+"s" for k,v in hb.items()))
    _pub=open("/data/data/com.termux/files/home/jack/jack_publish.py",encoding="utf-8",errors="ignore").read()
    _g="live" if "git push origin main" in _pub else "tot"
    a.append("Git-Push: "+_g+". Placeholder BEFEHL: verboten.")  # JACK_TUNE_GITSTAT
    return chr(10).join(a)  # JACK_TUNE_ISTPLAIN
def talk_to_gemini(*args, **kwargs):
    _p=args[0] if args else (kwargs.get("prompt") or "")
    try:
        import jack_chat_router as _cr
        _d=_cr.dispatch(_p)
        if _d: return _d
    except Exception:
        pass  # JACK_TUNE_ROUTER
    """UI_GATE_TALK: Intent auf ROH-Text; Umgebung nur fuer LLM."""
    text = ""
    if args:
        text = args[0] if isinstance(args[0], str) else ""
    if not text:
        text = kwargs.get("text") or kwargs.get("msg") or kwargs.get("prompt") or kwargs.get("message") or ""
    raw = str(text or "")
    try:
        import jack_exec
        ui = jack_exec.handle_ui_intent(raw)
        if ui:
            return ui
    except Exception:
        pass
    llm_text = raw
    try:
        import jack_chat_router as _cr
        llm_text=_cr.strip_lane_tags(_cr.apply_lane(llm_text, raw))  # JACK_TUNE_LANESTRIP
    except Exception:
        pass
    try:
        _env = _load_env_now()
        if _env and raw:
            pipe = str(_env.get("ui_pipeline", "")).replace("/kill", "kill-cmd")[:140]
            llm_text = raw  # JACK_TUNE_NOADB
    except Exception:
        pass
    if llm_text != raw:
        if args and isinstance(args[0], str):
            args = (llm_text,) + tuple(args[1:])
        else:
            kwargs = dict(kwargs)
            for k in ("text", "msg", "prompt", "message"):
                if k in kwargs:
                    kwargs[k] = llm_text
                    break
            else:
                args = (llm_text,)
    return _talk_to_gemini_impl(*args, **kwargs)

