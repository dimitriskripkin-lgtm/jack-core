#!/usr/bin/env python3
"""JACK Voice Chat LIVE - Mehrere Turns, EINE durchgehende Session.
Gemini behaelt den Gespraechskontext ueber alle Turns.
Start: python3 ~/jack/jack_voice_chat_live.py [sekunden] [max_turns]
Beenden: Strg+C"""
import os, sys, subprocess, time, wave, asyncio
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

sys.path.append(os.path.expanduser("~/jack"))
import jack_voice_live as vl
from google.genai import types

PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
M4A = os.path.join(PREFIX, "tmp", "jack_live_in.m4a")
PCM = os.path.join(PREFIX, "tmp", "jack_live_in.pcm")
WAV = os.path.join(PREFIX, "tmp", "jack_live_out.wav")
CHUNK = 32768

def hole_bausteine():
    """Client und Config wie in jack_voice_live.single_attempt() gebaut."""
    from google import genai
    if not getattr(vl, "API_KEY", ""):
        print("FEHLER: API_KEY fehlt in jack_voice_live")
        sys.exit(1)
    client = genai.Client(api_key=vl.API_KEY)
    config = types.LiveConnectConfig(response_modalities=["AUDIO"])
    return client, vl.MODEL, config

def record(seconds):
    for f in (M4A, PCM):
        if os.path.exists(f):
            os.remove(f)
    subprocess.run(["termux-microphone-record", "-f", M4A, "-e", "aac",
                    "-r", "16000", "-l", str(seconds)], capture_output=True)
    time.sleep(seconds + 1)
    subprocess.run(["termux-microphone-record", "-q"], capture_output=True)
    time.sleep(1)

def convert():
    subprocess.run(["ffmpeg", "-y", "-i", M4A, "-ar", "16000", "-ac", "1",
                    "-f", "s16le", PCM], capture_output=True)

def play_blocking():
    try:
        size = os.path.getsize(WAV)
        dauer = max(1, int(size / 48000) + 1)
        subprocess.run(["termux-media-player", "play", WAV], capture_output=True)
        time.sleep(dauer)
    except Exception as _le:
        _jlog and _jlog.fehler("jack_voice_chat_live","unbenannt",_le)

async def ein_turn(session, nummer, seconds):
    print(chr(10) + "--- Turn " + str(nummer) + " --- SPRICH JETZT (" + str(seconds) + "s)")
    record(seconds)
    if not os.path.exists(M4A) or os.path.getsize(M4A) < 500:
        print("Keine Aufnahme erkannt, ueberspringe.")
        return False
    convert()
    if not os.path.exists(PCM) or os.path.getsize(PCM) < 1000:
        print("PCM-Konvertierung fehlgeschlagen, ueberspringe.")
        return False

    t0 = time.time()
    daten = open(PCM, "rb").read()
    for i in range(0, len(daten), CHUNK):
        await session.send_realtime_input(
            audio=types.Blob(data=daten[i:i+CHUNK], mime_type="audio/pcm;rate=16000"))
        await asyncio.sleep(0.01)
    await session.send_realtime_input(audio_stream_end=True)
    t_sent = time.time()
    send_ms = (t_sent - t0) * 1000

    chunks = []
    first_ms = None
    async for message in session.receive():
        sc = getattr(message, "server_content", None)
        if sc is not None:
            mt = getattr(sc, "model_turn", None)
            if mt is not None and getattr(mt, "parts", None):
                for part in mt.parts:
                    inl = getattr(part, "inline_data", None)
                    if inl is not None and getattr(inl, "data", None):
                        if first_ms is None:
                            first_ms = (time.time() - t0) * 1000
                        chunks.append(inl.data)
            if getattr(sc, "turn_complete", False):
                break

    if not chunks:
        print("Keine Antwort erhalten.")
        return False

    with wave.open(WAV, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        w.writeframes(b"".join(chunks))
    wait_ms = (first_ms or 0) - send_ms
    anzahl_sendungen = (len(daten) + CHUNK - 1) // CHUNK
    print("Gesamt " + str(int(first_ms or 0)) + "ms = Senden " + str(int(send_ms)) +
          "ms (" + str(anzahl_sendungen) + " Sendungen) + Gemini " + str(int(wait_ms)) + "ms")
    print(str(len(chunks)) + " Audio-Chunks empfangen. Spiele ab...")
    play_blocking()
    return True

async def main():
    seconds = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    max_turns = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    client, MODEL, config = hole_bausteine()

    print("Oeffne Live-Session (" + str(MODEL) + ")...")
    print("Session bleibt offen. Kontext bleibt erhalten. Strg+C zum Beenden." + chr(10))
    t_start = time.time()
    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            print("Session offen nach " + str(int((time.time()-t_start)*1000)) + "ms")
            for n in range(1, max_turns + 1):
                await ein_turn(session, n, seconds)
                laufzeit = int(time.time() - t_start)
                if laufzeit > 840:
                    print(chr(10) + "Session naehert sich dem 15-Min-Limit. Beende sauber.")
                    break
    except KeyboardInterrupt:
        print(chr(10) + "Abgebrochen.")
    except Exception as e:
        print("SESSION-FEHLER: " + str(e)[:200])
    print(chr(10) + "Session geschlossen nach " + str(int(time.time()-t_start)) + "s")

if __name__ == "__main__":
    asyncio.run(main())
