import sys
import json
import urllib.request
import sqlite3
import secrets
import datetime
import shutil
import os
import jack_math
import jack_vecdb

MODEL_NAME = 'llama3'
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
    system_prompt = 'Du bist JACK, ein autarkes KI-System auf Android. Antworte kurz, direkt und auf Augenhoehe.'
    
    if context_memories:
        system_prompt += '\n\nRelevanter Kontext aus deinen Erinnerungen:\n'
        for mem in context_memories:
            system_prompt += f'- Befehl: {mem[1]} | Ergebnis: {mem[2]}\n'
            
    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': prompt}
    ]
    
    data = json.dumps({'model': MODEL_NAME, 'messages': messages, 'stream': False}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode('utf-8'))['message']['content']
    except Exception as e:
        return f'Ollama API Fehler: {e}'

def auto_save_to_memory(cmd, result, vec):
    hex_id = secrets.token_hex(8)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        shutil.copyfile(DB_PATH, DB_PATH + '.bak')
    except:
        pass
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute('INSERT INTO memory (id, cmd, result, timestamp) VALUES (?, ?, ?, ?);', (hex_id, cmd, result, timestamp))
        row_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        if vec:
            jack_vecdb.store_embedding(row_id, vec)
    except Exception as e:
        try:
            with open('/data/data/com.termux/files/home/jack/jack_errors.log', 'a') as f:
                f.write(f'[{timestamp}] Speicherfehler: {str(e)}\n')
        except:
            pass

def main():
    if len(sys.argv) < 2:
        print('Fehler: Kein Argument uebergeben.')
        sys.exit(1)
        
    first_arg = sys.argv[1]
    
    # Feature 1: Historie anzeigen (-h oder --history)
    if first_arg in ['--history', '-h']:
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute('SELECT timestamp, cmd, result FROM memory ORDER BY rowid DESC LIMIT 5;')
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                print('Keine Eintraege in der Historie.')
            else:
                print('=== JACK HISTORIE (Letzte 5 Interaktionen) ===')
                for row in reversed(rows):
                    print(f'[{row[0]}]')
                    print(f' -> CMD: {row[1]}')
                    print(f' -> RES: {row[2]}')
                    print('-' * 45)
        except Exception as e:
            print(f'Fehler beim Lesen der Historie: {e}')
        sys.exit(0)
        
    # Feature 2: Dashboard / System-Stats (-s oder --stats) -> FIX: Nutzt jetzt die Vektor-Pointer-Routine
    if first_arg in ['--stats', '-s']:
        try:
            conn = jack_vecdb.get_ptr(DB_PATH)
            total_mem = conn.execute('SELECT COUNT(*) FROM memory;').fetchone()[0]
            total_vec = conn.execute('SELECT COUNT(*) FROM memory_vec;').fetchone()[0]
            conn.close()
            
            db_size = os.path.getsize(DB_PATH) / 1024 / 1024 if os.path.exists(DB_PATH) else 0
            bak_path = DB_PATH + '.bak'
            bak_exists = os.path.exists(bak_path)
            bak_size = os.path.getsize(bak_path) / 1024 / 1024 if bak_exists else 0
            
            print('=== JACK SYSTEM-DASHBOARD ===')
            print(f'Erinnerungen (Text)    : {total_mem}')
            print(f'Vektoren indiziert     : {total_vec}')
            print(f'Datenbank-Groesse      : {db_size:.2f} MB')
            print(f'Backup-Integritaet     : {"VALID" if bak_exists and abs(db_size - bak_size) < 0.01 else "WARNUNG / REPAIR NEEDED"}')
            print(f'Backup-Datei           : {"BEREIT" if bak_exists else "FEHLT"} ({bak_size:.2f} MB)')
        except Exception as e:
            print(f'Fehler beim Generieren der Statistiken: {e}')
        sys.exit(0)
        
    # Feature 3: Datei einlesen (-r oder --read)
    file_content = ""
    file_path = ""
    if first_arg in ['--read', '-r']:
        if len(sys.argv) < 4:
            print('Fehler: Syntax ist jack --read <datei> "<prompt>"')
            sys.exit(1)
        file_path = sys.argv[2]
        user_input = sys.argv[3]
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
        except Exception as e:
            print(f'Fehler beim Lesen der Datei: {e}')
            sys.exit(1)
    else:
        user_input = first_arg
        
    math_res = jack_math.try_direct_calculation(user_input)
    if math_res is not None:
        print(f'[Mathe-Gate] Ergebnis: {math_res}')
        sys.exit(0)
        
    vec = get_embedding(user_input)
    memories = []
    if vec:
        memories = jack_vecdb.search_similar(vec, limit=2)
        
    if file_content:
        ollama_prompt = f'Kontext aus Datei ({file_path}):\n"""\n{file_content}\n"""\n\nAnweisung: {user_input}'
    else:
        ollama_prompt = user_input
        
    response = talk_to_ollama(ollama_prompt, memories)
    print(response)
    
    auto_save_to_memory(user_input, response, vec)

if __name__ == '__main__':
    main()

def compress_context(file_content, file_ext):
    lines = file_content.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped: continue
        if file_ext in ['.py', '.sh'] and stripped.startswith('#'): continue
        if file_ext in ['.log', '.txt'] and ("keep-alive" in stripped.lower() or "ping-pong" in stripped.lower()): continue
        cleaned_lines.append(line)
    if len(cleaned_lines) > 100 and file_ext == '.log':
        cleaned_lines = ["... [Ältere Log-Einträge gekürzt] ..."] + cleaned_lines[-100:]
    return '\n'.join(cleaned_lines)
