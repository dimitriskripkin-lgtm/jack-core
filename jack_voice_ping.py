import asyncio, time, os, sys, statistics
from google import genai
from google.genai import types

SECRETS = os.path.expanduser("~/.jack_secrets")
API_KEY = ""
if os.path.exists(SECRETS):
    with open(SECRETS) as f:
        for line in f:
            if line.strip().startswith("export GEMINI_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
if not API_KEY:
    print("FEHLER: GEMINI_API_KEY fehlt in ~/.jack_secrets" + chr(10))
    sys.exit(1)

MODEL = "gemini-3.1-flash-live-preview"
RUNS = 10
ok_ms = []
probleme = []

async def one_run():
    client = genai.Client(api_key=API_KEY)
    config = types.LiveConnectConfig(response_modalities=["AUDIO"])
    t0 = time.perf_counter()
    async with client.aio.live.connect(model=MODEL, config=config) as session:
        conn_ms = (time.perf_counter() - t0) * 1000
        await session.send_client_content(
            turns=types.Content(role="user", parts=[types.Part(text="ping")]),
            turn_complete=True,
        )
        t_sent = time.perf_counter()
        first_ms = None
        async for message in session.receive():
            sc = getattr(message, "server_content", None)
            if sc is None:
                continue
            if first_ms is None:
                mt = getattr(sc, "model_turn", None)
                if mt is not None and getattr(mt, "parts", None):
                    for p in mt.parts:
                        idat = getattr(p, "inline_data", None)
                        if idat is not None and getattr(idat, "data", None):
                            first_ms = (time.perf_counter() - t_sent) * 1000
                            break
            if getattr(sc, "turn_complete", False):
                break
        return conn_ms, first_ms

async def main():
    for i in range(1, RUNS + 1):
        try:
            conn_ms, first_ms = await asyncio.wait_for(one_run(), timeout=30)
            if first_ms is None:
                probleme.append(f"RUN{i}:keineAntwort")
                print(f"RUN {i}: connect={conn_ms:.0f}ms KEINE Antwort" + chr(10))
            else:
                ok_ms.append(first_ms)
                print(f"RUN {i}: connect={conn_ms:.0f}ms erste_antwort={first_ms:.0f}ms" + chr(10))
        except asyncio.TimeoutError:
            probleme.append(f"RUN{i}:Timeout")
            print(f"RUN {i}: TIMEOUT 30s" + chr(10))
        except Exception as e:
            probleme.append(f"RUN{i}:{type(e).__name__}")
            print(f"RUN {i}: FEHLER {type(e).__name__}: {str(e)[:120]}" + chr(10))
        await asyncio.sleep(0.5)

    print("-" * 44 + chr(10))
    if ok_ms:
        s = sorted(ok_ms)
        print(f"STATISTIK: {len(ok_ms)}/{RUNS} OK | min={s[0]:.0f} median={statistics.median(s):.0f} max={s[-1]:.0f} ms" + chr(10))
        if s[-1] > 2000:
            print("WARNUNG: Ausreisser ueber 2000ms (Spike-Risiko)" + chr(10))
    else:
        print("STATISTIK: keine erfolgreiche Messung" + chr(10))
    if probleme:
        print("PROBLEME: " + ", ".join(probleme) + chr(10))

if __name__ == "__main__":
    asyncio.run(main())
