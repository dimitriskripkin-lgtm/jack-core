#!/usr/bin/env python3
import os, json, subprocess, sqlite3, urllib.request
from datetime import datetime

JACK_HOME = "/data/data/com.termux/files/home"
SECRETS_PATH = os.path.expanduser("~/.jack_secrets")
ERRORS_DB = f"{JACK_HOME}/jack/jack_errors.db"

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
    ping = subprocess.run(["ping", "-c", "1", "-W", "2", "10.244.147.131"], capture_output=True)
    status["xiaomi_reachable"] = ping.returncode == 0
    return status

def ask_gemini(question, status=None):
    import jack_budget
    _ok,_m=jack_budget.check_and_count('text')
    if not _ok: return _m
    key = load_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={key}"
    system = (
        "Du bist JACKs Reasoning-Layer. JACK laeuft auf Honor Magic8 Pro (Termux). "
        "Slave: Xiaomi 11T Pro via SSH (10.244.147.131:8022, Key ~/.ssh/id_jack). "
        "Antworten: kurz, technisch, direkt. Kein Bullshit. Deutsch."
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
