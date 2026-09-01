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


def is_remote_alive(host, port, timeout=5):
    """Live TCP-Probe — kein Ping, funktioniert auf Android."""
    import socket
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except Exception:
        return False

def is_xiaomi_alive():
    """SSH-Port-Probe auf Xiaomi — Wahrheit statt Datei-mtime."""
    import configparser, os
    cfg = configparser.ConfigParser()
    cfg.read(os.path.expanduser('~/jack/config.ini'))
    host = cfg.get('xiaomi', 'ip', fallback='10.229.239.131')
    port = int(cfg.get('xiaomi', 'ssh_port', fallback='8022'))
    return is_remote_alive(host, port)

if __name__ == "__main__":
    import sys
    for d in ("jack_cortex", "jack_telegram", "jack_autolearn", "jack_waechter"):
        a = age(d)
        print(f"{d}: {'nie' if a is None else str(int(a)) + 's alt'}")
