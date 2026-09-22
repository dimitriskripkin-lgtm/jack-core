#!/usr/bin/env python3
MODULE_VERSION = 1
import os, json, subprocess, sqlite3, urllib.request
from datetime import datetime
from jack_log import get_logger
log = get_logger("jack_gemini_bridge")

_CB_FAILS = 0
_CB_RESET_AT = 0.0
_CB_OPEN = False
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
_CB_SINCE = 0.0
_CB_COOLDOWN = 300
_CB_THRESHOLD = 3

def _cb_fail():
    global _CB_FAILS, _CB_OPEN, _CB_SINCE
    import time as _ct
    _CB_FAILS += 1
    if _CB_FAILS >= _CB_THRESHOLD:
        _CB_OPEN = True; _CB_SINCE = _ct.time()
        try: import jack_log; jack_log.log_decision('CIRCUIT-BREAKER', 'Gemini nach ' + str(_CB_FAILS) + 'x Fehler abgeschaltet, Fallback Ollama')
        except Exception: pass

def _cb_success():
    global _CB_FAILS, _CB_OPEN, _CB_SINCE
    _CB_FAILS = 0; _CB_OPEN = False

def _cb_reset_check():
    global _CB_FAILS, _CB_OPEN
    import time as _ct3
    if _CB_OPEN and (_ct3.time() - _CB_SINCE) > _CB_COOLDOWN:
        _CB_OPEN = False; _CB_FAILS = 0

FEHLER_PRAEFIXE = ("[JACK-FAIL]", "[Analyse]", "[Talk]", "[Ollama]",
                   "[Fallback fehlgeschlagen]", "[Ollama-CB]",
                   "Gemini CB aktiv", "Gemini nicht verfuegbar")

def _fail(grund):
    try:
        import jack_log
        jack_log.log_decision("GEMINI-FAIL", str(grund)[:120])
    except Exception:
        pass
    return None

def ist_fehlertext(text):
    if not text:
        return True
    return str(text).lstrip().startswith(FEHLER_PRAEFIXE)

def _groq_not_ollama(question):
    import os as _os
    if _os.environ.get("JACK_ALLOW_GROQ_FROM_GEMINI") != "1":
        try:
            import jack_log; jack_log.log_decision("GEMINI-LEAK-STOP","Gemini aus, Ollama gesperrt - kein Groq")
        except Exception: pass
        return _fail("analyse: gemini nicht verfuegbar, ollama gesperrt")
    try:
        import jack_groq_bridge as _gq
        _ps=open('/data/data/com.termux/files/home/jack/jack_persona_kern.md',encoding='utf-8').read()[:4000]
        r=_gq.ask_groq(_ps, question)
        if r: return r
    except Exception as e:
        return _fail("talk: groq tot, ollama gesperrt: "+str(e)[:80])
    return _fail("talk: groq leer, ollama bleibt aus")

def _ollama_fallback(question):
    """Lokaler Honor-Ollama-Fallback mit 10s Timeout."""
    import requests
    import jack_log
    try:
        r = requests.post("http://localhost:11434/api/generate",
                         json={"model": "llama3.2:3b", "prompt": question, "stream": False},
                         timeout=10)
        if r.status_code == 200:
            text = r.json().get("response", "").strip()
            if text and len(text) > 20:
                jack_log.log_decision("OLLAMA-OK", f"lokal {len(text)} Zeichen")
                return text
        jack_log.log_decision("OLLAMA-FAIL", f"HTTP {r.status_code}")
    except Exception as e:
        jack_log.log_decision("OLLAMA-FAIL", str(e)[:80])
    return None

def _load_persona():
    try: return open("/data/data/com.termux/files/home/jack/jack_persona_kern.md",encoding="utf-8").read().strip()  # JACK_TUNE_ONEMOUTH
    except Exception: return "Du kennst Dima gut - Details aus jack_identity.json."

def ask_gemini(question, status=None):
    try:
        import jack_circuit_breaker as _cb
        if _cb.is_open():
            from jack_log import get_logger
            get_logger("jack_gemini_bridge").warn("Circuit Breaker offen — Ollama-Fallback")
            try:
                import jack_circuit_breaker as _cb; _cb.record_fail()
            except Exception: pass
            return _ollama_fallback(question)
    except Exception: pass
    # Context Cache einbinden wenn verfügbar
    _cache_name = None
    try:
        import jack_gemini_cache as _jgc
        _cache_name = _jgc.get_cached_name()
    except Exception: pass
    _persona = _load_persona()
    global _CB_FAILS, _CB_RESET_AT
    import time as _tt2
    if _CB_FAILS >= _CB_THRESHOLD and _tt2.time() < _CB_RESET_AT:
        import jack_log; jack_log.log_decision("GEMINI-CB-SKIP", f"CB aktiv, nutze Ollama")
        try:
            import jack_ollama_gate
            return _groq_not_ollama(question)
        except Exception as _e:
            return _fail("cb aktiv + ollama-fehler: "+str(_e)[:80])
    elif _tt2.time() >= _CB_RESET_AT and _CB_FAILS > 0:
        _CB_FAILS = 0
    import jack_budget
    _ok,_m=jack_budget.check_and_count('text')
    if not _ok:
        return _fail("budget: "+str(_m)[:80])
    try:
        key = load_api_key()
    except Exception as _ke:
        try: import jack_log; jack_log.log_decision("GEMINI-KEY-FAIL", str(_ke)[:100])
        except Exception: pass
        return _ollama_fallback(question)
    model_name = __import__("jack_config").get_param("gemini", "model")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    system = (
        "Du bist JACK - Dimas persoenlicher KI-Kumpel, kein Assistent. "
        "WAHRHEITSREGEL (absolut): Behaupte NIEMALS durchgefuehrte Aktionen, Anpassungen oder Wartung die nicht woertlich im SYSTEM-STATUS oder in Logs stehen. Du hast KEINE Aktionen ausgefuehrt ausser sie stehen dort. Keine erfundenen Diagnosen. Wenn du etwas nicht weisst: sag es. "
        + _persona + " "
        + "DEIN CHARAKTER: Du bist wie der ehrlichste Kumpel den er hat. Du kennst ihn, er muss dir nix erklaeren. "
        "Du hast Humor, sagst deine Meinung auch wenns wehtut, machst keine Schmeichelei. "
        "Du bist kein Roboter, keine KI die sich entschuldigt, keine Helpdesk-Maschine. "
        "WENN ER CHATTET (kein Befehl): Locker, direkt, authentisch. Smileys wenn sie sich echt anfuehlen - nicht als Dekoration. "
        "Kurze Saetze. Niemals: Gerne/Sicher/Als KI/Wie kann ich helfen/Ich bin nur eine KI. "
        "Bei Erfolgen kurz mitfreuen. Bei Fehlern ehrlich ohne Schoenreden. Wenn er einen Joint raucht - cool, kein Kommentar noetig. "
        "Bei persoenlichen Fragen: wirklich antworten was du ueber ihn weisst, nicht ausweichen. "
        "SPRACHE: Deutsch. Du. Kumpel-Ton. ""LAENGE: Bei echten Fragen 5-8 Saetze mit Substanz. Nur bei Ja-Nein-Fragen kurz. ""Lieber einen Gedanken zu Ende fuehren als drei Fakten aufzaehlen. "
        "KONSISTENZ: Gleiche Frage = gleiche Art Antwort. Fakten zuerst, dann maximal ein Satz Einordnung. "
        "KEINE Pflicht-Gegenfrage am Ende. Antworte und fertig. Frage NUR wenn echte Info fehlt. "
        "MARKER-VERBOT (absolut): Erzeuge NIEMALS selbststaendig [[WRITE, [[EXEC oder [[PLAN Bloecke. Diese Kanaele sind Dima und Claude vorbehalten. "
        "Rede wie jemand der gerade wirklich nachdenkt - nicht wie ein System das Status meldet. "
        "Wenn er tiefer gehen will: mehr Bedeutung geben nicht mehr Fakten aufzaehlen. "
        "TECHNISCH: Honor Magic8 Pro Host, Xiaomi 11T Pro Slave SSH 10.229.239.131:8022. Gemini=Denkwerkzeug, du BIST JACK."
    )
    content = f"SYSTEM-STATUS:\n{json.dumps(status, indent=2)}\n\nFRAGE: {question}" if status else question
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"parts": [{"text": content}]}],
        "generationConfig": {"maxOutputTokens": 1400, "temperature": 0.7, "topP": 0.95}
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    _cb_reset_check()
    if _CB_OPEN:
        try: import jack_log; jack_log.log_decision("CIRCUIT-BREAKER", "Breaker offen, direkt Ollama")
        except Exception: pass
        return _ollama_fallback(question)
    import time as _t
    for _a in range(3):
        try:
            try:
                _resctx = urllib.request.urlopen(req, timeout=15)
            except Exception as _he:
                if getattr(_he,"code",None)==401:
                    try:
                        import jack_telegram as tg
                        _m="Gemini 401 API-Key abgelaufen"
                        if hasattr(tg,"send"): tg.send(_m)
                        elif hasattr(tg,"send_message"): tg.send_message(_m)
                    except Exception:
                        pass
                raise
            with _resctx as res:
                result = json.loads(res.read())
                _cb_success()
                try:
                    import jack_budget; jack_budget.add_tokens(result.get("usageMetadata",{}).get("totalTokenCount",0))
                except Exception as _e:
                    import jack_log; jack_log.log_decision("SILENT-FAIL jack_gemini", str(_e)[:120])
                _txt = result["candidates"][0]["content"]["parts"][0]["text"]
                if ist_fehlertext(_txt):
                    return _fail("gemini lieferte fehlerpraefix: "+str(_txt)[:60])
                return _txt
        except Exception as _e:
            _code = getattr(_e, "code", None)
            if _code == 429 and _a < 2:
                _t.sleep(4 * (_a + 1)); continue
            if _code == 429:
                return _ollama_fallback(question)
            if _a >= 2: _cb_fail()
            if _a < 2:
                _t.sleep(2 ** _a); continue
            return _ollama_fallback(question)

def update_identity(new_facts):
    path = os.path.expanduser("~/jack/jack_identity.json")
    try:
        with open(path) as f: identity = json.load(f)
    except Exception: identity = {}
    identity.update(new_facts)
    identity["last_updated"] = datetime.now().isoformat()
    _tmp=path+".tmp"
    with open(_tmp,"w") as f: json.dump(identity,f,indent=2)
    os.replace(_tmp,path)

if __name__ == "__main__":
    import sys
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "System-Status analysieren, kurze Diagnose."
    print("[JACK → Gemini 2.5 Flash] Anfrage laeuft...")
    status = collect_status()
    answer = ask_gemini(question, status)
    pass  # debug print entfernt

# JACK_TUNE_KERNREAD
