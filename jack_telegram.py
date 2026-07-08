#!/usr/bin/env python3
import os, sys, json, time, urllib.request, urllib.parse, subprocess
from datetime import datetime

sys.path.append('/data/data/com.termux/files/home/jack')
import jack_gemini_bridge, jack_config

ERRORS_DB = jack_config.get_param('STORAGE', 'db_path')

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

def get_updates(offset=0):
    url = f"{API}/getUpdates?timeout=30&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=35) as res:
            return json.loads(res.read())['result']
    except: return []

def handle(text):
    text = text.strip().lower()
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
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        out = (result.stdout + result.stderr).strip()
        return f"$ {cmd}\n{out[:500]}" if out else f"$ {cmd}\n(kein Output)"
    elif text.startswith('frag gemini'):
        question = text[11:].strip() or "System-Status analysieren."
        status = jack_gemini_bridge.collect_status()
        return jack_gemini_bridge.ask_gemini(question, status)[:1000]
    else:
        status = jack_gemini_bridge.collect_status()
        return jack_gemini_bridge.ask_gemini(text, status)[:1000]

def main():
    send("JACK Telegram-Bridge online.")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] JACK Telegram läuft...")
    offset = 0
    while True:
        updates = get_updates(offset)
        for u in updates:
            offset = u['update_id'] + 1
            msg = u.get('message', {})
            if str(msg.get('chat', {}).get('id', '')) != CHAT_ID: continue
            text = msg.get('text', '')
            if not text: continue
            print(f"[TG] {text}")
            reply = handle(text)
            send(reply)
        time.sleep(1)

if __name__ == "__main__":
    main()
