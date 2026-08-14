#!/usr/bin/env python3
"""JACK RAM-Guard + Prozess-Lock. Verhindert OOM-Kills bei Schwerlast."""
import os, json, urllib.request

H = os.path.expanduser("~/jack")
SEC = os.path.expanduser("~/.jack_secrets")
MIN_RAM_MB = 800

class GuardBlocked(Exception):
    pass

def mem_available_mb():
    """Echter nutzbarer RAM. MemFree ist irrefuehrend, nie verwenden."""
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) // 1024
    except Exception:
        pass
    return -1

def _log(a, d=""):
    try:
        import jack_log; jack_log.log_decision(a, d)
    except Exception:
        import sys; print("[jack_guard] " + a + ": " + d, file=sys.stderr)

def _sec(k):
    try:
        for l in open(SEC):
            if k in l and "=" in l:
                return l.split('"')[1] if '"' in l else l.split("=", 1)[1].strip()
    except Exception:
        pass
    return None

def notify(t):
    tok = _sec("TELEGRAM_BOT_TOKEN"); cid = _sec("TELEGRAM_CHAT_ID")
    if not tok or not cid: return
    try:
        d = json.dumps({"chat_id": cid, "text": "[JACK Guard] " + t}).encode()
        r = urllib.request.Request(
            "https://api.telegram.org/bot" + tok + "/sendMessage",
            data=d, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(r, timeout=10)
    except Exception as e:
        _log("GUARD-NOTIFY-FEHLER", str(e)[:100])

def _pid_alive(pid):
    try:
        os.kill(pid, 0); return True
    except Exception:
        return False

def _lock_path(name):
    return os.path.join(H, "." + name + ".lock")

def acquire(name):
    """Lockfile-Mutex ueber Prozessgrenzen. True wenn Lock geholt."""
    p = _lock_path(name)
    if os.path.exists(p):
        try: old = int(open(p).read().strip())
        except Exception: old = -1
        if old > 0 and _pid_alive(old):
            return False
        _log("GUARD-STALE-LOCK", name + " PID " + str(old) + " tot, raeume auf")
        try: os.remove(p)
        except Exception: pass
    try:
        fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode()); os.close(fd)
        return True
    except Exception:
        return False

def release(name):
    try: os.remove(_lock_path(name))
    except Exception: pass

class Guard:
    """Context Manager: RAM-Check + Lock. Wirft GuardBlocked bei Ablehnung."""
    def __init__(self, name, min_mb=MIN_RAM_MB):
        self.name = name; self.min_mb = min_mb; self.held = False

    def __enter__(self):
        ram = mem_available_mb()
        if ram < 0:
            _log("GUARD-RAM-UNLESBAR", "meminfo nicht lesbar, lasse durch")
        elif ram < self.min_mb:
            m = self.name + " abgelehnt: nur " + str(ram) + "MB frei (min " + str(self.min_mb) + "MB)"
            _log("GUARD-RAM-BLOCK", m); notify(m)
            raise GuardBlocked(m)
        if not acquire(self.name):
            m = self.name + " laeuft bereits, Anfrage abgelehnt"
            _log("GUARD-LOCK-BLOCK", m); notify(m)
            raise GuardBlocked(m)
        self.held = True
        _log("GUARD-OK", self.name + " gestartet, " + str(ram) + "MB frei")
        return self

    def __exit__(self, *a):
        if self.held: release(self.name)
        return False

def get_model(default="gemini-2.5-flash", light="llama3.2:3b"):
    """Gibt leichteres Modell zurueck wenn RAM/Akku/Hitze kritisch."""
    ram = mem_available_mb()
    if ram > 0 and ram < 1200:
        _log("GRACEFUL-DEGRADE", "RAM nur " + str(ram) + "MB, schalte auf " + light)
        return light
    try:
        batt = int(open("/sys/class/power_supply/battery/capacity").read().strip())
        if batt < 15:
            _log("GRACEFUL-DEGRADE", "Akku " + str(batt) + "%, schalte auf " + light)
            return light
    except Exception:
        pass
    return default

def saga_cleanup(base_path=None):
    """Rauemt verwaiste temp-Dateien nach abgebrochenen Voice-Pipelines auf."""
    import glob, time
    H = os.path.expanduser('~/jack')
    patterns = ['voice_*.ogg','voice_*.wav','voice_*_resp.wav','.voice_rec.*']
    removed = []
    for pat in patterns:
        for f in glob.glob(os.path.join(H, pat)):
            try:
                age = time.time() - os.path.getmtime(f)
                if age > 120:
                    os.remove(f)
                    removed.append(os.path.basename(f))
            except Exception:
                pass
    if removed:
        _log('SAGA-CLEANUP', str(len(removed)) + ' temp-Dateien geloescht: ' + ','.join(removed[:5]))
    return removed

if __name__ == "__main__":
    print("MemAvailable:", mem_available_mb(), "MB")
    print("Schwelle:", MIN_RAM_MB, "MB")
    with Guard("selftest", min_mb=1):
        print("Lock geholt:", os.path.exists(_lock_path("selftest")))
    print("Lock freigegeben:", not os.path.exists(_lock_path("selftest")))
