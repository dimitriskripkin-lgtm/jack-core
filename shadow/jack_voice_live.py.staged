import asyncio, os, sys, time, wave
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
from datetime import datetime
from google import genai
from google.genai import types

SECRETS = os.path.expanduser("~/.jack_secrets")
API_KEY = ""
if os.path.exists(SECRETS):
    with open(SECRETS) as f:
        for line in f:
            if line.strip().startswith("export GEMINI_API_KEY="):
                API_KEY = line.split("=",1)[1].strip().strip('"').strip("'")
if not API_KEY:
    print("FEHLER: GEMINI_API_KEY fehlt in ~/.jack_secrets" + chr(10)); sys.exit(1)

MODEL = "gemini-3.1-flash-live-preview"
PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
CHUNK = 3200
MAX_RETRIES = 3
BASE_DELAY = 1.0
LOG_DIR = os.path.expanduser("~/jack/logs")
LOG_FILE = os.path.join(LOG_DIR, "voice_live.log")

def load_jack_context():
    """Lädt JACK-Persönlichkeit aus Context-Dateien."""
    parts = []
    for f in [os.path.expanduser("~/jack/jack_context.md"), os.path.expanduser("~/jack/jack_identity.json")]:
        try:
            if os.path.exists(f):
                with open(f) as fh:
                    parts.append(fh.read())
        except Exception as _le:
            _jlog and _jlog.fehler("jack_voice_live","unbenannt",_le)
    return chr(10).join(parts)[:6000]

SYSTEM_PROMPT = (
    "Du bist JACK, der Kumpel von Dima. Sprich IMMER Deutsch, kumpelhaft und direkt, "
    "per du, keine Hoeflichkeitsfloskeln, kein Sie, kein unterwuerfiger Ton. "
    "Du bist ein Freund auf Augenhoehe, kein Diener. Antworte kurz und knapp."
    + chr(10) + load_jack_context()
)

def log_event(etype, detail):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(ts + " | " + etype + " | " + detail + chr(10))
    except Exception as _le:
        _jlog and _jlog.fehler("jack_voice_live","unbenannt",_le)

async def single_attempt(pcm):
    client = genai.Client(api_key=API_KEY)
    config = types.LiveConnectConfig(response_modalities=["AUDIO"], system_instruction=SYSTEM_PROMPT)
    out_chunks = []
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        for i in range(0, len(pcm), CHUNK):
            await session.send_realtime_input(
                audio=types.Blob(data=pcm[i:i+CHUNK], mime_type="audio/pcm;rate=16000"))
            await asyncio.sleep(0.15)
        await session.send_realtime_input(audio_stream_end=True)
        t_sent = time.perf_counter()
        first_ms = None
        msg_count = 0
        async for message in session.receive():
            msg_count += 1
            sc = getattr(message, "server_content", None)
            if sc is None:
                continue
            mt = getattr(sc, "model_turn", None)
            if mt is not None and getattr(mt, "parts", None):
                for p in mt.parts:
                    idat = getattr(p, "inline_data", None)
                    if idat is not None and getattr(idat, "data", None):
                        if first_ms is None:
                            first_ms = max(1, int((time.perf_counter() - t_sent) * 1000))
                        out_chunks.append(idat.data)
            if getattr(sc, "turn_complete", False):
                break
    if not out_chunks:
        raise RuntimeError("leere Antwort erhalten")
    return first_ms, out_chunks

async def voice_roundtrip(pcm_path):
    pcm = open(pcm_path, "rb").read()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            first_ms, chunks = await asyncio.wait_for(single_attempt(pcm), timeout=60)
            log_event("OK", "attempt=" + str(attempt) + " first=" + str(int(first_ms)) + "ms chunks=" + str(len(chunks)))
            return first_ms, chunks
        except Exception as e:
            ename = type(e).__name__
            if attempt < MAX_RETRIES:
                log_event("RETRY", "attempt=" + str(attempt) + " err=" + ename + " " + str(e)[:100])
                delay = BASE_DELAY * (2 ** (attempt - 1))
                print("Retry " + str(attempt) + "/" + str(MAX_RETRIES) + " nach " + str(int(delay)) + "s (" + ename + ")" + chr(10))
                await asyncio.sleep(delay)
            else:
                log_event("FAIL", "attempt=" + str(attempt) + " err=" + ename + " " + str(e)[:100])
    return None, []

async def main():
    pcm_path = os.path.join(PREFIX, "tmp", "jack_voice_in.pcm")
    if not os.path.exists(pcm_path) or os.path.getsize(pcm_path) < 1000:
        print("FEHLER: jack_voice_in.pcm fehlt. Erst Aufnahme erstellen." + chr(10)); return
    first_ms, chunks = await voice_roundtrip(pcm_path)
    if chunks:
        wav_out = os.path.join(PREFIX, "tmp", "jack_voice_live_out.wav")
        with wave.open(wav_out, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(b"".join(chunks))
        print("OK: ersteAntwort=" + str(int(first_ms)) + "ms chunks=" + str(len(chunks)) + chr(10))
        print("WAV: " + wav_out + chr(10))
    else:
        print("FEHLER: alle Versuche fehlgeschlagen, Details im Log" + chr(10))
    print("Log: " + LOG_FILE + chr(10))

if __name__ == "__main__":
    asyncio.run(main())

async def voice_stream(pcm_path, callback):
    """Stream audio chunks in Echtzeit an eine Callback-Funktion.
    
    Args:
        pcm_path: Pfad zur PCM-Datei (16kHz, 16-bit, mono)
        callback: async Funktion die Audio-Chunks empfängt
    
    Returns:
        True bei Erfolg, False bei Fehler
    """
    pcm = open(pcm_path, "rb").read()
    if not API_KEY:
        return False
    
    client = genai.Client(api_key=API_KEY)
    config = types.LiveConnectConfig(response_modalities=["AUDIO"], system_instruction=SYSTEM_PROMPT)
    
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        # Audio an API senden
        for i in range(0, len(pcm), CHUNK):
            await session.send_realtime_input(
                audio=types.Blob(data=pcm[i:i+CHUNK], mime_type="audio/pcm;rate=16000"))
            await asyncio.sleep(0.01)
        
        await session.send_realtime_input(audio_stream_end=True)
        
        # Audio-Chunks in Echtzeit empfangen und an callback weiterleiten
        async for message in session.receive():
            sc = getattr(message, "server_content", None)
            if sc is None:
                continue
            
            mt = getattr(sc, "model_turn", None)
            if mt is not None and getattr(mt, "parts", None):
                for p in mt.parts:
                    idat = getattr(p, "inline_data", None)
                    if idat is not None and getattr(idat, "data", None):
                        # Audio-Chunk sofort an callback senden
                        await callback(idat.data)
            
            if getattr(sc, "turn_complete", False):
                break
        
        return True
