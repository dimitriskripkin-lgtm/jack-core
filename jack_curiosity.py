import time, subprocess, sqlite3, os, random
from datetime import datetime

H = "/data/data/com.termux/files/home/jack"
LOG = H + "/curiosity.log"
DB = H + "/jack_skills.db"
HOME = "/data/data/com.termux/files/home"
SSH = "/data/data/com.termux/files/usr/bin/ssh"
PAUSE = 1

def log(msg):
    line = "[%s] %s" % (datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def run(cmd, timeout=12):
    env = os.environ.copy()
    env["HOME"] = HOME
    env["PATH"] = "/data/data/com.termux/files/usr/bin"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
    out = ((r.stdout or "") + (r.stderr or ""))[-300:]
    return r.returncode, out

def candidates():
    c = sqlite3.connect(DB)
    rows = c.execute("SELECT name FROM skills WHERE state=? LIMIT 3", ("CANDIDATE",)).fetchall()
    c.close()
    return [r[0] for r in rows]

streak = {}
POOL = [
    ("tunnel", "curl -s -m 3 -o /dev/null -w %{http_code} http://127.0.0.1:11434/api/tags"),
    ("xiaomi_ssh", SSH + " -o BatchMode=yes -o ConnectTimeout=5 xiaomi-jack echo SSH_OK"),
    ("sv_core", "sv status jack_telegram jack_cortex jack_autolearn ssh_tunnel_ollama"),
    ("uptime", "uptime"),
    ("disk", "df -h /data/data/com.termux/files/home"),
    ("free", "free -m"),
    ("autolearn_tail", "tail -3 " + H + "/autolearn.log"),
]

def pick():
    weights = []
    for name, cmd in POOL:
        s = streak.get(name, 0)
        w = 1.0 if s <= 0 else max(0.15, 1.0 / (1 + s))
        weights.append(w)
    return random.choices(POOL, weights=weights, k=1)[0]

log("CURIOSITY START v2")
while True:
    cands = candidates()
    if cands:
        log("SELF-TASK skill-pending: %s" % ", ".join(cands))
    name, cmd = pick()
    log("SELF-TASK explore: %s (streak=%s)" % (name, streak.get(name, 0)))
    try:
        rc, out = run(cmd)
        ok = (rc == 0) and ("permission denied" not in out.lower()) and ("command not found" not in out.lower())
        if ok:
            streak[name] = streak.get(name, 0) + 1
        else:
            streak[name] = 0
            log("INTEREST fail on %s" % name)
        log("RESULT %s rc=%s ok=%s | %s" % (name, rc, ok, out.replace("\n", " ")[:180]))
    except Exception as e:
        streak[name] = 0
        log("FAIL %s %s" % (name, e))
    time.sleep(PAUSE)
