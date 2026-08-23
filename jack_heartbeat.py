#!/usr/bin/env python3
"""Heartbeat: Dienste melden Lebenszeichen. Waechter prueft mtime statt nur sv status."""
import os, time

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

if __name__ == "__main__":
    import sys
    for d in ("jack_cortex", "jack_telegram", "jack_autolearn", "jack_waechter"):
        a = age(d)
        print(f"{d}: {'nie' if a is None else str(int(a)) + 's alt'}")
