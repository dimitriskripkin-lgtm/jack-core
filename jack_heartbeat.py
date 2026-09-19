#!/usr/bin/env python3
MODULE_VERSION = 2  # bumped by shadow
"""Heartbeat: Dienste melden Lebenszeichen. Waechter prueft mtime statt nur sv status."""
import os, time
from jack_log import get_logger
log = get_logger("jack_heartbeat")

H = os.path.expanduser("~/jack")

def beat(dienst):
    """Vom Dienst aufrufen, z.B. einmal pro Loop-Durchlauf."""
    try:
        open(os.path.join(H, f".heartbeat_{dienst}"), "w").write(str(time.time()))
    except Exception:
        pass

def age(dienst):
    """Sekunden seit letztem Lebenszeichen. None wenn nie."""
    p = os.path.join(H, f".heartbeat_{dienst}")
    if not os.path.exists(p):
        return None
    try:
        return time.time() - float(open(p).read().strip())
    except Exception:
        return None

def is_alive(dienst, max_age=600):
    a = age(dienst)
    return a is not None and a < max_age


def sleep_until(dienst, seconds):
    """JACK_TUNE_PHASEA2: Dienst meldet eigene geplante Aufwachzeit."""
    try:
        open(os.path.join(H, f".sleep_until_{dienst}"), "w").write(str(time.time()+seconds))
    except Exception:
        pass

def is_sleeping(dienst):
    p = os.path.join(H, f".sleep_until_{dienst}")
    try:
        return time.time() < float(open(p).read().strip())
    except Exception:
        return False

def is_remote_alive(host, port, timeout=5):
    """Live TCP-Probe — kein Ping, funktioniert auf Android."""
    import socket
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except Exception:
        return False

def is_xiaomi_alive():
    import subprocess
    host, port = "10.229.239.131", 8022
    try:
        g = subprocess.run(["ssh","-G","xiaomi-jack"], capture_output=True, text=True, timeout=5)
        for ln in (g.stdout or "").splitlines():
            if ln.startswith("hostname "): host=ln.split(None,1)[1].strip()
            if ln.startswith("port "):
                try: port=int(ln.split(None,1)[1].strip())
                except Exception: pass
    except Exception:
        pass
    return is_remote_alive(host, port)  # JACK_TUNE_SSHG
if __name__ == "__main__":
    import sys
    for d in ("jack_cortex", "jack_telegram", "jack_autolearn", "jack_waechter"):
        a = age(d)
        print(f"{d}: {'nie' if a is None else str(int(a)) + 's alt'}")
