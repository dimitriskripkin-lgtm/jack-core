#!/usr/bin/env python3
import os, base64, json, subprocess, urllib.request

H = "/data/data/com.termux/files/home/jack"
HOME = "/data/data/com.termux/files/home"
SSH = "/data/data/com.termux/files/usr/bin/ssh"
OUT = H + "/xiaomi_shot.png"
LOG = H + "/vision_once.log"

def log(m):
    print(m, flush=True)
    open(LOG, "a").write(m + "\n")

def sh(cmd, timeout=30):
    env = os.environ.copy()
    env["HOME"] = HOME
    env["PATH"] = "/data/data/com.termux/files/usr/bin"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

def capture():
    # Screenshot auf Xiaomi
    sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "su -c \'screencap -p /sdcard/jack_shot.png\'"' % SSH)
    # nach Honor ziehen
    rc, _ = sh("%s -o BatchMode=yes xiaomi-jack cat /sdcard/jack_shot.png > %s" % (SSH, OUT))
    sz = os.path.getsize(OUT) if os.path.isfile(OUT) else 0
    log("SHOT size=%d path=%s rc=%s" % (sz, OUT, rc))
    return sz > 1000

def load_key():
    # 1) Bridge (bewiesen beim Curl-Lauf)
    try:
        import sys
        sys.path.insert(0, H)
        import jack_groq_bridge as groq
        k = groq.load_key()
        if k:
            return k
    except Exception:
        pass
    # 2) absoluter Pfad, kein Tilde
    for path in (
        "/data/data/com.termux/files/home/.jack_secrets",
        os.path.join(HOME, ".jack_secrets"),
    ):
        try:
            for l in open(path):
                if "GROQ_API_KEY" in l and "=" in l:
                    return l.split("=", 1)[1].strip().strip(chr(34)+chr(39))
        except Exception:
            pass
    return os.environ.get("GROQ_API_KEY", "")

def vision_groq(png_path):
    key = load_key()
    if not key:
        return "Kein GROQ_API_KEY"
    b64 = base64.b64encode(open(png_path, "rb").read()).decode()
    # Groq vision-faehiges Modell (falls Account es hat)
    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Du bist JACK. Beschreibe auf Deutsch kurz was auf dem Handy-Screen zu sehen ist. Liste klickbare Elemente und was der naechste sinnvolle Schritt waere (max 10 Saetze)."},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + b64}},
            ],
        }],
        "max_tokens": 500,
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:
        return "Vision-API Fehler: %s (Screenshot liegt unter %s)" % (e, png_path)

def main():
    log("=== VISION ONCE ===")
    if not capture():
        log("Screenshot fehlgeschlagen")
        return
    ans = vision_groq(OUT)
    log("--- BESCHREIBUNG ---")
    log(ans)
    open(H + "/learned_vision_last.txt", "w").write(ans)
    log("SAVED learned_vision_last.txt")
    log("=== ENDE ===")

if __name__ == "__main__":
    main()
