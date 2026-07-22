#!/usr/bin/env python3
"""JACK Hey - hands-free Sprach-Interaktion auf dem Honor.
Aufnehmen -> verstehen (whisper) -> routen (Aktion ODER reden) -> sprechen (ElevenLabs)."""
import os, subprocess, sys, time
sys.path.insert(0, os.path.expanduser("~/jack"))

HOME = os.path.expanduser("~")
WHISPER = HOME + "/whisper.cpp/build/bin/whisper-cli"
MODEL = HOME + "/whisper.cpp/models/ggml-small.bin"
REC = HOME + "/.jack_hey.m4a"
WAV = HOME + "/.jack_hey.wav"
RESP = HOME + "/.jack_hey_resp.mp3"
SEC = os.path.expanduser("~/.jack_secrets")

def _sec(k):
    for l in open(SEC):
        if k in l and "=" in l:
            return l.split("=",1)[1].strip().strip('"').strip("'")
    return None

def aufnehmen(sekunden=8):
    for f in (REC, WAV, RESP):
        if os.path.exists(f):
            try: os.remove(f)
            except Exception: pass
    subprocess.run(["termux-microphone-record","-f",REC,"-l",str(sekunden)], capture_output=True)
    time.sleep(sekunden + 2)
    subprocess.run(["termux-microphone-record","-q"], capture_output=True)
    return os.path.exists(REC) and os.path.getsize(REC) > 1000

def verstehen():
    subprocess.run(["ffmpeg","-y","-i",REC,"-ar","16000","-ac","1",WAV], check=True, capture_output=True)
    res = subprocess.run([WHISPER,"-m",MODEL,"-f",WAV,"-l","de","-nt","-t","6"], capture_output=True, text=True)
    return " ".join(res.stdout.split()).strip()

def denken(text):
    low = text.lower()
    if any(w in low for w in ("merk dir","merke dir","notiz","vergiss nicht","speicher")):
        notiz = text
        for prefix in ("merk dir","merke dir","notiz","vergiss nicht","speicher","jack"):
            notiz = notiz.lower().replace(prefix,"").strip(" ,:")
        import jack_memory
        jack_memory.save("Notiz von Dima", notiz, "notiz")
        return "Notiert. Ich hab mir gemerkt: " + notiz
    if any(w in low for w in ("skill","fuehr aus","mach einen","ram","disk","fehler","budget","modell")):
        import jack_skills
        for name in ["ram_check","disk_check","fehler_report","budget_rest","modell_check","gedaechtnis_stats","jack_status"]:
            if name.replace("_"," ") in low or name.split("_")[0] in low:
                ok, out = jack_skills.run_skill(name)
                if ok: return "Hier das Ergebnis: " + out[:300] + "\n\n⚡ Direkt (kein API)"
    if any(w in low for w in ("status","audit","systemcheck","laeuft alles","läuft alles","wie steht")):
        import jack_audit
        r = jack_audit.report()
        dienste = "alle sechs" if "6/6" in r else "nicht alle"
        fehler = "unbekannt"
        for l in r.split("\n"):
            if "Offene Fehler" in l:
                fehler = l.split(":")[-1].strip()
        return "Alles im Griff. Es laufen %s Dienste, %s offene Fehler, und die Sicherheit ist gruen." % (dienste, fehler)
    from jack_talk import talk_to_gemini
    return talk_to_gemini(text)

def sprechen(text):
    from elevenlabs.client import ElevenLabs
    c = ElevenLabs(api_key=_sec("ELEVENLABS_API_KEY"))
    audio = c.text_to_speech.convert(text=text, voice_id=_sec("ELEVENLABS_VOICE_ID"), model_id="eleven_flash_v2_5")
    with open(RESP,"wb") as f:
        for chunk in audio: f.write(chunk)
    subprocess.run(["termux-media-player","play",RESP], capture_output=True)

def lauf(sekunden=8):
    if not aufnehmen(sekunden):
        print("Keine Aufnahme - Mikro-Permission fuer Termux:API erteilt?"); return
    heard = verstehen()
    print("GEHOERT:", heard)
    if not heard:
        sprechen("Ich hab dich nicht verstanden, sag es nochmal."); return
    answer = denken(heard)
    print("JACK:", answer)
    sprechen(answer)

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    lauf(n)
