#!/usr/bin/env python3
import os, sys, time, signal, hashlib, sqlite3, argparse, subprocess
from datetime import datetime
try:
    from google import genai
    from google.genai import types
    GENAI_OK = True
except ImportError:
    GENAI_OK = False
JACK_HOME = "/data/data/com.termux/files/home"
MEMORY_DB = f"{JACK_HOME}/jack/jack_memory.db"
MODEL = "gemini-2.5-flash"
LOOP_SECS = 5
WATCH_SECS = 2
XIAOMI_USER = "u0_a69"
XIAOMI_IP = "192.168.178.154"
XIAOMI_SSH_PORT = "8022"
XIAOMI_TMP = "/data/local/tmp/jack_snap.png"
DEFAULT_PROMPT = "Du bist JACK. Analysiere: 1) App? 2) Was passiert? 3) Empfehlung? Kurz."
def capture_screen():
    try:
        subprocess.run(["ssh","-t","-p",XIAOMI_SSH_PORT,f"{XIAOMI_USER}@{XIAOMI_IP}",f"export RISH_APPLICATION_ID=com.termux && ~/rish -c '/system/bin/screencap -p {XIAOMI_TMP}'"],capture_output=True,timeout=20)
        r = subprocess.run(["ssh","-p",XIAOMI_SSH_PORT,f"{XIAOMI_USER}@{XIAOMI_IP}",f"cat {XIAOMI_TMP}"],capture_output=True,timeout=15)
        return r.stdout if r.returncode==0 and len(r.stdout)>500 else None
    except Exception as e:
        print(f"[CAP] {e}")
        return None
class VisionEngine:
    def __init__(self):
        key = os.environ.get("GEMINI_API_KEY")
        if not key:
            raise RuntimeError("[VISION] Key fehlt!")
        self.client = genai.Client(api_key=key)
    def analyze(self, png, prompt=DEFAULT_PROMPT):
        try:
            resp = self.client.models.generate_content(model=MODEL,contents=[types.Part.from_bytes(data=png,mime_type="image/png"),prompt])
            return resp.text.strip()
        except Exception as e:
            return f"[ERROR] {e}"
class MemoryWriter:
    def __init__(self):
        try:
            with sqlite3.connect(MEMORY_DB) as con:
                con.execute("CREATE TABLE IF NOT EXISTS vision_log (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, analysis TEXT, source TEXT DEFAULT 'jack_eyes')")
                con.commit()
        except:
            pass
    def save(self, analysis):
        try:
            with sqlite3.connect(MEMORY_DB) as con:
                con.execute("INSERT INTO vision_log (ts, analysis) VALUES (?, ?)",(datetime.now().isoformat(),analysis))
                con.commit()
        except:
            pass
class JackEyes:
    def __init__(self):
        self.mem = MemoryWriter()
        self._last_md5 = ""
        self._alive = True
        self.vision = None
        if GENAI_OK:
            try:
                self.vision = VisionEngine()
                print(f"[EYES] ✓ Gemini Vision aktiv ({MODEL})")
            except:
                pass
        signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
    def _changed(self, png):
        h = hashlib.md5(png).hexdigest()
        if h == self._last_md5: return False
        self._last_md5 = h
        return True
    def _process(self, png, force=False, prompt=None):
        if not force and not self._changed(png): return
        ts = datetime.now().strftime("%H:%M:%S")
        result = self.vision.analyze(png, prompt or DEFAULT_PROMPT) if self.vision else f"[KEIN MODEL] {len(png)} Bytes"
        print(f"\n╔═ JACK EYES [{ts}] [XIAOMI-SLAVE] ════")
        for line in result.splitlines():
            if line.strip(): print(f"║ {line}")
        print(f"╚══════════════════════════════════════")
        self.mem.save(result)
        subprocess.run(["termux-vibrate","-d","60"],capture_output=True)
    def single(self, prompt=None):
        print("[EYES] Einzelscan [XIAOMI-SLAVE] ...")
        png = capture_screen()
        if png: self._process(png, force=True, prompt=prompt)
        else: print("[EYES] Screenshot fehlgeschlagen.")
    def loop(self, interval=LOOP_SECS):
        print(f"[EYES] Loop | {interval}s | CTRL+C Stop")
        while self._alive:
            png = capture_screen()
            if png: self._process(png)
            time.sleep(interval)
    def watch(self, interval=WATCH_SECS):
        print(f"[EYES] Watch | {interval}s | CTRL+C Stop")
        while self._alive:
            png = capture_screen()
            if png and self._changed(png): self._process(png, force=True)
            time.sleep(interval)
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="single", choices=["single","loop","watch"])
    ap.add_argument("-i","--interval", type=int, default=None)
    ap.add_argument("-p","--prompt", type=str, default=None)
    args = ap.parse_args()
    eyes = JackEyes()
    if args.mode == "single": eyes.single(prompt=args.prompt)
    elif args.mode == "loop": eyes.loop(interval=args.interval or LOOP_SECS)
    elif args.mode == "watch": eyes.watch(interval=args.interval or WATCH_SECS)
