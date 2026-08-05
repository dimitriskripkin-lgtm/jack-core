import asyncio, os, sys, time, wave
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
PCM_IN = os.path.join(PREFIX, "tmp", "jack_voice_in.pcm")
WAV_OUT = os.path.join(PREFIX, "tmp", "jack_voice_out.wav")
CHUNK = 3200

async def main():
    if not os.path.exists(PCM_IN) or os.path.getsize(PCM_IN) < 1000:
        print("FEHLER: PCM-Eingabe fehlt oder zu klein. Erst Block A ausfuehren." + chr(10))
        return
    pcm = open(PCM_IN, "rb").read()
    client = genai.Client(api_key=API_KEY)
    config = types.LiveConnectConfig(response_modalities=["AUDIO"])
    out_chunks = []
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        for i in range(0, len(pcm), CHUNK):
            await session.send_realtime_input(
                audio=types.Blob(data=pcm[i:i+CHUNK], mime_type="audio/pcm;rate=16000"))
            await asyncio.sleep(0.1)
        await session.send_realtime_input(audio_stream_end=True)
        t_sent = time.perf_counter()
        first_ms = None
        async for message in session.receive():
            sc = getattr(message, "server_content", None)
            if sc is None:
                continue
            mt = getattr(sc, "model_turn", None)
            if mt is not None and getattr(mt, "parts", None):
                for p in mt.parts:
                    idat = getattr(p, "inline_data", None)
                    if idat is not None and getattr(idat, "data", None):
                        if first_ms is None:
                            first_ms = (time.perf_counter() - t_sent) * 1000
                        out_chunks.append(idat.data)
            if getattr(sc, "turn_complete", False):
                break
    if out_chunks:
        with wave.open(WAV_OUT, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
            w.writeframes(b"".join(out_chunks))
        f = f"{first_ms:.0f}" if first_ms else "keine"
        print(f"OK: ersteAntwort={f}ms, {len(out_chunks)} Audio-Chunks" + chr(10))
        print("WAV gespeichert: " + WAV_OUT + chr(10))
        print("Anhoeren mit: termux-media-player play " + WAV_OUT + chr(10))
    else:
        print("FEHLER: keine Audio-Antwort erhalten" + chr(10))

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.wait_for(main(), timeout=60))
    except asyncio.TimeoutError:
        print("TIMEOUT nach 60s" + chr(10))
