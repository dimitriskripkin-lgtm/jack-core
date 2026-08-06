#!/usr/bin/env python3
"""JACK Hey - Hands-free Sprach-Interaktion mit End-to-End-Stoppuhr."""
import os, sys, subprocess, time, asyncio

sys.path.append(os.path.expanduser("~/jack"))
import jack_voice_router as vr

HOME = os.path.expanduser("~")
REC = os.path.join(HOME, ".jack_hey.m4a")

# Globale Stoppuhr
TIMER = time.time()

def log_phase(phase):
    elapsed = time.time() - TIMER
    print(f"[TIMER {elapsed:6.2f}s] {phase}")

def aufnehmen(sekunden=10):
    if os.path.exists(REC):
        try: os.remove(REC)
        except Exception: pass
    
    log_phase(f"Starte Aufnahme für {sekunden} Sekunden... Sprich JETZT!")
    subprocess.run(["termux-microphone-record", "-f", REC, "-e", "aac", "-r", "16000", "-l", str(sekunden)], capture_output=True)
    
    time.sleep(sekunden + 1)
    
    subprocess.run(["termux-microphone-record", "-q"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    size = os.path.getsize(REC) if os.path.exists(REC) else 0
    log_phase(f"Aufnahme beendet. Dateigröße: {size} Bytes.")
    
    if size < 1000:
        log_phase("WARNUNG: Aufnahme zu klein.")
        return False
    return True

async def main():
    log_phase("=== JACK HEY START ===")
    
    if not aufnehmen(10):
        log_phase("Keine verwertbare Aufnahme. Abbruch.")
        return
    
    log_phase("Starte Voice-Router...")
    result = await vr.route_voice(REC)
    
    if result["success"]:
        if result["stack"] == "A":
            log_phase("Stack A erfolgreich. Audio-Wiedergabe gestartet.")
        elif result["stack"] == "B":
            log_phase(f"Stack B erfolgreich. Text: {result['text']}")
    else:
        log_phase(f"Fehler: {result['error']}")
    
    log_phase("=== JACK HEY ENDE ===")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log_phase("Abgebrochen durch Benutzer.")
