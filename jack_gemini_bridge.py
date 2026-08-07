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

def collect_status():
    status = {"timestamp": datetime.now().isoformat()}
    r = subprocess.run(["sv", "status", "jack_cortex"], capture_output=True, text=True)
    status["cortex"] = r.stdout.strip()
    try:
        con = sqlite3.connect(ERRORS_DB)
        count = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
        recent = con.execute("SELECT error_msg FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 3").fetchall()
        status["open_errors"] = count
        status["recent_errors"] = [r[0][:100] for r in recent]
        con.close()
    except: status["open_errors"] = "unknown"
    import jack_config as _jc; _xip = _jc.get_param("NETWORK","xiaomi_ip")
    import subprocess as _sp
    _r = _sp.run(["ssh","-i",os.path.expanduser("~/.ssh/id_jack"),"-o","BatchMode=yes","-o","StrictHostKeyChecking=no","-o","ConnectTimeout=3","-p","8022",f"root@{_xip}","true"],capture_output=True,timeout=6)
    status["xiaomi_reachable"] = _r.returncode == 0
    return status

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
        "SPRACHE: Deutsch. Du. Kumpel-Ton. Maximal 3-4 Saetze bei normalem Chat. "
        "TECHNISCH: Honor Magic8 Pro Host, Xiaomi 11T Pro Slave SSH 10.58.220.131:8022. Gemini=Denkwerkzeug, du BIST JACK."
    )
    content = f"SYSTEM-STATUS:\n{json.dumps(status, indent=2)}\n\nFRAGE: {question}" if status else question
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": content}]}]
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    import time as _t
    for _a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                result = json.loads(res.read())
                try:
                    import jack_budget; jack_budget.add_tokens(result.get("usageMetadata",{}).get("totalTokenCount",0))
                except Exception as _e:
                    import jack_log; jack_log.log_decision('SILENT-FAIL jack_gemini', str(_e)[:120])
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as _e:
            _code = getattr(_e, "code", None)
            if _code == 429 and _a < 2:
                _t.sleep(4 * (_a + 1)); continue
            if _code == 429:
                return "Gemini ist gerade ueberlastet (Rate-Limit). Gleich nochmal probieren."
            if _a < 2:
                _t.sleep(2); continue
            return f"Gemini-Verbindungsfehler: {_e}"

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
