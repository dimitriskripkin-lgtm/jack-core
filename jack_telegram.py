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

from jack_keyboards import build_write_keyboard, menu_hauptseite as _kb_menu, menu_kategorie as _kb_kat

sys.path.append(os.path.expanduser('~/jack'))
import jack_claude
import jack_gemini_bridge, jack_config, jack_talk, jack_write, jack_coder, jack_sensors, jack_improve, jack_log, jack_budget, jack_skills, jack_agent

from jack_voice_processor import process_voice_message

def _ui_gate_text(text):
    """UI_GATE_TEXT — gleicher Intent wie Voice/Slash."""
    try:
        import jack_exec
        return jack_exec.handle_ui_intent(text or "")
    except Exception:
        return None

try:
    from kortex_memory import add_memory, search_memory, get_recent
except Exception as _ke:
    def add_memory(*a,**k): pass
    def search_memory(*a,**k): return []
    def get_recent(*a,**k): return []

ERRORS_DB = os.path.expanduser('~/jack/jack_errors.db')  # errors-Tabelle, nicht db_path
PENDING_WRITE = {}
import jack_exec
PENDING_EXEC = {}
LAST_CODE = {'file': None}
BESTAETIGUNG = 'bestaetige schreiben'
PENDING_IMPROVE = {}
BESTAETIGUNG_PATCH = 'bestaetige patch'

FAST_CMDS = {'/selftest','/akku','/sensor','/standort','/status','/budget','/log','/werkstatt','/start','/help','/missionen','/errors','/befehle','/oracle_result','/menu','/m','/trace','/level','/kette','/baum','/lernen','/tap','/forsche','/kill','/stop'}

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
                ("/autolearn_status", "Zeigt Autolearn Loop Status", "/autolearn_status"),
                ("/ingest_status", "Zeigt Auto-Ingest Status", "/ingest_status"),
        ]
    },
    "gedaechtnis": {
        "label": "🧠 Gedaechtnis & Lernen",
        "befehle": [
            ("/lernen", "Autonome Lernrunde auf dem Xiaomi starten", "/lernen"),
            ("/baum", "Zeigt die letzte Gespraeches-Kette (was fuehrte wozu)", "/baum"),
                ("/rag Python", "Suche nach Python", "/rag Python"),
                ("/rag Skill", "Suche nach Skills", "/rag Skill"),
                ("/rag Fehler", "Suche nach Fehlern", "/rag Fehler"),
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

# MENU_EXTRA_ALL_COMMANDS_QWEN
MENU["befehle"] = {
    "label": "🔧 Alle Befehle",
    "befehle": [
        ("/activity","Activity-Log der letzten 24h","/activity"),
        ("/outcomes","Erfolgsquote aller Befehle","/outcomes"),
        ("/menu","Befehlszentrale","/menu"),
        ("/befehle","Schnellbuttons","/befehle"),
        ("/status","Systemstatus","/status"),
        ("/selftest","Kernchecks","/selftest"),
        ("/trace","Threads/RAM/Aktionen","/trace"),
        ("/scan","Vollscan","/scan"),
        ("/level","Autonomie-Level","/level"),
        ("/errors","Offene Fehler","/errors"),
        ("/log","Letzte Aktionen","/log"),
        ("/budget","API-Budget","/budget"),
        ("/audit","Systembericht","/audit"),
        ("/skills","Skills","/skills"),
        ("/baum","Gedächtnisbaum","/baum"),
        ("/lernen","Lernstatus","/lernen"),
        ("/kette","Aktionsketten","/kette"),
        ("/mission","Aufgabe starten","/mission pruefe logs"),
        ("/auto","Autonom arbeiten","/auto optimiere jack"),
        ("/bugfix","Bugfix-Lauf","/bugfix"),
        ("/find","Screen-Element suchen","/find Suchleiste"),
        ("/vision","Screenshot analysieren","/vision was siehst du"),
        ("/harvest","Fakten ernten","/harvest claude 20"),
        ("/harvest_status","Harvest Status","/harvest_status"),
        ("/harvest_lernen","Harvest destillieren","/harvest_lernen"),
        ("/fakten","Gelernte Fakten","/fakten"),
        ("/explore","App erkunden","/explore com.android.settings"),
        ("/explore_deep","Deep Explore","/explore_deep com.miui.gallery"),
        ("/appmap","App-Map anzeigen","/appmap"),
        ("/agent","UI-Agent starten","/agent öffne Einstellungen"),
        ("/ssh","SSH-Agent Xiaomi","/ssh uptime"),
        ("/code","Code schreiben","/code akku script"),
        ("/run","Letzten Code ausführen","/run"),
        ("/werkstatt","Werkstatt anzeigen","/werkstatt"),
        ("/cc","Claude Code fragen","/cc analysiere jack_exec"),
        ("/verbessere","Modul verbessern","/verbessere jack_memory"),
        ("/akku","Akku/Temp","/akku"),
        ("/sensor","Sensoren","/sensor"),
        ("/standort","GPS","/standort"),
        ("/sehen","Kamera sehen","/sehen was liegt da"),
        ("/tap","Screen tippen","/tap Chrome"),
        ("/forsche","Recherchieren","/forsche Ollama"),
        ("/kill","Stop","/kill")
    ]
}
def menu_hauptseite(): return _kb_menu(MENU)


def menu_kategorie(key): return _kb_kat(key, MENU)

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
    if callback_data == 'run_exec':
        c=PENDING_EXEC.get('cmd')
        if not c:
            answer_callback(callback_id,'Nichts offen'); return
        answer_callback(callback_id,'Laeuft...')
        send('Fuehre aus...')
        def _r(cmd=c):
            out=jack_exec.run(cmd)
            PENDING_EXEC.clear()
            send(out)
            if not out.startswith('rc=0') and not out.startswith('BLOCKIERT'):
                try:
                    import jack_react
                    send('Analysiere Fehler...')
                    send('VORSCHLAG:' + chr(10) + str(jack_react.analysiere(cmd, out))[:1500])
                except Exception as _e:
                    send('Analyse-Fehler: ' + str(_e)[:120])
        import threading as _th
        _th.Thread(target=_r, daemon=True).start()
        return
    if callback_data == 'cancel_exec':
        PENDING_EXEC.clear()
        answer_callback(callback_id,'Abgebrochen')
        send('Befehl verworfen.')
        return
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
    if callback_data.startswith("cmd:"):
        _befehl = callback_data[4:]
        answer_callback(callback_id, _befehl[:30])
        import threading as _cth
        def _crun():
            try:
                _r = handle(_befehl)
                if _r: send(str(_r))
            except Exception as _ce:
                send('Button-Fehler: ' + str(_ce)[:150])
        _cth.Thread(target=_crun, daemon=True).start()
        return None
    if callback_data.startswith("menu:") and callback_data != "menu:hauptmenu":
        key = callback_data[5:]
        if key in MENU:
            _kat = MENU[key]
            _btns = []
            for _bef, _desc, _bsp in _kat["befehle"]:
                _payload = ("cmd:" + _bsp)[:62]
                _btns.append([(_bef + " - " + _desc[:28], _payload)])
            _btns.append([("<< Hauptmenue", "menu:hauptmenu")])
            answer_callback(callback_id, _kat["label"])
            send_keyboard(_kat["label"] + " (antippen = ausfuehren):", _btns)
            return None
        answer_callback(callback_id, "Unbekannt")
        return "Unbekannte Kategorie"
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
    if callback_data=="selfsee_go":
        try:
            import signal as _sig; _sig.alarm(0)
        except Exception:
            pass
        answer_callback(callback_id,"Laeuft...")
        def _go():
            try:
                import jack_selfsee as _ss
                send(_ss.deep())
            except Exception as e:
                send("Selfsee-Fehler: "+str(e)[:160])
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

def get_updates(offset=0):
    url = f"{API}/getUpdates?timeout=0&offset={offset}"
    try:
        with urllib.request.urlopen(url, timeout=5) as res:
            return json.loads(res.read())['result']
    except Exception: return []

def oracle_sign(cmd, uuid, ts):
    try:
        sec = open(os.path.expanduser("~/.jack_secrets")).read()
        secret = [l.split("=",1)[1].strip().strip('"') for l in sec.split(chr(10)) if "ORACLE_SECRET=" in l][0]
        msg = f"{uuid}:{cmd}:{ts}".encode()
        import hmac as _h, hashlib as _hs
        return _h.new(secret.encode(), msg, _hs.sha256).hexdigest()
    except Exception: return ""

def handle(text):
    import jack_exec  # FIX-UNBOUND (Qwen 22.08.): Import oben, sonst UnboundLocalError
    if not text:
        return None
    if text.startswith("/find "):
        target = text[6:].strip()
        send(f'🔍 Suche "{target}" auf dem Screen...')
        def _do_find():
            try:
                import jack_vision, jack_grid_vision
                coords, raw = jack_grid_vision.find_element(target, jack_vision.vision_ask, jack_vision.get_screen_b64)
                if coords:
                    send(f'🎯 {target} gefunden bei: x={coords[0]}, y={coords[1]}')
                else:
                    send(f'❌ {target} nicht gefunden.\nRoh-Antwort: {raw}')
            except Exception as e:
                send(f'Fehler bei /find: {e}')
        import threading
        threading.Thread(target=_do_find, daemon=True).start()
        return None
    _pi=text.find('[[PLAN:')
    _pj=text.rfind('[[/PLAN]]')
    if _pi>=0 and _pj>_pi:
        _pname=text[_pi+7:text.find(']]',_pi)]
        _pjson=text[text.find(']]',_pi)+2:_pj].strip()
        def _runplan(pn=_pname,pj=_pjson):
            try:
                import json,importlib,jack_planner,jack_schema
                plan,err=jack_schema.validate(pj)
                if not plan:
                    send('PLAN UNGUELTIG: '+err); return
                importlib.reload(jack_planner)
                plan['name']=pn
                jack_planner.run_plan(plan,send)
            except Exception as e:
                send('Plan-Fehler: '+str(e)[:200])
        import threading as _th
        _th.Thread(target=_runplan,daemon=True).start()
        return None
    _cmd=jack_exec.extrahiere(text)
    if _cmd:
        PENDING_EXEC.clear(); PENDING_EXEC['cmd']=_cmd
        _prev=_cmd if len(_cmd)<800 else _cmd[:800]+' ...'
        send_keyboard('BEFEHL:'+chr(10)+_prev, [[('🟢 Ausführen','run_exec'),('🔴 Abbrechen','cancel_exec')]])
        return None
    _t=text.lower()
    if any(w in _t for w in ['schreib eine datei','erstell eine datei','mach eine datei','schreib datei']):
        import re as _re
        m=_re.search(r'datei\s+(\S+\.\w+)\s+(?:mit\s+inhalt\s+|inhalt\s+)(.*)',text,_re.I)
        if m:
            fn=m.group(1).strip(); ct=m.group(2).strip()
            p=jack_write.propose(fn,ct)
            PENDING_WRITE.clear(); PENDING_WRITE.update(p)
            send_keyboard("Datei: "+p['filename']+chr(10)+"Pfad: ~/jack_werkstatt/"+p['filename']+chr(10)+chr(10)+"Inhalt:"+chr(10)+p['preview'], [[('🟢 Bestätigen','confirm_write:'+p['filename']),('🔴 Abbrechen','cancel_write:'+p['filename'])]])
            return None
        pass
    if text.strip().startswith('/ssh '):
        cmds=[c.strip() for c in text.strip()[5:].split(',') if c.strip()]
        if not cmds: return 'Bitte Befehle angeben: /ssh ls, python3 --version, free -m'
        import jack_ui_agent,threading
        threading.Thread(target=jack_ui_agent.run_ssh_agent,args=(cmds,send),daemon=True).start()
        return 'SSH-Agent gestartet: '+', '.join(cmds)
    if text.strip().startswith('/agent '):
        ziel=text.strip()[7:].strip()
        import jack_ui_agent,threading
        app=None
        if 'termux' in ziel.lower(): app='com.termux'
        elif 'einstellungen' in ziel.lower() or 'settings' in ziel.lower(): app='com.android.settings'
        elif 'chrome' in ziel.lower(): app='com.android.chrome'
        threading.Thread(target=jack_ui_agent.run_agent,args=(ziel,app,20,send),daemon=True).start()
        return 'Agent gestartet: '+ziel
    if text.strip()=='/explore_deep' or text.strip().startswith('/explore_deep '):
        parts=text.strip().split()
        paket=parts[1] if len(parts)>1 else None
        import jack_explorer_deep as _jed, threading
        if paket:
            threading.Thread(target=_jed.explore_deep,args=(paket,8,2,send),daemon=True).start()
            return 'Deep-Explore gestartet: '+paket
        else:
            threading.Thread(target=_jed.run_deep_loop,args=(None,6,send),daemon=True).start()
            return 'Deep-Loop gestartet - erkunde naechste 3 unbekannte Apps...'
    if text.strip()=='/explore' or text.strip().startswith('/explore '):
        n=int(text.strip().split()[-1]) if text.strip()!=('/explore') else 3
        n=min(n,50)
        import jack_explorer, threading
        threading.Thread(target=jack_explorer.run_exploration,args=(n,send),daemon=True).start()
        return 'Starte Xiaomi-Exploration ('+str(n)+' Apps)...'
    if text.strip()=='/appmap':
        try:
            import jack_intent_apps as _jia
            _m = _jia.MAP
            _lines = ['APP-MAP (' + str(len(_m)) + ' Eintraege, live verifiziert):']
            for _k, _v in list(_m.items()):
                _lines.append(_k + ': ' + _v)
            return chr(10).join(_lines)
        except Exception as _e:
            return 'AppMap-Fehler: ' + str(_e)[:100]
    if False:  # alter appmap-block deaktiviert
        import json,os as _os
        f=_os.path.expanduser('~/jack/xiaomi_app_map.json')
        try:
            d=json.load(open(f))
            lines=['APP-MAP ('+str(len(d))+' Apps):']
            for k,v in list(d.items())[:15]:
                lines.append(k.split('.')[-1]+': '+str(v.get('clickable',0))+' Buttons')
            return chr(10).join(lines)
        except Exception: return 'Noch keine App-Map. /explore zuerst.'


    if text.strip() in ("/mission", "/missions"):
        try:
            import subprocess
            r = subprocess.run(
                ["python3", "/data/data/com.termux/files/home/jack/jack_mission_run.py"],
                capture_output=True, text=True, timeout=180,
            )
            out = ((r.stdout or "") + (r.stderr or "")).strip()[:1500]
            return "MISSION:\n" + out
        except Exception as e:
            return "Mission Fehler: " + str(e)[:300]

    if text.strip() in ("/mission next", "/mnext"):
        try:
            import subprocess
            r = subprocess.run(
                ["python3", "/data/data/com.termux/files/home/jack/jack_mission_queue.py", "next"],
                capture_output=True, text=True, timeout=30,
            )
            out = ((r.stdout or "") + (r.stderr or "")).strip()
            if r.returncode == 0 and "ACTIVE" in out:
                r2 = subprocess.run(
                    ["python3", "/data/data/com.termux/files/home/jack/jack_mission_run.py"],
                    capture_output=True, text=True, timeout=180,
                )
                out2 = ((r2.stdout or "") + (r2.stderr or "")).strip()[:1200]
                return "QUEUE→ACTIVE\n" + out + "\n---\n" + out2
            return "QUEUE:\n" + out
        except Exception as e:
            return "Queue Fehler: " + str(e)[:200]

    if text.strip() in ("/overmind", "/om"):
        try:
            import subprocess
            # Kurzer Health zuerst
            h = subprocess.run(
                ["python3", "/data/data/com.termux/files/home/jack/jack_health.py"],
                capture_output=True, text=True, timeout=20,
            )
            health_line = ((h.stdout or "") + (h.stderr or "")).strip()[:400]
            r = subprocess.run(
                ["python3", "/data/data/com.termux/files/home/jack/jack_overmind_client.py"],
                capture_output=True, text=True, timeout=120,
            )
            out = ((r.stdout or "") + (r.stderr or "")).strip()[:1200]
            return "OVERMIND\n" + health_line + "\n---\n" + out
        except Exception as e:
            return "Overmind Fehler: " + str(e)[:300]

    if text.strip()=='/skills':
        import jack_skill_lib as _sk
        skills=_sk.list_all()
        if not skills: return 'Keine Skills gespeichert.'
        lines=['SKILLS ('+str(len(skills))+'):']
        for s2 in skills:
            lines.append('['+s2['state']+'] '+s2['name']+' - '+str(s2['successes'])+'/'+str(s2['executions'])+' Erfolge')
        return chr(10).join(lines)
    if text.strip().startswith('skill:'):
        import jack_skill_lib as _sk, jack_planner, importlib
        importlib.reload(jack_planner)
        sname=text.strip()[6:].strip()
        skill=_sk.get(sname)
        if not skill: return 'Skill nicht gefunden: '+sname
        import threading as _th2
        _th2.Thread(target=jack_planner.run_plan,args=(skill['plan'],send),daemon=True).start()
        return 'Starte Skill: '+sname+' ['+skill['state']+']'

    # --- UI: tap / forsche / kill (Hauptleitung jack_exec) ---

    if False and text.strip() in ("/skills", "/skill"):  # dup, erster Block bleibt
        try:
            import sqlite3, os
            db = "/data/data/com.termux/files/home/jack/jack_skills.db"
            c = sqlite3.connect(db)
            rows = c.execute(
                "SELECT name, state, successes, executions FROM skills ORDER BY state, name"
            ).fetchall()
            c.close()
            lines = ["SKILLS (%d):" % len(rows)]
            for name, state, suc, ex in rows[:40]:
                lines.append("%s | %s | ok=%s/%s" % (name, state, suc, ex))
            send("\n".join(lines) if rows else "Keine Skills in DB")
        except Exception as e:
            send("skills Fehler: " + str(e)[:200])
        return



    if text.strip().startswith('/tap'):
        q = text.strip()[4:].strip()
        if not q:
            send("Nutzung: /tap Chrome\\nOder: /tap Einstellungen")
            return
        try:
            import jack_exec
            out = jack_exec.tap_text(q)
            send("TAP: " + str(out)[:1500])
        except Exception as e:
            send("TAP Fehler: " + str(e)[:300])
        return

    if text.strip().startswith('/forsche'):
        topic = text.strip()[8:].strip() or "Ollama Termux"
        try:
            flag = "/data/data/com.termux/files/home/jack/.jack_ui_run"
            kill = "/data/data/com.termux/files/home/jack/.jack_ui_kill"
            if os.path.isfile(kill):
                os.remove(kill)
            open(flag, "w").write(topic)
            import urllib.parse
            q = urllib.parse.quote(topic)
            url = "https://www.google.com/search?q=" + q
            # Chrome mit Suche (Xiaomi)
            cmd = (
                "ssh -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "
                "\"su -c 'input keyevent 224; input keyevent 82; input swipe 540 1500 540 1000 160; "
                "am start -a android.intent.action.VIEW -d %s "
                "-n com.android.chrome/com.google.android.apps.chrome.Main'\""
            ) % repr(url)
            import jack_exec
            out = jack_exec.run(cmd, timeout=40)
            send(
                chat_id,
                "Forschung gestartet: " + topic + "\\nChrome/Suche auf Xiaomi.\\n"
                "Stoppen: /kill\\n\\n" + str(out)[:800],
            )
        except Exception as e:
            send("Forsche Fehler: " + str(e)[:300])
        return

    if text.strip() in ("/kill", "/stop"):
        try:
            kill = "/data/data/com.termux/files/home/jack/.jack_ui_kill"
            open(kill, "w").write("1")
            flag = "/data/data/com.termux/files/home/jack/.jack_ui_run"
            if os.path.isfile(flag):
                os.remove(flag)
            # leichte Stopps
            import subprocess
            subprocess.run(
                "pkill -f run_guarded_settings; pkill -f jack_ui_; pkill -f ui_agent.cortex",
                shell=True, capture_output=True,
            )
            send("KILL: UI/Forschung gestoppt (.jack_ui_kill gesetzt).")
        except Exception as e:
            send("KILL Fehler: " + str(e)[:300])
        return


    if text.strip().startswith('/sehen'):
        try:
            import jack_vision
            _frage = text.strip()[6:].strip() or "Was siehst du?"
            return jack_vision.analyze_screen(_frage)
        except Exception as e:
            return 'Vision-Fehler: ' + str(e)[:100]
    if text.strip() in ['/selftest','/test']:
        import jack_cortex
        return jack_cortex.selftest()
    if text.strip() == '/kette' or text.strip().startswith('/kette '):
        try:
            import jack_chains
            _teile = text.strip().split(None, 1)
            if len(_teile) == 1:
                _kb=[[('System-Vollcheck','cmd:/kette system_vollcheck')],[('Xiaomi reparieren','cmd:/kette xiaomi_reparieren')],[('Notfall-Recovery','cmd:/kette notfall_recovery')],[('Morgen-Briefing','cmd:/kette morgen_briefing')]]
                send_keyboard('Aktionsketten (antippen = starten):', _kb)
                return None
            _kn = _teile[1].strip()
            send('Kette startet: ' + _kn)
            import threading as _kth
            def _krun():
                try:
                    _r = jack_chains.run(_kn)
                    send(_r.get('text', 'Kette fertig, kein Text'))
                except Exception as _ke:
                    send('Ketten-Fehler: ' + str(_ke)[:150])
            _kth.Thread(target=_krun, daemon=True).start()
            return None
        except Exception as _ke2:
            return 'Ketten-Fehler: ' + str(_ke2)[:150]
    if text.strip() == '/bugfix':
        send('Bugfix-Loop startet: suche fixbare Bugs in errors.db...')
        import threading as _bth
        def _brun():
            try:
                import jack_bugfix_loop as _bl
                _erg = _bl.run(max_bugs=1)
                send(str(_erg)[:3500] if _erg else 'Bugfix-Loop ohne Ergebnis')
            except Exception as _be:
                send('Bugfix-Fehler: ' + str(_be)[:150])
        _bth.Thread(target=_brun, daemon=True).start()
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
    if any(k in text.lower() for k in ['xiaomi inspizieren', 'xiaomi prozesse', 'xiaomi umgebung', 'xiaomi system inspect']) and len(text) < 50:
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

    _rt = text.strip()
    if _rt in ('/errors','/error'):
        try:
            import sqlite3 as _sq
            con=_sq.connect(os.path.expanduser('~/jack/jack_errors.db'),timeout=5)
            rows=con.execute('SELECT module,error_msg,timestamp FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 5').fetchall(); con.close()
            return 'Keine offenen Fehler.' if not rows else chr(10).join(f'[{r[2][:16]}] {r[0]}: {r[1][:60]}' for r in rows)
        except Exception as _e: return 'Errors-Fehler: '+str(_e)[:80]
    if _rt in ('/akku','/sensor'):
        try: import jack_sensors as _js; return _js.get_battery()+' | '+_js.get_motion()
        except Exception as _e: return 'Akku-Fehler: '+str(_e)[:80]
    if _rt == '/log':
        try: import jack_log as _jl; return 'JACKs Logbuch:'+chr(10)+_jl.recent(15)
        except Exception as _e: return 'Log-Fehler: '+str(_e)[:80]
    if _rt == '/level':
        try:
            import jack_intent as _ji; lvl=_ji.get_level()
            return f'Autonomie-Level: {lvl}/4'
        except Exception as _e: return 'Level-Fehler: '+str(_e)[:80]
    if _rt == '/vision' or _rt.startswith('/vision '):
        _frage = _rt[8:].strip() or None
        send('Vision: Screenshot vom Xiaomi laeuft...')
        import threading as _vth
        def _do_analyze(q=_frage):
            try:
                import jack_android as _ja2
                if q:
                    result = _ja2.run(q, max_rounds=5)
                    send('VISION: ' + str(result)[:1500])
                else:
                    elements = _ja2.get_ui_tree()
                    send('Vision: ' + str(len(elements)) + ' Elemente gefunden')
            except Exception as e:
                send('Vision-Fehler: ' + str(e)[:150])
        _vth.Thread(target=_do_analyze, daemon=True).start()
        return None

    if _rt == '/harvest_status':
        import jack_harvest as _jh
        return _jh.status()
    if _rt == '/harvest_lernen':
        send('Destilliere Fakten aus geernteten Chats...')
        import threading as _lth
        def _lrun():
            try:
                import jack_harvest_lernen as _jl
                send(str(_jl.lernen()))
            except Exception as _e:
                send('Lern-Fehler: ' + str(_e)[:150])
        _lth.Thread(target=_lrun, daemon=True).start()
        return None
    if _rt == '/fakten':
        import jack_harvest_lernen as _jl
        return _jl.zeige_fakten()
    if _rt.startswith('/harvest'):
        _teile = _rt.split()
        _quelle = _teile[1] if len(_teile) > 1 else 'unbekannt'
        _runden = int(_teile[2]) if len(_teile) > 2 and _teile[2].isdigit() else 20
        send(f'Harvest startet: {_quelle}, max {_runden} Runden. Chrome mit offenem Chat muss im Vordergrund sein. Stop: /harvest_stop')
        import threading as _hth
        def _hrun():
            try:
                import jack_harvest as _jh
                _r = _jh.harvest(_quelle, _runden, status_fn=send)
                send(f'HARVEST FERTIG: {_r.get("neu",0)} neue Eintraege in {_r.get("runden",0)} Runden. {_r.get("grund","")}')
            except Exception as _e:
                send('Harvest-Fehler: ' + str(_e)[:150])
        _hth.Thread(target=_hrun, daemon=True).start()
        return None
    if _rt == '/activity':
        try:
            import jack_activity_logger as _al
            return _al.generate_summary(24)
        except Exception as e:
            return 'Activity-Fehler: ' + str(e)[:100]
    if _rt == '/outcomes':
        try:
            import jack_outcome_tracker as _ot
            stats = _ot.get_stats(10)
            if not stats: return 'Noch keine Outcomes gespeichert.'
            lines = ['OUTCOMES (Top 10 Befehle):']
            for cmd, total, succ in stats:
                rate = (succ / total * 100) if total > 0 else 0
                lines.append(f'{cmd[:50]} - {total}x ({rate:.0f}% Erfolg)')
            return chr(10).join(lines)
        except Exception as e:
            return 'Outcomes-Fehler: ' + str(e)[:100]
    if _rt.startswith('/agent'):
        _ziel = text.strip()[6:].strip() or "optimiere system"
        return 'AGENT gestartet: ' + _ziel + chr(10) + 'Status: In Entwicklung'
    if _rt.startswith('/auto'):
        _ziel = text.strip()[5:].strip() or "optimiere jack"
        return 'AUTO gestartet: ' + _ziel + chr(10) + 'Status: In Entwicklung'
    if _rt.startswith('/ssh'):
        _cmd = text.strip()[4:].strip()
        if not _cmd:
            return 'Syntax: /ssh <befehl>'
        try:
            import jack_exec
            return jack_exec.run('ssh xiaomi-jack "' + _cmd + '"', timeout=30)
        except Exception as e:
            return 'SSH-Fehler: ' + str(e)[:100]
    if _rt.startswith('/code'):
        _desc = text.strip()[5:].strip()
        if not _desc:
            return 'Syntax: /code <beschreibung>'
        return 'CODE-GENERATOR: ' + _desc + chr(10) + 'Status: In Entwicklung (braucht jack_coder Integration)'
    if _rt == '/run':
        return 'RUN: Letzten Code ausführen - Status: In Entwicklung'
    if _rt.startswith('/cc'):
        _frage = text.strip()[3:].strip() or "analysiere jack_exec"
        try:
            import jack_talk as _jt
            return _jt.talk_to_gemini('CC: ' + _frage)
        except Exception as e:
            return 'CC-Fehler: ' + str(e)[:100]
    if _rt == '/db_skills':
        try:
            import sqlite3
            c = sqlite3.connect(os.path.expanduser('~/jack/jack_skills.db'))
            rows = c.execute('SELECT name, state, COUNT(*) FROM skills GROUP BY name, state').fetchall()
            c.close()
            lines = ['SKILLS-DB:']
            for name, state, count in rows[:20]:
                lines.append(f'{name}: {state} ({count}x)')
            return chr(10).join(lines)
        except Exception as e:
            return 'Skills-DB-Fehler: ' + str(e)[:100]
    if _rt.startswith('/db_trace'):
        _query = text.strip()[9:].strip() or "SELECT * FROM outcomes LIMIT 10"
        try:
            import sqlite3
            c = sqlite3.connect(os.path.expanduser('~/jack/jack_outcomes.db'))
            rows = c.execute(_query).fetchall()
            c.close()
            return 'TRACE: ' + str(len(rows)) + ' Zeilen' + chr(10) + str(rows[:5])
        except Exception as e:
            return 'Trace-DB-Fehler: ' + str(e)[:100]
    if _rt.startswith('/find'):
        _element = text.strip()[5:].strip() or "Suchleiste"
        try:
            import jack_screen_mapper as sm
            h, pkg, act, els = sm.dump_and_parse()
            found = [e for e in els if _element.lower() in str(e).lower()]
            if found:
                return f'FOUND: {len(found)} Elemente mit "{_element}"' + chr(10) + str(found[:3])
            else:
                return f'NICHT GEFUNDEN: "{_element}" auf Screen {pkg}/{act}'
        except Exception as e:
            return 'Find-Fehler: ' + str(e)[:100]
    if _rt.startswith('/mission'):
        _aufgabe = text.strip()[8:].strip() or "pruefe logs"
        try:
            import jack_autonomous
            return 'MISSION gestartet: ' + _aufgabe + chr(10) + 'Status: ' + str(jack_autonomous.run_task(_aufgabe))
        except Exception as e:
            return 'Mission-Fehler: ' + str(e)[:100]
    if _rt.startswith('/rag'):
        _query = text.strip()[4:].strip() or "Python"
        try:
            import jack_memory
            results = jack_memory.search_similar(_query, limit=5)
            if results:
                lines = ['RAG: ' + str(len(results)) + ' Treffer']
                for r in results[:3]:
                    lines.append('  ' + str(r)[:80])
                return chr(10).join(lines)
            else:
                return f'RAG: Keine Treffer für "{_query}"'
        except Exception as e:
            return 'RAG-Fehler: ' + str(e)[:100]
    if _rt == '/skill_builder':
        return 'SKILL-BUILDER: Status: In Entwicklung (braucht jack_skill_builder Modul)'
    if _rt == '/tb':
        return 'TRACEBACK: Kein aktiver Fehler. System läuft stabil.'
    if _rt.startswith('/verbessere'):
        _modul = text.strip()[11:].strip() or "jack_memory"
        return 'VERBESSERE: ' + _modul + chr(10) + 'Status: In Entwicklung (braucht jack_coder Integration)'
    if _rt == '/budget':
        try:
            import jack_budget as _jb; return str(_jb.status())
        except Exception as _e: return 'Budget-Fehler: ' + str(_e)[:120]
    if _rt == '/missionen':
        try:
            import jack_missions as _jm; return str(_jm.uebersicht())
        except Exception as _e: return 'Missionen-Fehler: ' + str(_e)[:120]
    if _rt == '/audit':
        try:
            import jack_audit as _ja; return str(_ja.report())
        except Exception as _e: return 'Audit-Fehler: ' + str(_e)[:120]
    if _rt == '/scan':
        try:
            import jack_monitor as _jmo; return str(_jmo.vollscan())
        except Exception as _e: return 'Scan-Fehler: ' + str(_e)[:120]
    if _rt == '/baum':
        try:
            import jack_memory_tree as _jmt
            return (str(_jmt.statistik()) + chr(10) + str(_jmt.letzte_kette(5)))
        except Exception as _e: return 'Baum-Fehler: ' + str(_e)[:120]
    if _rt == '/trace':
        try:
            import sqlite3 as _sq, os as _os
            _c=_sq.connect(_os.path.expanduser('~/jack/jack_cognition.db'), timeout=5)
            _rows=_c.execute('SELECT * FROM traces ORDER BY rowid DESC LIMIT 5').fetchall(); _c.close()
            return 'Letzte Traces:' + chr(10) + chr(10).join(str(_r)[:180] for _r in _rows) if _rows else 'Keine Traces vorhanden.'
        except Exception as _e: return 'Trace-Fehler: ' + str(_e)[:120]
    if _rt == '/werkstatt':
        try:
            import os as _os
            _w=_os.path.expanduser('~/jack_werkstatt'); _f=sorted(_os.listdir(_w)) if _os.path.isdir(_w) else []
            return 'Werkstatt: ' + str(len(_f)) + ' Dateien' + chr(10) + chr(10).join(_f[-5:])
        except Exception as _e: return 'Werkstatt-Fehler: ' + str(_e)[:120]
    if text.startswith('/rag '):
        q = text[5:].strip()
        if not q: return 'Nutzung: /rag <suchbegriff>'
        try:
            import sqlite3 as _sq
            con = _sq.connect(os.path.expanduser('~/jack/jack_memory.db'))
            rows = con.execute(
                'SELECT content FROM ingested_context WHERE content LIKE ? LIMIT 5',
                ('%' + q + '%',)).fetchall()
            con.close()
            if not rows: return 'Keine RAG-Treffer fuer: ' + q
            sep = chr(10) + '---' + chr(10)
            return 'RAG [' + q + ']:' + chr(10)+chr(10) + sep.join(r[0][:200] for r in rows)
        except Exception as e: return 'RAG-Fehler: ' + str(e)

    if text.strip() == '/autolearn_status':
        try:
            import subprocess as _sp
            r = _sp.run(['pgrep', '-f', 'jack_autolearn_loop.py'],
                capture_output=True, text=True)
            p = r.stdout.strip()
            log = os.path.expanduser('~/jack/autolearn.log')
            last = open(log).readlines()[-1].strip() if os.path.exists(log) else '(kein Log)'
            st = 'PIDs: ' + p if p else 'NICHT LAUFEND'
            return 'Autolearn: ' + st + chr(10) + 'Log: ' + last[:150]
        except Exception as e: return 'Autolearn-Fehler: ' + str(e)

    if text.strip() == '/ingest_status':
        try:
            import subprocess as _sp2
            r = _sp2.run(['pgrep', '-f', 'jack_auto_ingest.py'],
                capture_output=True, text=True)
            p = r.stdout.strip()
            import sqlite3 as _sq2
            con = _sq2.connect(os.path.expanduser('~/jack/jack_memory.db'))
            n = con.execute('SELECT COUNT(*) FROM ingested_context').fetchone()[0]
            con.close()
            st = 'PIDs: ' + p if p else 'NICHT LAUFEND'
            return 'Ingest: ' + st + chr(10) + 'DB: ' + str(n) + ' Eintraege'
        except Exception as e: return 'Ingest-Fehler: ' + str(e)

    _NUTZUNG = {
        '/rag': 'Nutzung: /rag <suchbegriff>\nBeispiel: /rag KEYCODE_BACK',
        '/ssh': 'Nutzung: /ssh <befehl>\nBeispiel: /ssh uptime',
        '/agent': 'Nutzung: /agent <ziel>\nBeispiel: /agent oeffne die Einstellungen',
        '/find': 'Nutzung: /find <was>\nBeispiel: /find Suchleiste',
        '/vision': 'Nutzung: /vision <frage>\nBeispiel: /vision was siehst du',
        '/explore': 'Nutzung: /explore <paket>\nBeispiel: /explore com.android.settings',
    }
    _c0 = _rt.split()[0].lower()
    if _c0 in _NUTZUNG:
        return _NUTZUNG[_c0]

    if _rt.lower() == '/standort':
        send('Frage Position vom Xiaomi ab, kann bis 50s dauern...')
        def _do_standort():
            try:
                import jack_sensors as _js2
                loc = _js2.get_location()
                if 'error' in loc:
                    send('Standort-Fehler: ' + str(loc['error'])); return
                send('Standort: ' + str(loc.get('latitude')) + ', ' +
                     str(loc.get('longitude')) + ' (Genauigkeit: ' +
                     str(loc.get('accuracy')) + 'm)')
            except Exception as _e2:
                send('Standort-Fehler: ' + str(_e2)[:100])
        import threading
        threading.Thread(target=_do_standort, daemon=True).start()
        return None
    if _rt == '/lernen' or _rt.startswith('/lernen '):
        import subprocess as _sp_l, json as _j_l
        try:
            _b = _j_l.loads(_sp_l.run(['termux-battery-status'], capture_output=True, text=True, timeout=8).stdout)
            if _b.get('percentage', 100) < 30:
                return 'Akku unter 30% - Lernen ausgesetzt'
            if float(_b.get('temperature', 0)) > 45:
                return 'Temperatur ueber 45C - Lernen ausgesetzt'
        except Exception:
            pass
        try:
            for _l in open('/proc/meminfo'):
                if 'MemAvailable' in _l:
                    if int(_l.split()[1]) // 1024 < 800:
                        return 'RAM unter 800MB - Lernen ausgesetzt'
                    break
        except Exception:
            pass
        send('Lernrunde startet: 5 Experimente auf Stufe-0-Parametern...')
        import threading as _lth
        def _lrun():
            try:
                import subprocess as _sp3
                r = _sp3.run(['python3', os.path.expanduser('~/jack/jack_lerner.py'), 'runde'],
                             capture_output=True, text=True, timeout=300, cwd=os.path.expanduser('~/jack'))
                send('LERNRUNDE FERTIG:' + chr(10) + (r.stdout or r.stderr)[:2000])
            except Exception as e:
                send('Lern-Fehler: ' + str(e)[:150])
        _lth.Thread(target=_lrun, daemon=True).start()
        return None
    if _rt.startswith('/'):
        return 'Unbekannter Befehl: ' + _rt.split()[0] + ' - /menu zeigt alle Befehle.'


    try:  # JACK_TUNE_CHATGATE
        import jack_chat_router as _cr
        _lane=_cr.classify(text)
        if _lane in ("FACT","EXPLAIN","DIAG"):
            _r=_cr.dispatch(text, send_keyboard)
            if _r is False:
                return None
            if _r:
                return _r
    except Exception:
        pass
    # Deep-Navigation VOR App-Handler (Qwen 21.08.)
    try:
        import jack_intent_lookup as _il
        _intent, _cmd = _il.suggest_deep_navigation(text)
        if _cmd:
            PENDING_EXEC.clear()
            PENDING_EXEC['cmd'] = _cmd
            send_keyboard('VORSCHLAG (Deep):' + chr(10) + _cmd, [[(' Ausfuehren', 'run_exec'), (' Abbrechen', 'cancel_exec')]])
            return None
    except Exception:
        pass
    import jack_intent_apps
    try:
        import jack_ui_nav as _nav
        _hit,_act,_ok,_msg=_nav.try_nav_intent(text)
        if _hit:
            send(("NAV OK: " if _ok else "NAV FAIL: ")+str(_act)+" | "+str(_msg))
            return None
    except Exception:
        pass
    try:  # JACK_TUNE_MAPSYT_H
        import re as _re
        import jack_ui_type as _ut
        _t=text
        _mm=_re.search(r"(?:navigiere (?:zu|nach)|maps|karte|zeig(?:e)? (?:mir )?(?:den weg|die route) (?:zu|nach)|route nach)\s+(.+)", _t, _re.I)
        if _mm and len(_t)<140:
            _ok,_msg=_ut.maps_open(_mm.group(1).strip())
            send(("MAPS OK: " if _ok else "MAPS FAIL: ")+str(_msg)[:180])
            return None
        _my=_re.search(r"(?:youtube|yt)\s+(.+)", _t, _re.I)
        if (not _my) and _re.search(r"(?:spiel(?:e)?|zeig(?:e)?)\s+.+\s+(?:auf|bei)\s+youtube", _t, _re.I):
            _my=_re.search(r"(?:spiel(?:e)?|zeig(?:e)?)\s+(.+?)\s+(?:auf|bei)\s+youtube", _t, _re.I)
        if _my and len(_t)<140:
            _q=_my.group(1).strip()
            _ok,_msg=_ut.youtube_play(_q)
            send(("YT OK: " if _ok else "YT FAIL: ")+str(_msg)[:180])
            return None
    except Exception:
        pass
    try:  # JACK_TUNE_SPOTIFY_SUR
        import re as _re
        if _re.search(r"\b(überrasche mich|surprise|irgendwas abspielen|zufall\w* (song|track|musik))\b", text, _re.I):
            import jack_ui_type as _ut
            _ok,_msg=_ut.spotify_surprise()
            send(("SPOTIFY OK: " if _ok else "SPOTIFY FAIL: ")+str(_msg)[:180])
            return None
    except Exception:
        pass
    try:  # JACK_TUNE_MAPS_YT_H
        import re as _re
        _m=_re.search(r"(?:navigiere(?: zu)?|maps|route nach|zeig(?: mir)? (?:den )?weg (?:nach|zu))\s+(.+)", text, _re.I)
        if _m and len(text)<120:
            import jack_ui_type as _ut
            _ok,_msg=_ut.maps_nav(_m.group(1).strip())
            send(("MAPS OK: " if _ok else "MAPS FAIL: ")+str(_msg)[:160])
            return None
        _m=_re.search(r"(?:youtube|yt|zeig(?: mir)? (?:auf )?youtube)\s+(.+)", text, _re.I)
        if _m and len(text)<120:
            import jack_ui_type as _ut
            _ok,_msg=_ut.youtube_search(_m.group(1).strip())
            send(("YT OK: " if _ok else "YT FAIL: ")+str(_msg)[:160])
            return None
    except Exception:
        pass
    try:  # JACK_TUNE_SPOTIFY_H
        import re as _re
        _m=_re.search(r"(?:spiel|play)\s+(.+)", text, _re.I)
        if _m and len(text)<100:
            _q=_m.group(1).strip()
            for _cut in (" auf dem xiaomi", " auf xiaomi", " bitte", " bei spotify"):
                if _q.lower().endswith(_cut.strip()):
                    _q=_q[:len(_q)-len(_cut)].strip()
            import jack_ui_type as _ut
            _ok,_msg=_ut.spotify_play(_q)
            send(("SPOTIFY OK: " if _ok else "SPOTIFY FAIL: ")+str(_msg)[:180])
            return None
    except Exception:
        pass
    try:  # JACK_TUNE_CHROME_SEARCH
        import re as _re
        _m=_re.search(r"(?:suche|search|google)\s+(?:in\s+chrome\s+)?(?:nach\s+)?(.+)", text, _re.I)
        if _m and len(text)<120:
            _q=_m.group(1).strip()
            for _cut in (" auf dem xiaomi", " auf xiaomi", " bitte"):
                if _q.lower().endswith(_cut.strip()):
                    _q=_q[:len(_q)-len(_cut)].strip()
            import jack_ui_type as _ut
            _ok,_msg=_ut.chrome_search(_q)
            send(("CHROME OK: " if _ok else "CHROME FAIL: ")+str(_msg)[:180])
            return None
    except Exception:
        pass
    if jack_intent_apps.try_app_launch(text, PENDING_EXEC, send_keyboard):
        return None
    # LLM Call mit Timeout und EXEC-Parser
    try:
        import jack_talk as _jt
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("LLM-Timeout nach 15s")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        import jack_chat_router as _cr
        resp=_cr.dispatch(text, send_keyboard)
        if resp is False:
            return None
        if resp is None:
            resp = _jt.talk_to_gemini(text)  # JACK_TUNE_ISTPLAIN
            try:
                import jack_chat_router as _cr2
                if resp:
                    resp=_cr2.strip_lane_tags(_cr2.apply_lane(resp, text))  # JACK_TUNE_LANESTRIP
            except Exception:
                pass
            if resp and "Ausfuehren oder beenden" in resp:
                send_keyboard(resp, [[("🟢 Ausführen","selfsee_go"),("🔴 Abbrechen","selfsee_no")]])
                resp=None
        signal.alarm(0)
        
        if not resp:
            return None
        
        # EXEC-Parser inline
        cmd = None
        if '[[EXEC:' in resp:
            start = resp.find('[[EXEC:') + 7
            end = resp.find(']]', start)
            if end != -1: cmd = resp[start:end].strip()
        elif '[[EXECUTE:' in resp:
            start = resp.find('[[EXECUTE:') + 10
            end = resp.find(']]', start)
            if end != -1: cmd = resp[start:end].strip()
        
        if cmd:
            # SSH-Befehle bereinigen
            if 'sshpass' in cmd or '10.229.239.131' in cmd:
                import re
                match = re.search(r"'(am start.*?)'", cmd)
                if match:
                    cmd = 'ssh xiaomi-jack su -c "' + match.group(1) + '"'
                else:
                    cmd = 'ssh xiaomi-jack su -c "' + cmd.split()[-1].strip("'") + '"'
            
            PENDING_EXEC.clear()
            PENDING_EXEC['cmd'] = cmd
            preview = cmd if len(cmd) < 800 else cmd[:800] + ' ...'
            send_keyboard('VORSCHLAG:' + chr(10) + preview, [[(' Ausführen', 'run_exec'), (' Abbrechen', 'cancel_exec')]])
            
            # Tag entfernen
            import re
            resp = re.sub(r'\[\[EXEC(?:UTE)?:.*?\]\]', '', resp).strip()
        
        return resp if resp else None
    except TimeoutError:
        return "⚠️ LLM-Timeout (15s). Bitte nochmal versuchen."
    except Exception as _te:
        return f"LLM-Fehler: {_te}"


def _offset_lesen():
    try:
        return int(open(os.path.expanduser('~/.jack_tg_offset')).read().strip())
    except Exception:
        return 0

def _offset_schreiben(wert):
    try:
        open(os.path.expanduser('~/.jack_tg_offset'), 'w').write(str(wert))
    except Exception:
        pass

def _einzelinstanz():
    """Verhindert Doppelbots: zweiter Prozess beendet sich selbst.
    Lock ueber O_EXCL plus Lebendigkeitspruefung der eingetragenen PID."""
    lock = os.path.expanduser("~/.jack_telegram.lock")
    meine = os.getpid()
    if os.path.exists(lock):
        try:
            alt = int(open(lock).read().strip())
        except Exception:
            alt = 0
        lebt = False
        if alt and alt != meine:
            try:
                os.kill(alt, 0)
                cmd = open("/proc/" + str(alt) + "/cmdline").read()
                lebt = "jack_telegram" in cmd
            except Exception:
                lebt = False
        if lebt:
            print("[TG] Bot laeuft bereits als PID " + str(alt) + " - beende mich.")
            raise SystemExit(0)
        try: os.remove(lock)
        except Exception: pass
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f: f.write(str(meine))
    except FileExistsError:
        print("[TG] Lock-Rennen verloren - beende mich.")
        raise SystemExit(0)
    import atexit
    def _weg():
        try:
            if int(open(lock).read().strip()) == meine: os.remove(lock)
        except Exception: pass
    atexit.register(_weg)
    print("[TG] Einzelinstanz-Lock gesetzt (PID " + str(meine) + ")")

def main():
    _einzelinstanz()
    try: send("JACK online. Alle Dienste gestartet.")
    except Exception: pass
    vibrate(200)
    offset = _offset_lesen()
    import jack_inbox; jack_inbox.start_inbox_poller(send)
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
                if 'photo' in msg and chat_id:
                    file_id = msg['photo'][-1]['file_id']
                    caption = msg.get('caption','Was siehst du? Analysiere auf Deutsch.')
                    send('📸 Analysiere...')
                    vibrate(80)
                    def _foto(fid=file_id, cap=caption):
                        try:
                            import urllib.request as _ur, json as _j, base64, subprocess as _sp2, os as _o2
                            url = f"{API}/getFile?file_id={fid}"
                            with _ur.urlopen(url) as res:
                                path = _j.loads(res.read())['result']['file_path']
                            dl = f"https://api.telegram.org/file/bot{TOKEN}/{path}"
                            raw = _o2.path.expanduser(f"~/jack/foto_{fid}.jpg")
                            _ur.urlretrieve(dl, raw)
                            b64 = base64.b64encode(open(raw,'rb').read()).decode()
                            import jack_gemini_bridge as _gb, jack_config as _jc
                            key = _gb.load_api_key()
                            model = _jc.get_param('gemini','model')
                            payload = _j.dumps({
                                "system_instruction":{"parts":[{"text":_PERSONA}]},
                                "contents":[{"parts":[{"text":cap},{"inline_data":{"mime_type":"image/jpeg","data":b64}}]}]
                            }).encode()
                            req = _ur.Request(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",data=payload,headers={"Content-Type":"application/json"})
                            with _ur.urlopen(req,timeout=45) as r:
                                ans = _j.loads(r.read())['candidates'][0]['content']['parts'][0]['text']
                            send(ans[:3000])
                            try: _o2.remove(raw)
                            except Exception: pass
                        except Exception as e:
                            send("Foto-Fehler: " + str(e)[:200])
                    import threading
                    threading.Thread(target=_foto, daemon=True).start()
                    continue
                if 'voice' in msg and chat_id:
                    file_id = msg['voice']['file_id']
                    ogg = os.path.expanduser(f'~/jack/voice_{file_id}.ogg')
                    rw = ogg.replace('.ogg','_resp.wav')
                    send('🎤')
                    vibrate(60)
                    def _vrun(fid=file_id, op=ogg):
                        try:
                            get_voice(fid, op)
                            rw2, heard, ans = process_voice_message(op)
                            if isinstance(ans, str) and ans.startswith('__APPCMD__:'):
                                _pkg = ans.split(':', 1)[1]
                                _cmd = 'ssh xiaomi-jack "su -c \'monkey -p ' + _pkg + ' -c android.intent.category.LAUNCHER 1\'"'
                                PENDING_EXEC.clear()
                                PENDING_EXEC['cmd'] = _cmd
                                send_keyboard('VORSCHLAG:' + chr(10) + _cmd, [[('🟢 Ausfuehren', 'run_exec'), ('🔴 Abbrechen', 'cancel_exec')]])
                                send('Du: ' + str(heard) + chr(10) + chr(10) + 'JACK: App-Befehl erkannt - Freigabe tippen.')
                                ans = ''
                                rw2 = None
                            else:
                                import jack_exec_parser
                                ans = jack_exec_parser.parse_and_prepare(str(ans), PENDING_EXEC, send_keyboard) or ''
                            if isinstance(ans, str) and ans.startswith('__APPCMD__:'):
                                _pkg = ans.split(':', 1)[1]
                                _cmd = 'ssh xiaomi-jack "su -c \'monkey -p ' + _pkg + ' -c android.intent.category.LAUNCHER 1\'"'
                                PENDING_EXEC.clear()
                                PENDING_EXEC['cmd'] = _cmd
                                send_keyboard('VORSCHLAG:' + chr(10) + _cmd, [[('🟢 Ausfuehren', 'run_exec'), ('🔴 Abbrechen', 'cancel_exec')]])
                                send('Du: ' + str(heard) + chr(10) + chr(10) + 'JACK: App-Befehl erkannt - Freigabe tippen.')
                                ans = ''
                                rw2 = None
                            else:
                                pass
                            import jack_exec_parser
                            # Deep-Navigation VOR App-Handler (Voice)
                            try:
                                import jack_intent_lookup as _il2
                                _intent2, _cmd2 = _il2.suggest_deep_navigation(str(heard))
                                if _cmd2:
                                    PENDING_EXEC.clear()
                                    PENDING_EXEC['cmd'] = _cmd2
                                    send_keyboard('VORSCHLAG (Deep):' + chr(10) + _cmd2, [[(' Ausfuehren', 'run_exec'), (' Abbrechen', 'cancel_exec')]])
                                    _deep_handled = True
                                else:
                                    _deep_handled = False
                            except Exception:
                                _deep_handled = False
                            if not _deep_handled:
                                import jack_intent_apps
                                if jack_intent_apps.try_app_launch(str(heard), PENDING_EXEC, send_keyboard):
                                    _app_handled = True
                                else:
                                    _app_handled = False
                            else:
                                _app_handled = False
                            if _deep_handled:
                                send("Du: "+str(heard)+chr(10)+chr(10)+"JACK: Deep-Navigation bereit - Freigabe tippen.")
                            elif _app_handled:
                                send("Du: "+str(heard)+chr(10)+chr(10)+"JACK: App-Befehl bereit - Freigabe tippen.")
                            else:
                                send("Du: "+str(heard)+chr(10)+chr(10)+"JACK: "+str(ans))
                            try: send_voice(rw2)
                            except Exception: pass
                            for f in (op, rw2):
                                try: os.remove(f)
                                except Exception: pass
                        except Exception as e:
                            send("Sprachfehler: " + str(e)[:100])
                    import threading
                    threading.Thread(target=_vrun, daemon=True).start()
                    continue
                if text and chat_id:
                    vibrate(40)
                    reply = handle(text)
                    if reply:
                        import re as _rw
                        _m=_rw.search(r'\[\[WRITE:(.+?)\]\](.*?)\[\[/WRITE\]\]', reply, _rw.S)
                        if _m:
                            _fn=_m.group(1).strip(); _ct=_m.group(2).strip()
                            _p=jack_write.propose(_fn,_ct)
                            PENDING_WRITE.clear(); PENDING_WRITE.update(_p)
                            _clean=_rw.sub(r'\[\[WRITE:.+?\]\].*?\[\[/WRITE\]\]','',reply,flags=_rw.S).strip()
                            if _clean: send(_clean)
                            send_keyboard("Datei: "+_p['filename']+chr(10)+chr(10)+_p['preview'],[[('🟢 Bestätigen','confirm_write:'+_p['filename']),('🔴 Abbrechen','cancel_write:'+_p['filename'])]])
                        else:
                            send(reply)
                        try:
                            import jack_talk as _jt
                            _jt.add_to_window(text, reply)
                        except Exception: pass
        except Exception as e:
            time.sleep(2)
        import jack_heartbeat; jack_heartbeat.beat('jack_telegram')
        time.sleep(1)

if __name__ == '__main__':
    main()
