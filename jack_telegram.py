#!/usr/bin/env python3
import os, sys, json, time, urllib.request, urllib.parse, subprocess
_PERSONA_PATH=os.path.expanduser("~/jack/jack_persona.md")
try:
    _PERSONA=open(_PERSONA_PATH,encoding="utf-8").read().strip()
except Exception:
    _PERSONA="Du bist JACK, Dimas KI-System. Kumpel-Ton, Deutsch, direkt."
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
from datetime import datetime
import threading
try:
    from jack_live_bridge import JACKLiveVoiceBridge as _JLVB; live_bridge=_JLVB()
except ImportError:
    live_bridge=None

def build_write_keyboard(filename):
    return {"inline_keyboard":[[{"text":"🟢 Bestätigen","callback_data":f"confirm_write:{filename}"},{"text":"🔴 Abbrechen","callback_data":f"cancel_write:{filename}"}]]}

sys.path.append(os.path.expanduser('~/jack'))
import jack_claude
import jack_gemini_bridge, jack_config, jack_talk, jack_write, jack_coder, jack_sensors, jack_improve, jack_log, jack_budget, jack_skills, jack_agent
from jack_voice_processor import process_voice_message
try:
    from kortex_memory import add_memory, search_memory, get_recent
except Exception as _ke:
    def add_memory(*a,**k): pass
    def search_memory(*a,**k): return []
    def get_recent(*a,**k): return []

ERRORS_DB = jack_config.get_param('STORAGE', 'db_path')
PENDING_WRITE = {}
LAST_CODE = {'file': None}
BESTAETIGUNG = 'bestaetige schreiben'
PENDING_IMPROVE = {}
BESTAETIGUNG_PATCH = 'bestaetige patch'

FAST_CMDS = {'/selftest','/akku','/sensor','/standort','/status','/budget','/log','/werkstatt','/start','/help','/missionen','/errors','/befehle','/oracle_result','/menu','/m','/trace','/level','/kette','/baum'}

def load_secrets():
    token, chat_id = None, None
    with open(os.path.expanduser('~/.jack_secrets')) as f:
        for line in f:
            if 'TELEGRAM_BOT_TOKEN' in line: token = line.split('"')[1]
            if 'TELEGRAM_CHAT_ID' in line: chat_id = line.split('"')[1]
    return token, chat_id


MENU = {
    "status": {
        "label": "🔴 System & Status",
        "befehle": [
            ("/selftest", "Prueft ob alle 5 Kern-Checks OK sind", "/selftest"),
            ("/trace", "Zeigt was JACK gerade tut - Threads, RAM, letzte Aktionen", "/trace"),
            ("/scan", "Vollstaendiger System-Scan mit allen Sensoren", "/scan"),
            ("/level", "Zeigt oder setzt wie autonom JACK handeln darf (1-4)", "/level 2"),
        ]
    },
    "diagnose": {
        "label": "🔧 Diagnose & Fehler",
        "befehle": [
            ("/tb", "Analysiert einen Python-Fehler und gibt Loesungshinweis", "/tb NameError: name x is not defined"),
            ("/errors", "Zeigt alle offenen Fehler im System", "/errors"),
            ("/log", "Die letzten 15 Aktionen die JACK gemacht hat", "/log"),
            ("/budget", "Wie viele API-Calls wurden heute verbraucht", "/budget"),
            ("/audit", "Vollstaendiger System-Bericht", "/audit"),
        ]
    },
    "autonomie": {
        "label": "🤖 Autonomie & Aufgaben",
        "befehle": [
            ("/kette", "Zeigt alle verfuegbaren Aktionsketten", "/kette"),
            ("/kette system_vollcheck", "Prueft alles durch: Dienste, RAM, Temp, Akku, SSH", "/kette system_vollcheck"),
            ("/kette xiaomi_reparieren", "Xiaomi pruefen, bei Problem WiFi neustarten", "/kette xiaomi_reparieren"),
            ("/mission", "Gibt JACK eine Aufgabe die er selbst ausfuehrt", "/mission pruefe ob alle logs sauber sind"),
            ("/missionen", "Zeigt alle laufenden und abgeschlossenen Aufgaben", "/missionen"),
            ("/auto", "JACK arbeitet selbstaendig an einem Ziel (max 4 Runden)", "/auto optimiere jack_selftest.py"),
            ("/bugfix", "JACK sucht Bugs und repariert sie autonom mit Freigabe-Button", "/bugfix"),
        ]
    },
    "gedaechtnis": {
        "label": "🧠 Gedaechtnis & Lernen",
        "befehle": [
            ("/baum", "Zeigt die letzte Gespraeches-Kette (was fuehrte wozu)", "/baum"),
            ("/baum stat", "Statistik: wie viele Erinnerungen sind vernetzt", "/baum stat"),
            ("/baum reset", "Startet eine neue Gedaechtnis-Kette", "/baum reset"),
            ("merke dir", "JACK merkt sich eine wichtige Information dauerhaft", "merke dir ich mag keine langen Antworten"),
        ]
    },
    "werkzeug": {
        "label": "🛠️ Code & Werkzeug",
        "befehle": [
            ("/code", "JACK schreibt ein Python-Script fuer dich", "/code schreibe ein script das den akku anzeigt"),
            ("/run", "Fuehrt das zuletzt geschriebene Script aus", "/run"),
            ("/werkstatt", "Zeigt alle Scripts die JACK geschrieben hat", "/werkstatt"),
            ("/cc", "Fragt Claude Code direkt an (fuer komplexe Fragen)", "/cc was ist eine rekursive funktion"),
            ("/verbessere", "JACK analysiert ein Modul und schlaegt Verbesserungen vor", "/verbessere jack_memory"),
        ]
    },
    "hardware": {
        "label": "📡 Sensoren & Hardware",
        "befehle": [
            ("/akku", "Akkustand, Ladestand und Temperatur", "/akku"),
            ("/sensor", "Bewegungssensor und weitere Hardware-Daten", "/sensor"),
            ("/standort", "Aktueller GPS-Standort", "/standort"),
            ("/sehen", "JACK macht ein Foto und beschreibt was er sieht", "/sehen was liegt auf dem Tisch"),
            ("Foto schicken", "Foto an JACK schicken - er analysiert Fehler oder Inhalt auf Deutsch", "(einfach Foto schicken, optional Caption: was ist hier das Problem)"),
        ]
    },
    "skills": {
        "label": "⚙️ Skills & Oracle",
        "befehle": [
            ("/befehle", "Oracle-Buttons: Dienste, RAM, Fehler, Budget, Modelle sofort abrufen", "/befehle"),
            ("/db_skills", "Alle gespeicherten Faehigkeiten die JACK gelernt hat", "/db_skills"),
            ("/skill_builder", "JACK analysiert sich selbst und baut neue Faehigkeiten", "/skill_builder"),
            ("/db_trace", "Zeigt den Ausfuehrungs-Verlauf eines Skills", "/db_trace akku_status"),
        ]
    },
}

def menu_hauptseite():
    """Sendet Hauptmenue mit Kategorie-Buttons."""
    buttons = [[(_v["label"], "menu:"+_k)] for _k, _v in MENU.items()]
    return buttons

def menu_kategorie(key):
    """Text fuer eine Kategorie."""
    if key not in MENU: return "Unbekannte Kategorie"
    kat = MENU[key]
    zeilen = [kat["label"], ""]
    for befehl, beschreibung, beispiel in kat["befehle"]:
        zeilen.append(f"• {befehl}")
        zeilen.append(f"  {beschreibung}")
        zeilen.append(f"  Beispiel: {beispiel}")
        zeilen.append("")
    zeilen.append("← /menu fuer Hauptmenue")
    return chr(10).join(zeilen)

TOKEN, CHAT_ID = load_secrets()
API = f"https://api.telegram.org/bot{TOKEN}"

def send(text):
    text = str(text)
    if len(text) <= 3800:
        _send_raw(text)
        return
    teile = [text[i:i+3800] for i in range(0, len(text), 3800)]
    for teil in teile:
        _send_raw(teil)
def _send_raw(text):
    url = f"{API}/sendMessage"
    data = json.dumps({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        body = ""
        try: body = e.read().decode()[:200]
        except Exception: pass
        try:
            import jack_log; jack_log.log_decision("TG-SEND-FEHLER", f"{e} | {body} | text={str(text)[:60]}")
        except Exception: pass
        print(f"Send-Fehler: {e} | {body}")

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

def vibrate(ms=80):
    """Kurze Haptik-Rueckmeldung."""
    try:
        import subprocess as _vs
        _vs.run(['termux-vibrate','-d',str(ms)],capture_output=True,timeout=2)
    except Exception: pass

def send_webapp(text, url, button_text="Ergebnisse anzeigen"):
    import json as _j
    keyboard = {"inline_keyboard": [[{"text": button_text, "url": url}]]}
    data = _j.dumps({"chat_id": CHAT_ID, "text": text, "reply_markup": keyboard}).encode()
    try:
        req = urllib.request.Request(API + "/sendMessage", data=data,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as _e:
        import jack_log; jack_log.log_decision("WEBAPP-FEHLER", str(_e)[:100])

def answer_callback(callback_id, text="OK"):
    """Bestaetigt Callback-Query damit Telegram Ladeanimation entfernt."""
    data = json.dumps({"callback_query_id": callback_id, "text": text}).encode()
    try:
        req = urllib.request.Request(API + "/answerCallbackQuery", data=data,
            headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5)
    except Exception as _le:
        _jlog and _jlog.fehler("telegram","unbenannt",_le)

def _check_memory_trigger(text, chat_id):
    triggers=["merk dir","vergiss nicht","ich hab jetzt","ich bin jetzt","ab sofort","wichtig:","ich wohne","ich arbeite"]
    if any(t in text.lower() for t in triggers):
        kb={"inline_keyboard":[[
            {"text":"Ja, speichern","callback_data":"mem_save:"+text[:200]},
            {"text":"Nein","callback_data":"mem_skip"}
        ]]}
        send_keyboard("Soll ich das speichern? "+text[:150], kb["inline_keyboard"])
        return True
    return False

def handle_callback(callback_data, callback_id):
    """Verarbeitet Inline-Button-Klicks."""
    if callback_data.startswith("confirm_write:"):
        fn=callback_data[14:]
        if PENDING_WRITE and PENDING_WRITE.get("filename")==fn:
            try:
                ok,msg=jack_write.commit_write(PENDING_WRITE["filename"],PENDING_WRITE["content"])
                PENDING_WRITE.clear()
                answer_callback(callback_id,"Gespeichert" if ok else "Fehler")
                send("✅ "+msg if ok else "❌ "+msg)
            except Exception as e:
                answer_callback(callback_id,"Fehler")
                send("Fehler beim Schreiben: "+str(e)[:100])
        else:
            answer_callback(callback_id,"Kein Vorschlag offen")
        return
    if callback_data.startswith("cancel_write:"):
        PENDING_WRITE.clear()
        answer_callback(callback_id,"Abgebrochen")
        send("❌ Abgebrochen.")
        return
    if callback_data.startswith("mem_save:"):
        fact=callback_data[9:]
        try:
            import jack_memory as _jm; _jm.save(fact,"Dima erwaehnte",intent="dima_fact")
            answer_callback(callback_id,"Gespeichert")
        except Exception as e:
            answer_callback(callback_id,"Fehler: "+str(e)[:50])
        return
    if callback_data=="mem_skip":
        answer_callback(callback_id,"Ok")
        return
    # Kategorie-Menu - sofort pruefen
    if callback_data.startswith("menu:"):
        key = callback_data[5:]
        antwort = menu_kategorie(key)
        answer_callback(callback_id, "Oeffne " + key + "...")
        return antwort
    # Zurueck zum Hauptmenu
    if callback_data == "menu:hauptmenu":
        answer_callback(callback_id, "Hauptmenu")
        send_keyboard("JACK Befehlszentrale:", menu_hauptseite())
        return None
    # Gedanken-Popup: was macht JACK gerade
    try:
        import datetime as _dt
        _lines = open(os.path.expanduser("~/jack/jack_decisions.log")).readlines()
        _last = _lines[-1].split("|")[-1].strip()[:30] if _lines else "..."
        answer_callback(callback_id, _last)
    except Exception:
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
    return f"Unbekannter Button: {callback_data}"

def get_updates(offset=0):
    url = f"{API}/getUpdates?timeout=0&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=5) as res:
            return json.loads(res.read())['result']
    except: return []

def oracle_sign(cmd, uuid, ts):
    try:
        sec = open(os.path.expanduser("~/.jack_secrets")).read()
        secret = [l.split("=",1)[1].strip().strip('"') for l in sec.split(chr(10)) if "ORACLE_SECRET=" in l][0]
        msg = f"{uuid}:{cmd}:{ts}".encode()
        import hmac as _h, hashlib as _hs
        return _h.new(secret.encode(), msg, _hs.sha256).hexdigest()
    except: return ""

def handle(text):
    if not text:
        return None
    if text.strip() == '/befehle':
        send_keyboard("JACK Befehle:", [
            [("Status","intent:dienste_check"),("RAM","intent:ram_check")],
            [("Temperatur","intent:temp_check"),("Honor Akku","intent:akku_check")],
            [("Xiaomi Akku","intent:xiaomi_akku"),("Xiaomi SSH","intent:ssh_check")],
            [("Fehler","intent:fehler_check"),("Ollama","intent:ollama_check")],
            [("Proaktiv","intent:proaktiv_check"),("SSH Xiaomi","intent:ssh_check")],
            [("Xiaomi Wecken","intent:xiaomi_wake"),("Selftest","oracle:dienste")]
        ])
        return None
    if text.strip() in ['/menu', '/m']:
        send_keyboard("JACK Befehlszentrale:", menu_hauptseite())
        return None

    # 1. Autonomer Xiaomi Inspector Trigger
    if any(k in text.lower() for k in ['xiaomi', 'slave']) and any(k in text.lower() for k in ['check', 'prüf', 'umgebung', 'status', 'inspekt', 'prozess']):
        try:
            import jack_xiaomi_inspector
            send('📱 *Verbinde mit Xiaomi Slave via SSH...*')
            ok, sys_data = jack_xiaomi_inspector.inspect_xiaomi_system()
            if ok:
                return f"[ECHTER XIAOMI SYSTEM-INSPECT OUTPUT]:\n" + sys_data + f"\n\n[ANWEISUNG]:\nAnalysiere diese echten Systemdaten präzise und technisch. Nenne konkrete Zahlen (RAM, Load, Prozesse, Speicher)."
            else:
                send(f'⚠️ *Xiaomi SSH Fehler:* {sys_data}\nVerarbeite Anfrage ohne Live-Daten.')
        except Exception as e:
            send(f'⚠️ *Inspector Fehler:* {e}')

    # 2. Smart Web-Ingest Trigger (ignoriert localhost / internal URLs)
    import re
    url_match = re.search(r'https?://[^\s]+', text)
    if url_match:
        url = url_match.group(0)
        if 'localhost' not in url and '127.0.0.1' not in url:
            user_prompt = text.replace(url, '').strip()
            try:
                import jack_web_ingest
                send(f'🌐 *Lade Web-Inhalt...*\n`{url}`')
                success, clean_text, added, skipped, err = jack_web_ingest.fetch_and_process_url(url)
                if success:
                    if not user_prompt:
                        return f'✅ *Web-Ingest erfolgreich!*\n📊 {added} Chunks gelernt, {skipped} Duplikate verworfen.'
                    else:
                        text = f'[WEB-INHALT VON {url}]:\n' + clean_text[:4000] + f'\n\n[ANWEISUNG DES BENUTZERS]:\n{user_prompt}'
                else:
                    send(f'⚠️ *Web-Fetch Warnung:* {err}\nVerarbeite Frage ohne Seiteninhalt.')
            except Exception as e:
                send(f'⚠️ *Web-Fehler:* {e}')

    # Weiter zu jack_talk wenn kein fruehzeitiger Return
    try:
        import jack_talk as _jt
        return _jt.talk_to_gemini(text)
    except Exception as _te:
        return f"Fehler: {_te}"

def _offset_lesen():
    try:
        return int(open(os.path.expanduser('~/.jack_tg_offset')).read().strip())
    except:
        return 0

def _offset_schreiben(wert):
    try:
        open(os.path.expanduser('~/.jack_tg_offset'), 'w').write(str(wert))
    except:
        pass

def main():
    try: send("JACK online. Alle Dienste gestartet.")
    except Exception: pass
    vibrate(200)
    offset = _offset_lesen()
    print('[INFO] Telegram Bot Schleife gestartet, warte auf Nachrichten...')
    while True:
        try:
            updates = get_updates(offset)
            for u in updates:
                offset = u['update_id'] + 1
                _offset_schreiben(offset)
                cb = u.get('callback_query', {})
                if cb:
                    cb_data = cb.get('data', '')
                    cb_id = cb.get('id', '')
                    cb_chat = str(cb.get('message', {}).get('chat', {}).get('id', ''))
                    if cb_chat == str(CHAT_ID):
                        vibrate(60)
                        cb_reply = handle_callback(cb_data, cb_id)
                        if cb_reply:
                            send(cb_reply)
                    continue
                msg = u.get('message', {})
                text = msg.get('text', '')
                chat_id = msg.get('chat', {}).get('id')
                if text and chat_id:
                    vibrate(40)
                    reply = handle(text)
                    if reply:
                        send(reply)
        except Exception as e:
            time.sleep(2)
        time.sleep(1)

if __name__ == '__main__':
    main()
