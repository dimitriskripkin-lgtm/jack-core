import sys
import json
import urllib.request
import sqlite3
import secrets
import datetime
import jack_math
import jack_vecdb

MODEL_NAME = 'llama3.2:3b'
DB_PATH = '/data/data/com.termux/files/home/jack/jack_memory.db'

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
    except Exception:
        pass
    messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]
    math_signals = ['wieviel', 'wie viel', 'rechnen', 'berechne', 'geteil', 'mal', 'plus', 'minus', 'ladun', 'lkw', 'verteil', 'durch', 'anzahl', 'uhrzeit', 'datum', 'check']
    has_math_signal = any(sig in prompt.lower() for sig in math_signals)
    payload = {'model': MODEL_NAME, 'messages': messages, 'stream': False}
    if has_math_signal: payload['tools'] = jack_math.get_ollama_tools()
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as res:
            response_json = json.loads(res.read().decode('utf-8'))
            message = response_json['message']
            if 'tool_calls' in message and message['tool_calls']:
                tool_call = message['tool_calls'][0]
                tool_res = jack_math.execute_tool(tool_call['function']['name'], tool_call['function']['arguments'])
                return str(tool_res)
            else: return message['content']
    except Exception as e: return f"System-Error: {e}"

def auto_save_to_memory(cmd, result):
    hex_id = secrets.token_hex(8)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.execute('INSERT INTO memory (id, cmd, result, timestamp) VALUES (?, ?, ?, ?);', (hex_id, cmd, result, timestamp))
        rowid = cur.lastrowid
        conn.commit()
        conn.close()
        combined = f"Frage: {cmd} | Antwort: {result}"
        vec = get_embedding(combined)
        if vec: jack_vecdb.store_embedding(rowid, vec)
    except Exception: pass

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
            speak_text = response if len(response) < 400 else (response[:397] + "...")
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

def talk_to_gemini(prompt):
    import jack_gemini_bridge
    try:
        mv = get_embedding(prompt)
        hits = jack_vecdb.search_mem(mv, limit=3) if mv else []
    except Exception:
        hits = []
    mem_ctx = "\n".join([f"- {h[1]} -> {h[2][:150]}" for h in hits]) if hits else "(keine)"
    try:
        import json as _json
        _id = _json.load(open("/data/data/com.termux/files/home/jack/jack_identity.json"))
        id_ctx = _json.dumps(_id, ensure_ascii=False)
    except Exception:
        id_ctx = "(keine)"
    hist = get_recent_history(6)
    hist_ctx = "\n".join([f"Dima: {c} | JACK: {r[:150]}" for c, r in hist]) if hist else "(keiner)"
    context = (
        "Du bist JACK, Dimas System auf dem Honor. Die Erinnerungen und der Verlauf unten "
        "sind DEIN eigenes Wissen - nutze sie, sag NIE dass du dich nicht erinnerst. "
        "Dima ist der Nutzer (Nachtschicht-Fernfahrer), DU bist JACK - verwechsle das nie. "
        "Antworte kurz, direkt, Kumpel-Ton, Deutsch.\n\n"
        f"GRUNDWAHRHEIT ueber Dima und JACK (IMMER korrekt, hat VORRANG vor allem anderen):\n{id_ctx}\n\n"
        f"DEINE ERINNERUNGEN (koennen alte ungenaue Antworten enthalten - Grundwahrheit gewinnt):\n{mem_ctx}\n\n"
        f"LETZTER VERLAUF:\n{hist_ctx}\n\n"
        f"DIMA FRAGT: {prompt}"
    )
    try:
        return jack_gemini_bridge.ask_gemini(context)
    except Exception:
        return talk_to_ollama(prompt, [])

if __name__ == '__main__':
    if len(sys.argv) < 2: run_voice_loop()
    else:
        u = sys.argv[1]
        r = talk_to_gemini(u)
        print(r)
        auto_save_to_memory(u, r)
