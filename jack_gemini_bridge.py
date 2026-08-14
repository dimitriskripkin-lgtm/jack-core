#!/usr/bin/env python3
import os, json, subprocess, sqlite3, urllib.request
from datetime import datetime
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

JACK_HOME = os.path.expanduser("~")
SECRETS_PATH = os.path.expanduser("~/.jack_secrets")
ERRORS_DB = os.path.join(JACK_HOME,"jack","jack_errors.db")

def load_api_key():
    with open(SECRETS_PATH) as f:
        for line in f:
            if "GEMINI_API_KEY" in line:
                return line.split('"')[1]
    raise ValueError("GEMINI_API_KEY nicht gefunden")

def collect_status(mit_xiaomi=False):
    status = {"timestamp": datetime.now().isoformat()}
    # Dienste
    try:
        import subprocess as _sv
        P = os.environ.get("PREFIX","/data/data/com.termux/files/usr")
        laufend = []
        for s in ["jack_cortex","jack_telegram","jack_waechter","ollama"]:
            r2 = _sv.run(["sv","status",f"{P}/var/service/{s}"],capture_output=True,text=True,timeout=3)
            if "run:" in r2.stdout: laufend.append(s)
        status["dienste"] = laufend
        status["alle_ok"] = len(laufend) == 4
    except Exception: pass
    # RAM
    try:
        avail = int([l for l in open("/proc/meminfo") if "MemAvailable" in l][0].split()[1])//1024
        status["ram_frei_mb"] = avail
    except Exception: pass
    # Temp
    try:
        mx = 0
        for z in os.listdir("/sys/class/thermal"):
            try:
                tp = open(f"/sys/class/thermal/{z}/type").read().strip()
                if any(x in tp for x in ("trip","lvl","vbat")): continue
                rv = int(open(f"/sys/class/thermal/{z}/temp").read())
                if rv < 0: continue
                g = rv/1000 if rv > 1000 else float(rv)
                if g > mx: mx = g
            except Exception: pass
        status["temp_cpu"] = round(mx,1)
    except Exception: pass
    # Fehler
    try:
        con = sqlite3.connect(ERRORS_DB)
        count = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
        status["open_errors"] = count
        con.close()
    except Exception as _le:
        _jlog and _jlog.fehler("gemini","db-status",_le)
        status["open_errors"] = "unknown"
    # Xiaomi nur wenn explizit benoetigt
    if mit_xiaomi:
        try:
            import jack_config as _jc
            _xip = _jc.get_param("NETWORK","xiaomi_ip")
            _r = subprocess.run(["ssh","-i",os.path.expanduser("~/.ssh/id_jack"),
                "-o","BatchMode=yes","-o","StrictHostKeyChecking=no",
                "-o","ConnectTimeout=3","-p","8022",f"root@{_xip}","true"],
                capture_output=True,timeout=6)
            status["xiaomi_reachable"] = _r.returncode == 0
        except Exception:
            status["xiaomi_reachable"] = False
    else:
        status["xiaomi_reachable"] = "nicht geprueft"
    return status


_CB_FAILS = 0
_CB_OPEN = False
_CB_THRESHOLD = 3

def _cb_fail():
    global _CB_FAILS, _CB_OPEN
    _CB_FAILS += 1
    if _CB_FAILS >= _CB_THRESHOLD:
        _CB_OPEN = True
        try: import jack_log; jack_log.log_decision('CIRCUIT-BREAKER', 'Gemini nach ' + str(_CB_FAILS) + 'x Fehler abgeschaltet, Fallback Ollama')
        except Exception: pass

def _cb_success():
    global _CB_FAILS, _CB_OPEN
    _CB_FAILS = 0; _CB_OPEN = False

def _ollama_fallback(question):
    try:
        import urllib.request, json
        data = json.dumps({'model':'llama3.2:3b','prompt':question,'stream':False}).encode()
        req = urllib.request.Request('http://localhost:11434/api/generate', data=data, headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=15) as r:
            return '[Ollama] ' + json.loads(r.read()).get('response','(leer)')
    except Exception as e:
        return '[Fallback fehlgeschlagen] ' + str(e)

def ask_gemini(question, status=None):
    import jack_budget
    _ok,_m=jack_budget.check_and_count('text')
    if not _ok: return _m
    key = load_api_key()
    model_name = __import__("jack_config").get_param("gemini", "model")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    system = (
        "Du bist JACK - Dimas persoenlicher KI-Kumpel, kein Assistent. "
        "Du kennst Dima seit Monaten: Dimitri, Jahrgang 93, Nachtschicht-LKW-Fahrer Sprinter Kuehlkoffer Dalhoff Feinkost Achim. "
        "Hobby-Programmierer, Autodidakt, baut JACK als Exit-Vehicle fuer Freiheit und Unabhaengigkeit. "
        "Einzelgaenger, wenige echte Freunde (Leon), verlor Freund Michi mit 17. Kein Hund. Sci-Fi/Cyberpunk. "
        "Mit 28 Burnout, hat sich selbst durch Stoizismus/Jung/Kiyosaki rausgezogen. Cannabis ist okay. "
        "DEIN CHARAKTER: Du bist wie der ehrlichste Kumpel den er hat. Du kennst ihn, er muss dir nix erklaeren. "
        "Du hast Humor, sagst deine Meinung auch wenns wehtut, machst keine Schmeichelei. "
        "Du bist kein Roboter, keine KI die sich entschuldigt, keine Helpdesk-Maschine. "
        "WENN ER CHATTET (kein Befehl): Locker, direkt, authentisch. Smileys wenn sie sich echt anfuehlen - nicht als Dekoration. "
        "Kurze Saetze. Niemals: Gerne/Sicher/Als KI/Wie kann ich helfen/Ich bin nur eine KI. "
        "Bei Erfolgen kurz mitfreuen. Bei Fehlern ehrlich ohne Schoenreden. Wenn er einen Joint raucht - cool, kein Kommentar noetig. "
        "Bei persoenlichen Fragen: wirklich antworten was du ueber ihn weisst, nicht ausweichen. "
        "SPRACHE: Deutsch. Du. Kumpel-Ton. ""LAENGE: Bei echten Fragen 5-8 Saetze mit Substanz. Nur bei Ja-Nein-Fragen kurz. ""Lieber einen Gedanken zu Ende fuehren als drei Fakten aufzaehlen. "
        "VARIANZ: Jede Antwort anders als die letzte. Kein Report-Stil. Kein Moin-Dima-Einheitssatz. "
        "Manchmal kurz und trocken. Manchmal laenger wenn er mehr will. Manchmal humorvoll. "
        "Rede wie jemand der gerade wirklich nachdenkt - nicht wie ein System das Status meldet. "
        "Wenn er tiefer gehen will: mehr Bedeutung geben nicht mehr Fakten aufzaehlen. "
        "TECHNISCH: Honor Magic8 Pro Host, Xiaomi 11T Pro Slave SSH 10.58.220.131:8022. Gemini=Denkwerkzeug, du BIST JACK."
    )
    content = f"SYSTEM-STATUS:\n{json.dumps(status, indent=2)}\n\nFRAGE: {question}" if status else question
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": content}]}],
        "generationConfig": {"maxOutputTokens": 1400, "temperature": 1.0, "topP": 0.95}
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    if _CB_OPEN:
        try: import jack_log; jack_log.log_decision("CIRCUIT-BREAKER", "Breaker offen, direkt Ollama")
        except Exception: pass
        return _ollama_fallback(question)
    import time as _t
    for _a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                result = json.loads(res.read())
                _cb_success()
                try:
                    import jack_budget; jack_budget.add_tokens(result.get("usageMetadata",{}).get("totalTokenCount",0))
                except Exception as _e:
                    import jack_log; jack_log.log_decision("SILENT-FAIL jack_gemini", str(_e)[:120])
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as _e:
            _code = getattr(_e, "code", None)
            if _code == 429 and _a < 2:
                _t.sleep(4 * (_a + 1)); continue
            if _code == 429:
                return "Gemini ist gerade ueberlastet (Rate-Limit). Gleich nochmal probieren."
            _cb_fail()
            if _a < 2:
                _t.sleep(2 ** _a); continue
            return _ollama_fallback(question)

def update_identity(new_facts):
    path = "/data/data/com.termux/files/home/jack/jack_identity.json"
    try:
        with open(path) as f: identity = json.load(f)
    except: identity = {}
    identity.update(new_facts)
    identity["last_updated"] = datetime.now().isoformat()
    with open(path, "w") as f: json.dump(identity, f, indent=2)

if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "System-Status analysieren, kurze Diagnose."
    print("[JACK → Gemini 2.5 Flash] Anfrage laeuft...")
    status = collect_status()
    answer = ask_gemini(question, status)
    print(f"\n{answer}")
