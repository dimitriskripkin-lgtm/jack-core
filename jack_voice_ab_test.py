#!/usr/bin/env python3
"""A/B-Test v4: feingranulares Logging pro Run, Abbruch nach erstem Chunk, flush=True.
Aufruf: python3 jack_voice_ab_test.py [pfad_zu_pcm]"""
import os, sys, time, asyncio
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
sys.path.append(os.path.expanduser("~/jack"))
import jack_voice_live as vl
from google import genai
from google.genai import types

PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
PCM = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PREFIX, "tmp", "jack_voice_in.pcm")
CHUNK = 32768
SLEEP = 0.01
RUNS = 3
START = time.time()

def log(msg):
    print(str(round(time.time() - START, 2)) + "s | " + msg, flush=True)

async def ein_run(api_key, model, pcm, nr):
    log("Run " + str(nr) + ": Verbinde Session...")
    t_conn = time.perf_counter()
    client = genai.Client(api_key=api_key)
    config = types.LiveConnectConfig(response_modalities=["AUDIO"])
    async with client.aio.live.connect(model=model, config=config) as session:
        log("Run " + str(nr) + ": Session offen nach " + str(int((time.perf_counter()-t_conn)*1000)) + "ms. Sende...")
        t0 = time.perf_counter()
        for i in range(0, len(pcm), CHUNK):
            await session.send_realtime_input(
                audio=types.Blob(data=pcm[i:i+CHUNK], mime_type="audio/pcm;rate=16000"))
            await asyncio.sleep(SLEEP)
        await session.send_realtime_input(audio_stream_end=True)
        t_sent = time.perf_counter()
        log("Run " + str(nr) + ": Gesendet in " + str(int((t_sent-t0)*1000)) + "ms. Warte auf ersten Chunk...")
        async for message in session.receive():
            sc = getattr(message, "server_content", None)
            if sc is None:
                continue
            mt = getattr(sc, "model_turn", None)
            if mt is not None and getattr(mt, "parts", None):
                for part in mt.parts:
                    inl = getattr(part, "inline_data", None)
                    if inl is not None and getattr(inl, "data", None):
                        first = time.perf_counter()
                        return (first-t0)*1000, (first-t_sent)*1000
        return None, None

async def main():
    if not os.path.exists(PCM) or os.path.getsize(PCM) < 1000:
        log("FEHLER: " + PCM + " fehlt oder zu klein.")
        return
    pcm = open(PCM, "rb").read()
    log("PCM: " + str(len(pcm)) + " Bytes = ca. " + str(round(len(pcm)/32000,1)) + "s Audio")
    api_key = getattr(vl, "API_KEY", None)
    if not api_key:
        log("FEHLER: API_KEY nicht in jack_voice_live gefunden.")
        return
    model = getattr(vl, "MODEL", "gemini-3.1-flash-live-preview")
    log("Modell: " + model + ", schnelles Pacing, " + str(RUNS) + " Runs")
    werte = []
    for r in range(1, RUNS + 1):
        try:
            erg = await asyncio.wait_for(ein_run(api_key, model, pcm, r), timeout=60)
            if erg[0] is not None:
                werte.append(erg[1])
                log("Run " + str(r) + ": abStreamEnde=" + str(int(erg[1])) + "ms")
            else:
                log("Run " + str(r) + ": keine Audio-Antwort.")
        except asyncio.TimeoutError:
            log("Run " + str(r) + ": TIMEOUT nach 60s.")
        except Exception as e:
            log("Run " + str(r) + ": FEHLER " + type(e).__name__ + " " + str(e)[:100])
        await asyncio.sleep(1)
    if werte:
        werte.sort()
        log("MEDIAN abStreamEnde (" + str(len(werte)) + " Runs): " + str(int(werte[len(werte)//2])) + "ms")
        log("Vergleich: 5.1s Einzel=2585ms, Mehr-Turn=2133ms, alter 3s-Test(langsames Pacing)=707ms.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(chr(10) + "Sauber abgebrochen.", flush=True)
