import json, os, time, subprocess, sys
H = os.path.expanduser("/data/data/com.termux/files/home/jack")
LOOP = H + "/jack_loop.json"
ALLOWED = ("status_snapshot", "verify_youtube", "play_sido_youtube", "commit_yt_sido")

def run(cmd, timeout=40):
    r = subprocess.run(cmd, cwd=H, capture_output=True, text=True, timeout=timeout)
    return r.returncode, ((r.stdout or "") + (r.stderr or ""))[-2000:]

def su_xiaomi(cmd):
    r = subprocess.run(["ssh", "xiaomi-jack", "su", "-c", cmd], capture_output=True, text=True, timeout=20)
    return (r.stdout or "") + (r.stderr or "")

def load():
    return json.load(open(LOOP, encoding="utf-8"))

def save(d):
    d["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S+02:00")
    json.dump(d, open(LOOP, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def status_snapshot():
    rc, sv = run(["sv", "status", "jack_telegram", "jack_cortex", "jack_waechter", "jack_autolearn", "ssh_tunnel_ollama"])
    rc2, mem = run(["free", "-h"])
    curl = subprocess.run(["curl", "-s", "-m", "4", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:11434/api/tags"], capture_output=True, text=True, timeout=8)
    return True, {"sv": sv[-800:], "mem": mem[-400:], "ollama_tunnel": (curl.stdout or "").strip()}

def verify_youtube():
    s = su_xiaomi("dumpsys media_session")
    foc = su_xiaomi("dumpsys window")
    playing = ("package=com.android.chrome" in s) and ("state=3" in s.replace(" ", ""))
    focus = "?"
    for ln in foc.splitlines():
        if "mCurrentFocus" in ln:
            focus = ln.strip()
            break
    return playing, {"playing": playing, "focus": focus}

def play_sido_youtube():
    py = H + "/jack_yt_sido.py"
    if not os.path.isfile(py):
        return False, {"error": "jack_yt_sido.py fehlt"}
    rc, out = run([sys.executable, py], timeout=180)
    return "ERFOLG" in out, {"rc": rc, "tail": out[-1500:]}

def commit_yt_sido():
    run(["git", "add", "jack_yt_sido.py", "jack_loop.py", "jack_loop.json"])
    rc, out = run(["git", "commit", "-m", "loop: yt sido plus handshake"])
    rc2, out2 = run(["git", "push"])
    return True, {"commit": out[-400:], "push": out2[-400:]}

TASKS = {
    "status_snapshot": status_snapshot,
    "verify_youtube": verify_youtube,
    "play_sido_youtube": play_sido_youtube,
    "commit_yt_sido": commit_yt_sido,
}

os.chdir(H)
d = load()
print("LOOP", d.get("id"), d.get("from"), d.get("status"), d.get("task"))
if d.get("from") != "grok" or d.get("status") != "open":
    print("nichts offen")
    raise SystemExit(0)
task = d.get("task")
if task not in ALLOWED:
    d["from"] = "jack"
    d["status"] = "blocked"
    d["result"] = {"error": "task nicht erlaubt"}
    save(d)
    raise SystemExit(2)
ok, result = TASKS[task]()
d["from"] = "jack"
d["status"] = "done" if ok else "fehler"
d["ok"] = bool(ok)
d["result"] = result
save(d)
run(["git", "add", "jack_loop.json", "jack_loop.py"])
run(["git", "commit", "-m", "loop: JACK result"])
prc, pout = run(["git", "push"])
print("RESULT", ok, "PUSH", prc, pout)
