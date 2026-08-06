#!/usr/bin/env python3
import os, sys, subprocess, time, wave, asyncio
sys.path.append(os.path.expanduser("~/jack"))
from jack_voice_live import voice_roundtrip

PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
M4A = os.path.join(PREFIX, "tmp", "jack_chat_in.m4a")
PCM = os.path.join(PREFIX, "tmp", "jack_chat_in.pcm")
WAV_OUT = os.path.join(PREFIX, "tmp", "jack_chat_out.wav")

def record(seconds):
    for f in (M4A, PCM):
        if os.path.exists(f):
            os.remove(f)
    subprocess.run(["termux-microphone-record", "-f", M4A, "-e", "aac", "-r", "16000", "-l", str(seconds)], capture_output=True)
    time.sleep(seconds + 1)
    subprocess.run(["termux-microphone-record", "-q"], capture_output=True)
    time.sleep(1)

def convert():
    subprocess.run(["ffmpeg", "-y", "-i", M4A, "-ar", "16000", "-ac", "1", "-f", "s16le", PCM], capture_output=True)

def play_blocking():
    try:
        size = os.path.getsize(WAV_OUT)
        seconds = max(1, int(size / 48000) + 1)
        subprocess.run(["termux-media-player", "play", WAV_OUT], capture_output=True)
        time.sleep(seconds)
    except Exception:
        pass

async def main():
    seconds = 5
    if len(sys.argv) > 1:
        try:
            seconds = int(sys.argv[1])
        except Exception:
            seconds = 5
    print("Bitte JETZT sprechen. Aufnahme laeuft " + str(seconds) + " Sekunden." + chr(10))
    record(seconds)
    if not os.path.exists(PCM) or os.path.getsize(PCM) < 1000:
        print("FEHLER: keine verwertbare Aufnahme. Nochmal versuchen." + chr(10))
        return
    convert()
    if not os.path.exists(PCM) or os.path.getsize(PCM) < 1000:
        print("FEHLER: PCM-Konvertierung fehlgeschlagen." + chr(10))
        return
    print("Sende an Gemini Live..." + chr(10))
    first_ms, chunks = await voice_roundtrip(PCM)
    if not chunks:
        print("FEHLER: keine Antwort erhalten. Details im Log." + chr(10))
        return
    with wave.open(WAV_OUT, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        w.writeframes(b"".join(chunks))
    print("Antwort nach " + str(int(first_ms)) + "ms. Spiele ab..." + chr(10))
    play_blocking()
    print("Fertig. Fuer den naechsten Satz das Skript erneut starten." + chr(10))

if __name__ == "__main__":
    asyncio.run(main())
