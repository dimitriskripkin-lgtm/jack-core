import time, subprocess, os, re
from datetime import datetime

H = "/data/data/com.termux/files/home/jack"
LOG = H + "/anomaly.log"
HOME = "/data/data/com.termux/files/home"
PAUSE = 120
LOAD_LIMIT = 8.0

def log(msg):
    line = "[%s] %s" % (datetime.now().strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def run(cmd, timeout=15):
    env = os.environ.copy()
    env["HOME"] = HOME
    env["PATH"] = "/data/data/com.termux/files/usr/bin:/system/bin"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()

def get_load():
    rc, out = run("uptime")
    if rc != 0:
        return None, out
    # load average: 15.53, 15.37, 15.17
    if "load average:" not in out:
        return None, out
    part = out.split("load average:")[-1].strip()
    first = part.split(",")[0].strip()
    try:
        return float(first), out
    except ValueError:
        return None, out

def services_down():
    rc, out = run("sv status jack_telegram jack_cortex jack_autolearn ssh_tunnel_ollama")
    down = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("down:") or "want up" in line:
            down.append(line)
        # "run:" = ok
    return down, out

def who_eats_cpu():
    # Termux/Android: ps aux ist am robustesten
    rc, out = run("ps aux 2>/dev/null | sort -k3 -nr | head -15")
    if rc != 0 or not out:
        rc2, out2 = run("top -n 1 -b 2>/dev/null | head -25")
        return out2 or out
    return out

log("ANOMALY START limit=%.1f pause=%ss" % (LOAD_LIMIT, PAUSE))

while True:
    load, raw = get_load()
    down, sv_out = services_down()

    if load is None:
        log("WARN uptime unlesbar: %s" % (raw[:120],))
    else:
        log("OK load=%.2f" % load)

    if down:
        log("ANOMALY service: %s" % " | ".join(down))
        log("DETAIL sv: %s" % sv_out.replace("\n", " ")[:240])

    if load is not None and load >= LOAD_LIMIT:
        log("ANOMALY load=%.2f >= %.1f -> wer frisst CPU?" % (load, LOAD_LIMIT))
        top = who_eats_cpu()
        for line in (top or "").splitlines()[:12]:
            log("CPU %s" % line[:160])

    if (load is None or load < LOAD_LIMIT) and not down:
        log("ruhig")

    time.sleep(PAUSE)
