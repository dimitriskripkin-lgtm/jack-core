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
        f"Antworte nur mit Kern-Daten (Honor 8, Android, Termux, Speicherstatus). Keine fiktive Hardware. "
        f"Antworte bei Voice-Ausgabe in maximal zwei Sätzen."
        f"Datum/Zeit: {current_time}."
    )
    
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
        conn.execute('INSERT INTO memory (id, cmd, result, timestamp) VALUES (?, ?, ?, ?);', (hex_id, cmd, result, timestamp))
        conn.commit()
        conn.close()
        combined = f"Frage: {cmd} | Antwort: {result}"
        vec = get_embedding(combined)
        if vec: jack_vecdb.store_embedding(hex_id, vec)
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
            
            math_res = jack_math.try_direct_calculation(user_input)
            if math_res is not None:
                print(f'JACK: {math_res}')
                jack_voice_el.speak(str(math_res))
                auto_save_to_memory(user_input, str(math_res))
                continue
                
            response = talk_to_ollama(user_input, [])
            print(f'JACK: {response}')
            
            # Truncate for TTS to prevent timeout
            speak_text = response if len(response) < 400 else (response[:397] + "...")
            jack_voice_el.speak(speak_text)
            
            auto_save_to_memory(user_input, response)
        except KeyboardInterrupt: break

if __name__ == '__main__':
    if len(sys.argv) < 2: run_voice_loop()
    else:
        u = sys.argv[1]
        r = talk_to_ollama(u, [])
        print(r)
        auto_save_to_memory(u, r)
