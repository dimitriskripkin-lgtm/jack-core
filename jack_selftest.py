#!/usr/bin/env python3
"""jack_selftest.py — Ein Kommando, kompletter JACK-Systemcheck."""
MODULE_VERSION = 1

import os, sys, time, json
JACK = os.path.expanduser("~/jack")
sys.path.insert(0, JACK)

results = {}

def chk(name, fn):
    try:
        t0 = time.time()
        ok, info = fn()
        ms = int((time.time()-t0)*1000)
        results[name] = {"ok": ok, "info": str(info)[:80], "ms": ms}
    except Exception as e:
        results[name] = {"ok": False, "info": str(e)[:80], "ms": 0}

# Services
def _svcs():
    import subprocess
    SVCS = ["jack_cortex","jack_telegram","jack_waechter","jack_autolearn","jack_publisher","jack_missions"]
    dead = []
    for s in SVCS:
        r = subprocess.run(["sv","status",s], capture_output=True, text=True, timeout=5)
        if "run:" not in r.stdout: dead.append(s)
    return len(dead)==0, f"{len(SVCS)-len(dead)}/{len(SVCS)} laufen" + (f" DEAD:{dead}" if dead else "")

# Xiaomi SSH
def _xiaomi():
    import jack_heartbeat
    ok = jack_heartbeat.is_xiaomi_alive()
    return ok, "SSH-Port erreichbar" if ok else "SSH-Port TOT"

# Ollama HTTP
def _ollama():
    """Prüft ob Ollama startbar ist — nicht ob er läuft (by-design off)."""
    try:
        import jack_heartbeat
        if not jack_heartbeat.is_xiaomi_alive():
            return False, "SSH tot — Gate nicht erreichbar"
        import subprocess
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             "xiaomi-jack", "ls /data/data/com.termux/files/usr/bin/ollama"],
            capture_output=True, text=True, timeout=8)
        if r.returncode == 0:
            return True, "Binary OK, Gate bereit (off by design)"
        return False, "Binary nicht gefunden"
    except Exception as e:
        return False, str(e)[:60]

# Graph
def _graph():
    import jack_graph as _g
    r = _g.recall("Dima")
    return bool(r), f"{len((r or '').splitlines())} Einträge"

# Heartbeats
def _beats():
    import jack_heartbeat
    SVCS = ["jack_cortex","jack_telegram","jack_waechter","jack_autolearn"]
    stale = []
    for s in SVCS:
        a = jack_heartbeat.age(s)
        if a is None or a > 600: stale.append(s)
    return len(stale)==0, f"{len(SVCS)-len(stale)}/{len(SVCS)} frisch" + (f" STALE:{stale}" if stale else "")

# Missions
def _missions():
    p = os.path.join(JACK,"missions","pending")
    d = os.path.join(JACK,"missions","done")
    f = os.path.join(JACK,"missions","fail")
    pending = len(os.listdir(p)) if os.path.exists(p) else 0
    done = len(os.listdir(d)) if os.path.exists(d) else 0
    fail = len(os.listdir(f)) if os.path.exists(f) else 0
    return fail<25, f"pending={pending} done={done} fail={fail}"

# Config
def _config():
    cfg = os.path.join(JACK,"config.ini")
    return os.path.exists(cfg), "vorhanden" if os.path.exists(cfg) else "FEHLT"

chk("services", _svcs)
chk("xiaomi_ssh", _xiaomi)
chk("ollama", _ollama)
chk("graph", _graph)
chk("heartbeats", _beats)
chk("missions", _missions)
chk("config", _config)

# Auswertung
ok_n = sum(1 for v in results.values() if v["ok"])
total = len(results)
score = int(ok_n/total*100)

print(f"\n{'='*40}")
print(f"JACK SELFTEST — Score: {score}% ({ok_n}/{total})")
print(f"{'='*40}")
for name, r in results.items():
    sym = "✓" if r["ok"] else "✗"
    print(f"  {sym} {name:<16} {r['info']} ({r['ms']}ms)")
print(f"{'='*40}\n")

snap = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "score": score,
    "nodes": results
}
if __name__ == "__main__":
    json.dump(snap, open(os.path.join(JACK,"jack_diag_snapshot.json"),"w"), indent=2)
    print("Snapshot: ~/jack/jack_diag_snapshot.json")
    sys.exit(0 if score==100 else 1)
