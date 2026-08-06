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

SEKUNDEN = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 10

STILLE_DB = "-35dB"
STILLE_SEK = 2.0

def _stille_am_ende(pfad):
    """True wenn am Ende der Aufnahme STILLE_SEK Sekunden Ruhe sind."""
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", pfad, "-af",
             "silencedetect=noise=" + STILLE_DB + ":d=" + str(STILLE_SEK),
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=10)
        aus = r.stderr
        if "silence_start" not in aus:
            return False, 0.0
        # Dauer der Datei ermitteln
        dauer = 0.0
        for zeile in aus.split(chr(10)):
            if "Duration:" in zeile:
                t = zeile.split("Duration:")[1].split(",")[0].strip()
                h, m, sek = t.split(":")
                dauer = int(h)*3600 + int(m)*60 + float(sek)
        # Letzter silence_start
        letzter = None
        for zeile in aus.split(chr(10)):
            if "silence_start:" in zeile:
                try: letzter = float(zeile.split("silence_start:")[1].strip().split()[0])
                except Exception: pass
        if letzter is None or dauer == 0.0:
            return False, dauer
        # Stille bis zum Ende? Dann kein silence_end nach letztem start
        rest = aus.split("silence_start: " + str(letzter))[-1]
        offen = "silence_end" not in rest
        return offen, dauer
    except Exception:
        return False, 0.0

def _hat_sprache(pfad):
    """True wenn ueberhaupt etwas ueber der Schwelle war."""
    try:
        r = subprocess.run(
            ["ffmpeg", "-hide_banner", "-i", pfad, "-af", "volumedetect",
             "-f", "null", "-"],
            capture_output=True, text=True, timeout=10)
        for zeile in r.stderr.split(chr(10)):
            if "max_volume:" in zeile:
                wert = float(zeile.split("max_volume:")[1].replace("dB","").strip())
                return wert > -30.0
    except Exception:
        pass
    return True

def aufnehmen(sekunden=10):
    """Nimmt auf, stoppt frueher wenn zwei Sekunden Stille erkannt werden."""
    if os.path.exists(REC):
        try: os.remove(REC)
        except Exception: pass

    log_phase("Starte Aufnahme (max " + str(sekunden) + "s, stoppt bei Stille)... Sprich JETZT!")
    subprocess.run(["termux-microphone-record", "-f", REC, "-e", "aac",
                    "-r", "16000", "-l", str(sekunden)], capture_output=True)

    t0 = time.time()
    frueh_gestoppt = False
    gesprochen = False
    while time.time() - t0 < sekunden + 1:
        time.sleep(1.0)
        if not os.path.exists(REC) or os.path.getsize(REC) < 2000:
            continue
        if not gesprochen:
            gesprochen = _hat_sprache(REC)
            continue
        still, dauer = _stille_am_ende(REC)
        if still and dauer >= 2.5:
            log_phase("Stille erkannt nach " + str(round(time.time()-t0,1)) + "s - stoppe frueher")
            frueh_gestoppt = True
            break

    subprocess.run(["termux-microphone-record", "-q"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)

    size = os.path.getsize(REC) if os.path.exists(REC) else 0
    gespart = ""
    if frueh_gestoppt:
        gespart = " (" + str(round(sekunden - (time.time()-t0), 1)) + "s gespart)"
    log_phase("Aufnahme beendet. " + str(size) + " Bytes" + gespart)

    if size < 1000:
        log_phase("WARNUNG: Aufnahme zu klein.")
        return False
    return True

async def main():
    log_phase("=== JACK HEY START ===")
    
    if not aufnehmen(SEKUNDEN):
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
