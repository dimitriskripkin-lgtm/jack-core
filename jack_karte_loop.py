#!/usr/bin/env python3
"""JACK Karten-Dauerlauf: kartiert restliche Settings-Activities im Hintergrund.
Stop: touch ~/jack/.karte_stop"""
import os, sys, time
sys.path.insert(0, os.path.expanduser("~/jack"))
import jack_karte

STOP = os.path.expanduser("~/jack/.karte_stop")
PID = os.path.expanduser("~/jack/.karte_loop.pid")

def ram_frei():
    try:
        for l in open("/proc/meminfo"):
            if l.startswith("MemAvailable:"):
                return int(l.split()[1]) // 1024
    except Exception:
        pass
    return -1

def log(msg):
    print(time.strftime("%H:%M:%S") + " | " + str(msg), flush=True)

def main():
    if os.path.exists(STOP):
        os.remove(STOP)
    with open(PID, "w") as f:
        f.write(str(os.getpid()))
    log("Karten-Dauerlauf gestartet (PID " + str(os.getpid()) + ")")
    while True:
        if os.path.exists(STOP):
            log("Stop-Datei gefunden - ende sauber.")
            break
        ram = ram_frei()
        if 0 <= ram < 800:
            log("RAM knapp (" + str(ram) + "MB) - warte 60s")
            time.sleep(60)
            continue
        acts, w = jack_karte.activities()
        karte = jack_karte.lade_karte()
        rest = [a for a in acts if a not in karte]
        if not rest:
            log("Alle " + str(len(acts)) + " Activities kartiert - fertig.")
            break
        log(str(len(rest)) + " uebrig")
        try:
            log(jack_karte.chunk(20))
        except Exception as e:
            log("FEHLER: " + str(e)[:120])
        time.sleep(2)
    try:
        os.remove(PID)
    except Exception:
        pass

if __name__ == "__main__":
    main()
