#!/usr/bin/env python3
import os, sys, json, time, urllib.request, urllib.parse, subprocess
from datetime import datetime

sys.path.append('/data/data/com.termux/files/home/jack')
import jack_gemini_bridge, jack_config, jack_talk, jack_write
from jack_voice_processor import process_voice_message

ERRORS_DB = jack_config.get_param('STORAGE', 'db_path')
PENDING_WRITE = {}
BESTAETIGUNG = 'bestaetige schreiben'

def load_secrets():
    token, chat_id = None, None
    with open(os.path.expanduser('~/.jack_secrets')) as f:
        for line in f:
            if 'TELEGRAM_BOT_TOKEN' in line: token = line.split('"')[1]
            if 'TELEGRAM_CHAT_ID' in line: chat_id = line.split('"')[1]
    return token, chat_id

TOKEN, CHAT_ID = load_secrets()
API = f"https://api.telegram.org/bot{TOKEN}"

def send(text):
    url = f"{API}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Send-Fehler: {e}")

def get_voice(file_id, out_path):
    url = f"{API}/getFile?file_id={file_id}"
    with urllib.request.urlopen(url) as res:
        path = json.loads(res.read())['result']['file_path']
    dl_url = f"https://api.telegram.org/file/bot{TOKEN}/{path}"
    urllib.request.urlretrieve(dl_url, out_path)

def send_voice(file_path):
    subprocess.run([
        "curl", "-s", "-X", "POST",
        f"{API}/sendVoice",
        "-F", f"chat_id={CHAT_ID}",
        "-F", f"voice=@{file_path}"
    ])

def get_updates(offset=0):
    url = f"{API}/getUpdates?timeout=30&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=35) as res:
            return json.loads(res.read())['result']
    except: return []

def handle(text):
    global PENDING_WRITE
    raw = text.strip()
    text = raw.lower()

    # Schritt 2: Bestaetigung eines wartenden Schreibvorschlags
    if text.replace("ä","ae").replace("ü","ue") == BESTAETIGUNG:
        if not PENDING_WRITE:
            return "Kein Schreibvorschlag offen."
        ok, msg = jack_write.commit_write(PENDING_WRITE["filename"], PENDING_WRITE["content"])
        PENDING_WRITE = {}
        return msg

    if text in ("abbrechen", "verwerfen"):
        PENDING_WRITE = {}
        return "Schreibvorschlag verworfen."

    if text in ['/start', 'hi', 'hallo']:
        return "JACK online. Befehle: /status /errors /fix /shell <cmd> oder einfach fragen."
    elif text == '/status':
        s = jack_gemini_bridge.collect_status()
        return f"Cortex: {s['cortex']}\nXiaomi: {'✓' if s['xiaomi_reachable'] else '✗'}\nOffene Fehler: {s['open_errors']}"
    elif text == '/errors':
        import sqlite3
        con = sqlite3.connect(ERRORS_DB)
        rows = con.execute("SELECT id, module, error_msg FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 5").fetchall()
        con.close()
        if not rows: return "Keine offenen Fehler."
        return "\n".join([f"[{r[0]}] {r[1]}: {r[2][:80]}" for r in rows])
    elif text.startswith('/shell '):
        cmd = text[7:]
        return "/shell deaktiviert bis Auth eingebaut (Sicherheit). Naechste Session."
        out = (result.stdout + result.stderr).strip()
        return f"$ {cmd}\n{out[:500]}" if out else f"$ {cmd}\n(kein Output)"
    elif text.startswith('frag gemini'):
        question = text[11:].strip() or "System-Status analysieren."
        status = jack_gemini_bridge.collect_status()
        return jack_gemini_bridge.ask_gemini(question, status)[:1000]
    else:
        req = jack_write.detect_write_request(raw)
        if req:
            PENDING_WRITE.clear()
            PENDING_WRITE.update(req)
            pv = jack_write.propose(req["filename"], req["content"])
            return ("Schreibvorschlag:\nDatei: " + pv["filename"] +
                    "\nOrdner: ~/jack_werkstatt\nInhalt:\n" + pv["preview"] +
                    "\n\nZum Ausfuehren antworte exakt: " + BESTAETIGUNG + "\nOder: abbrechen")
        _r = jack_talk.talk_to_gemini(text)
        jack_talk.auto_save_to_memory(text, _r)
        return _r[:1500]

def main():
    send("JACK Telegram-Bridge online (mit Voice-Support).")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] JACK Telegram läuft...")
    offset = 0
    while True:
        updates = get_updates(offset)
        for u in updates:
            offset = u['update_id'] + 1
            msg = u.get('message', {})
            if str(msg.get('chat', {}).get('id', '')) != CHAT_ID: continue
            
            if 'voice' in msg:
                print("[TG] Eingehende Sprachnachricht erkannt.")
                file_id = msg['voice']['file_id']
                ogg_path = os.path.expanduser(f"~/jack/voice_{file_id}.ogg")
                
                try:
                    get_voice(file_id, ogg_path)
                    resp_wav, heard, answer = process_voice_message(ogg_path)
                    
                    send(f"Verstanden: {heard}\n\nJACK: {answer}")
                    send_voice(resp_wav)
                    
                    for _f in (ogg_path, resp_wav):
                        try:
                            os.remove(_f)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"Fehler bei Voice-Verarbeitung: {e}")
                    send("Fehler bei der Sprachverarbeitung.")
                continue

            text = msg.get('text', '')
            if not text: continue
            print(f"[TG] {text}")
            reply = handle(text)
            send(reply)
        time.sleep(1)

if __name__ == "__main__":
    main()
