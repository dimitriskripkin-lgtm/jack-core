from kortex_memory import add_memory, search_memory, get_recent
#!/usr/bin/env python3
import os, sys, json, time, urllib.request, urllib.parse, subprocess
from datetime import datetime

sys.path.append('/data/data/com.termux/files/home/jack')
import jack_claude
import jack_gemini_bridge, jack_config, jack_talk, jack_write, jack_coder, jack_sensors, jack_improve, jack_log, jack_budget, jack_skills, jack_agent
from jack_voice_processor import process_voice_message

ERRORS_DB = jack_config.get_param('STORAGE', 'db_path')
PENDING_WRITE = {}
LAST_CODE = {'file': None}
BESTAETIGUNG = 'bestaetige schreiben'
PENDING_IMPROVE = {}
BESTAETIGUNG_PATCH = 'bestaetige patch'

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

def send_keyboard(text, buttons):
    """Sendet Nachricht mit Inline-Keyboard. buttons = [[('Label','data'),...],...]"""
    keyboard = {"inline_keyboard": [
        [{"text": b[0], "callback_data": b[1]} for b in row]
        for row in buttons
    ]}
    data = json.dumps({
        "chat_id": CHAT_ID,
        "text": text,
        "reply_markup": keyboard
    }).encode()
    try:
        req = urllib.request.Request(API + "/sendMessage", data=data,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as _e:
        import jack_log; jack_log.log_decision("KEYBOARD-FEHLER", str(_e)[:100])

def answer_callback(callback_id, text="OK"):
    """Bestaetigt Callback-Query damit Telegram Ladeanimation entfernt."""
    data = json.dumps({"callback_query_id": callback_id, "text": text}).encode()
    try:
        req = urllib.request.Request(API + "/answerCallbackQuery", data=data,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

def handle_callback(callback_data, callback_id):
    """Verarbeitet Inline-Button-Klicks."""
    answer_callback(callback_id)
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
                capture_output=True, text=True, timeout=30)
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
        mem_str = "\n".join([f'  [{r["category"]}] {r["content"][:50]}' for r in mem])
        lines = open(os.path.expanduser("~/jack/jack_decisions.log")).readlines()
        letzter = lines[-1].strip() if lines else "-"
        return f"Status 7/7 Dienste ok | Fehler offen: {n}\nLetzte Aktion: {letzter[:80]}\nGedaechtnis:\n{mem_str}"
    if callback_data.startswith("suche:"):
        q = callback_data.split(":",1)[1]
        from kortex_memory import search_memory
        results = search_memory(q, limit=3)
        if not results or isinstance(results, dict):
            return f"Nichts gefunden fuer: {q}"
        return "\n".join([f'[{r["category"]}] {r["content"][:80]}' for r in results])
    return f"Unbekannter Button: {callback_data}"

def get_updates(offset=0):
    url = f"{API}/getUpdates?timeout=30&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=35) as res:
            return json.loads(res.read())['result']
    except: return []

def handle(text):
    if text.strip() == "/audit":
        import jack_audit; return jack_audit.report()
    global PENDING_WRITE, PENDING_IMPROVE
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

    if text.strip() in ('/akku','/sensor'):
        return jack_sensors.get_battery() + " | " + jack_sensors.get_motion()

    if text.strip() == '/standort':
        d = jack_sensors.get_location()
        if 'error' in d: return "Standort: " + str(d['error'])
        return f"Standort: {d.get('latitude')}, {d.get('longitude')} (+-{d.get('accuracy')}m)"

    if text.strip() == '/sehen' or text.startswith('/sehen '):
        frage = raw[7:].strip() or "Was siehst du? Kurz auf Deutsch."
        return "JACK schaut durch die Kamera...\n\n" + jack_sensors.see(frage)

    if text.strip() == BESTAETIGUNG_PATCH:
        global PENDING_IMPROVE
        if not PENDING_IMPROVE:
            return "Kein Verbesserungs-Vorschlag offen."
        ok, msg = jack_improve.apply_improvement(PENDING_IMPROVE.get('module'), PENDING_IMPROVE.get('answer'))
        PENDING_IMPROVE = {}
        return msg

    if text.startswith('/cc '):
        frage = raw[4:].strip()
        if not frage:
            return "Nutzung: /cc <Frage an Claude Code>"
        import threading
        def _run(f):
            try:
                ans = jack_claude.ask_claude(f)
                send("Claude Code:\n\n" + ans[:3500])
            except Exception as e:
                send(f"Claude-Fehler: {e}")
        threading.Thread(target=_run, args=(frage,), daemon=True).start()
        return "Claude Code arbeitet dran (bis zu 2 Min), ich melde mich mit der Antwort."

    if text.startswith('/auto '):
        ziel = raw[6:].strip()
        if not ziel:
            return "Nutzung: /auto <ziel>"
        import threading
        def _run(z):
            try:
                ok, msg = jack_agent.autonomous_task(z)
                send(("AGENT FERTIG: " if ok else "AGENT (nicht geschafft): ") + msg)
            except Exception as e:
                send(f"Agent-Fehler: {e}")
        threading.Thread(target=_run, args=(ziel,), daemon=True).start()
        return "Alles klar, ich arbeite selbststaendig dran (max 4 Runden, nur Werkstatt) und melde mich, wenn ich fertig bin."

    if text.strip() == '/skills':
        return jack_skills.list_skills()

    if text.startswith('/skill save '):
        nm = raw[12:].strip()
        ok, msg = jack_skills.save_skill(nm, LAST_CODE.get('file'))
        return msg

    if text.startswith('/skill '):
        nm = raw[7:].strip()
        ok, out = jack_skills.run_skill(nm)
        return ("OK" if ok else "FEHLER") + f" [{nm}]\n\n{out}"

    if text.strip() == '/budget':
        return jack_budget.status()

    if text.strip() == '/log':
        return 'JACKs Logbuch:\n' + jack_log.recent(15)

    if text.startswith('/verbessere '):
        mod = raw[12:].strip()
        ans, name = jack_improve.propose_improvement(mod)
        if not ans:
            return name
        PENDING_IMPROVE.clear(); PENDING_IMPROVE.update({'module': name, 'answer': ans})
        prev = ans if len(ans) < 1200 else ans[:1200] + "\n... (gekuerzt)"
        return (f"Verbesserungs-Vorschlag fuer {name}:\n\n{prev}\n\n"
                f"Zum Anwenden antworte exakt: {BESTAETIGUNG_PATCH}\n(rollt automatisch zurueck wenn es bricht)\nOder: abbrechen")

    if text.startswith('/code '):
        aufgabe = raw[6:].strip()
        if not aufgabe:
            return "Nutzung: /code <was soll das Programm tun>"
        fn, code, msg = jack_coder.write_code(aufgabe)
        LAST_CODE['file'] = fn
        if not fn:
            return f"Fehler: {msg}"
        vorschau = code if len(code) < 1200 else code[:1200] + "\n... (gekuerzt)"
        return (f"Code geschrieben: {fn} (in ~/jack_werkstatt)\n\n{vorschau}\n\n"
                f"Zum Testen: /run {fn}")

    if text.strip() == '/run' or text.startswith('/run '):
        fn = raw[5:].strip() if len(raw) > 4 else ""
        if not fn:
            fn = LAST_CODE.get('file')
        if not fn:
            return "Noch kein Code da. Erst /code <aufgabe>."
        ok, out = jack_coder.run_code(fn)
        status = "OK" if ok else "BLOCKIERT/FEHLER"
        return f"[{status}] {fn}\n\n{out}"

    if text.strip() == '/werkstatt':
        import os as _os
        d = _os.path.expanduser("~/jack_werkstatt")
        files = sorted(_os.listdir(d)) if _os.path.isdir(d) else []
        return "Werkstatt-Inhalt:\n" + ("\n".join(files) if files else "(leer)")

    if raw.strip() == "/status_report":
        import subprocess
        result = subprocess.run(
            ["bash", "/data/data/com.termux/files/home/jack/jack_status_report.sh"],
            capture_output=True, text=True, timeout=15
        )
        return result.stdout[:3000] if result.stdout else "Fehler beim Status-Report."
    if raw.startswith("/approve_fix_"):
        fix_id = raw.strip()[1:]
        try:
            import json, subprocess
            fixes = json.load(open(os.path.expanduser("~/jack/jack_fixes.json")))
            fix = fixes.get(fix_id.replace("approve_","",1))
            if not fix:
                return f"Fix nicht gefunden: {fix_id}"
            pfad = fix.get("pfad","")
            if not os.path.exists(pfad):
                return f"Fix-Datei fehlt: {pfad}"
            r = subprocess.run(["python3", pfad],
                capture_output=True, text=True, timeout=30)
            output = (r.stdout + r.stderr).strip()[:500]
            import jack_log
            jack_log.log_decision("APPROVE-FIX", f"{fix_id}: {output[:80]}")
            return f"Fix ausgefuehrt:\n{output}"
        except Exception as _e:
            return f"Fehler bei Fix-Ausfuehrung: {str(_e)[:200]}"
    if raw.strip() == "/test_button":
        send_keyboard(
            "JACK Schnellzugriff:",
            [[("📊 Status", "status:now"), ("🔍 JACK suchen", "suche:JACK")],
             [("🧠 Gedaechtnis", "suche:kortex"), ("⚙️ Waechterstatus", "status:waechter")]]
        )
        return None
    if raw.startswith("/merke "):
        inhalt = raw[7:].strip()
        cat, tags = "general", ""
        worte = inhalt.split()
        for w in worte:
            if w.startswith("#"):
                cat = w[1:]; tags = w[1:]
                inhalt = inhalt.replace(w, "").strip()
        r = add_memory(inhalt, category=cat, source="telegram", tags=tags)
        return f"Gespeichert (ID {r['id']}): {inhalt[:80]}"
    if raw.startswith("/suche "):
        q = raw[7:].strip()
        results = search_memory(q, limit=5)
        if not results or isinstance(results, dict):
            return f"Nichts gefunden fuer: {q}"
        lines = [f"Suche '{q}':"]
        for r in results:
            lines.append(f"[{r['category']}] {r['content'][:100]}")
        return "\n".join(lines)
    if text.strip() == "/gedaechtnis":
        recent = get_recent(limit=5)
        if not recent:
            return "Gedaechtnis ist leer."
        lines = ["Letzte 5 Eintraege:"]
        for r in recent:
            lines.append(f"[{r['category']}] {r['content'][:80]}")
        return "\n".join(lines)
    if text in ['/start', 'hi', 'hallo']:
        return "JACK online. Befehle: /status /errors /code <aufgabe> /run <datei> oder einfach fragen (Text+Sprache)."
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
            cb = u.get('callback_query', {})
            if cb:
                cb_chat = str(cb.get('message', {}).get('chat', {}).get('id', ''))
                if cb_chat == CHAT_ID:
                    cb_reply = handle_callback(cb.get('data', ''), cb.get('id', ''))
                    if cb_reply:
                        send(cb_reply)
                continue
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

            # Callback-Query (Inline-Button-Klick)
            cb = u.get('callback_query', {})
            if cb:
                cb_data = cb.get('data', '')
                cb_id = cb.get('id', '')
                cb_reply = handle_callback(cb_data, cb_id)
                send(cb_reply)
                continue

            text = msg.get('text', '')
            if not text: continue
            print(f"[TG] {text}")
            try:
                reply = handle(text)
            except Exception as e:
                reply = f"Fehler beim Verarbeiten: {e}"
            if reply is not None:
                send(reply)
        time.sleep(1)

if __name__ == "__main__":
    main()
