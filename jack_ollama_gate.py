#!/usr/bin/env python3
# ---------------------------------------------------------------
# OLLAMA-REFERENZEN — Klassifizierung 03.09.2026 (Cloud + Honor-Messung)
# 16 Dateien nennen Port 11434. Nur drei koennen Ollama STARTEN.
#
# STARTET (Lock noetig, Lock vorhanden):
#   jack_ollama_gate.py        start() prueft .ollama_lock
#   jack_heat_protection.py    fallback prueft .ollama_lock
#   jack_voraussetzung.py      ollama_an() prueft Lock ab L57
#
# LIEST NUR (kein Lock noetig):
#   jack_autonomous.py         L220 urlopen /api/tags — Sonde
#   jack_voice_router.py       L190 /api/chat gegen localhost (Honor hat kein
#                              Ollama -> toter Pfad). Popen L86 ist mpv, nicht Ollama.
#   jack_autofixer_shadow.py   jack_curiosity.py    jack_intent.py
#   jack_lokal.py              jack_loop.py         jack_talk.py
#   jack_tuev3.py              jack_ui_elements.py  jack_ui_read.py
#   jack_xiaomi_think.py       jack_xiaomi_web.py
#
# Ergebnis: Lock-Abdeckung vollstaendig. Kein weiterer Patch noetig.
# ---------------------------------------------------------------

MODULE_VERSION = 1
"""jack_ollama_gate.py — Ollama on-demand: warm -> use -> cool down."""
import subprocess, time, threading, os, logging

JACK      = "/data/data/com.termux/files/home/jack"
SVC       = "/data/data/com.termux/files/usr/var/service/ollama"
def _ollama_url():
    host="10.229.239.131"
    try:
        g=subprocess.run(["ssh","-G","xiaomi-jack"],capture_output=True,text=True,timeout=5)
        for ln in (g.stdout or "").splitlines():
            if ln.startswith("hostname "): host=ln.split(None,1)[1].strip()
    except Exception:
        pass
    return "http://%s:11434"%host  # JACK_TUNE_GURL
OLLAMA = _ollama_url()
TEMP_MAX  = 52.0
IDLE_STOP = 90
log       = logging.getLogger("ollama_gate")
_timer    = None
_lock     = threading.Lock()

def _ssh(cmd, timeout=10):
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", f"ConnectTimeout={timeout}",
         "xiaomi-jack", cmd],
        capture_output=True, text=True, timeout=timeout + 2
    )
    return r.stdout.strip()

def get_temp() -> float:
    try:
        raw = _ssh("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null | sort -rn | head -1")
        return round(int(raw.strip()) / 1000, 1)
    except Exception as e:
        log.warning(f"Temp-Read fehlgeschlagen: {e}")
        return 0.0

def temp_ok() -> bool:
    t = get_temp()
    log.info(f"Xiaomi Temp: {t}C (Limit {TEMP_MAX}C)")
    return t < TEMP_MAX

def _ollama_ready(retries=12) -> bool:
    try:
        import requests
        for _ in range(retries):
            try:
                r = requests.get(f"{OLLAMA}/api/tags", timeout=3)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(1)
    except ImportError:
        time.sleep(6)
        return True
    return False

def start() -> bool:
    if os.path.exists("/data/data/com.termux/files/home/jack/.ollama_lock"):
        log.warning("Ollama-Start gesperrt: .ollama_lock")
        return False
    if not temp_ok():
        log.warning("Ollama-Start abgelehnt: Xiaomi zu heiss")
        return False
    _ssh(f"sv up {SVC}")
    ok = _ollama_ready()
    log.info("Ollama bereit" if ok else "Ollama nicht bereit nach Start")
    return ok

MAX_RUN = 300  # JACK_TUNE_HARDSTOP — harte Obergrenze in Sekunden
_start_ts = None

def _schedule_stop():
    global _timer, _start_ts
    if _timer:
        _timer.cancel()
    # harte Grenze: laeuft der Dienst laenger als MAX_RUN, sofort stoppen
    import time as _t
    if _start_ts is None:
        _start_ts = _t.time()
    elif _t.time() - _start_ts > MAX_RUN:
        _ssh(f"sv down {SVC}")
        log.info(f"Ollama nach {MAX_RUN}s Hartgrenze gestoppt")
        _start_ts = None
        return
    def _do_stop():
        _ssh(f"sv down {SVC}")
        t = get_temp()
        log.info(f"Ollama gestoppt. Xiaomi Temp danach: {t}C")
    _timer = threading.Timer(IDLE_STOP, _do_stop)
    _timer.daemon = True
    _timer.start()

def call(prompt: str, model: str = "llama3.2:3b") -> str:
    import requests as req
    with _lock:
        if not start():
            return "[Ollama offline: zu heiss oder SSH-Fehler]"
        try:
            r = req.post(f"{OLLAMA}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=60)
            result = r.json().get("response", "")
        except Exception as e:
            result = f"[Ollama-Fehler: {e}]"
        _schedule_stop()
        return result

if __name__ == "__main__":
    print(f"Xiaomi Temp: {get_temp()}C")
    print(f"temp_ok: {temp_ok()}")
