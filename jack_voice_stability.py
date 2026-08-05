import asyncio, os, sys, time, statistics
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
RUNS = 5
CHUNK = 3200

async def one_run():
    pcm = open(PCM_IN, "rb").read()
    client = genai.Client(api_key=API_KEY)
    config = types.LiveConnectConfig(response_modalities=["AUDIO"])
    n_chunks = 0
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
                        n_chunks += 1
            if getattr(sc, "turn_complete", False):
                break
    return first_ms, n_chunks

async def main():
    if not os.path.exists(PCM_IN) or os.path.getsize(PCM_IN) < 1000:
        print("FEHLER: jack_voice_in.pcm fehlt. Erst Aufnahme erstellen." + chr(10)); return
    results, errors = [], []
    for i in range(1, RUNS + 1):
        try:
            first_ms, n_chunks = await asyncio.wait_for(one_run(), timeout=60)
            if first_ms is not None and n_chunks > 0:
                results.append(first_ms)
                print(f"RUN {i}: OK ersteAntwort={first_ms:.0f}ms chunks={n_chunks}" + chr(10))
            else:
                errors.append(f"RUN{i}:leer")
                print(f"RUN {i}: keine Audio-Antwort" + chr(10))
        except asyncio.TimeoutError:
            errors.append(f"RUN{i}:Timeout")
            print(f"RUN {i}: TIMEOUT 60s" + chr(10))
        except Exception as e:
            errors.append(f"RUN{i}:{type(e).__name__}")
            print(f"RUN {i}: FEHLER {type(e).__name__}: {str(e)[:120]}" + chr(10))
        await asyncio.sleep(1)
    print("-" * 44 + chr(10))
    if results:
        s = sorted(results)
        print(f"STATISTIK: {len(results)}/{RUNS} OK | min={s[0]:.0f} median={statistics.median(s):.0f} max={s[-1]:.0f} ms" + chr(10))
    else:
        print("STATISTIK: kein erfolgreicher Lauf" + chr(10))
    if errors:
        print("PROBLEME: " + ", ".join(errors) + chr(10))

if __name__ == "__main__":
    asyncio.run(main())
