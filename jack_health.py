#!/data/data/com.termux/files/usr/bin/python3
"""Kurz-Health: Dienste, SSH, Heartbeats, Tune  # JACK_TUNE_HEALTH → jack_health_now.json"""
import json, subprocess, time
from pathlib import Path
H = Path("/data/data/com.termux/files/home/jack")

def sh(cmd, t=8):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return ((p.stdout or "") + (p.stderr or "")).strip()
    except Exception as e:
        return str(e)

def main():
    health = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sv": sh("sv status /data/data/com.termux/files/usr/var/service/jack_* 2>/dev/null"),
        "ssh_xiaomi": "OK" if "OK" in sh("ssh -o ConnectTimeout=4 -o BatchMode=yes xiaomi-jack 'echo OK'") else "DOWN",
        "heartbeats": {},
    }
    for f in H.glob(".heartbeat_*"):
        health["heartbeats"][f.name.replace(".heartbeat_", "")] = round(time.time() - f.stat().st_mtime, 1)
    try:
        tj = H / "jack_tune.json"
        health["tune"] = json.loads(tj.read_text()) if tj.is_file() else None
    except Exception:
        health["tune"] = None
    health["marks"] = {}
    for rel, mark in (("jack_hey.py","JACK_TUNE_NC"),("jack_voice.py","JACK_TUNE_NC"),("jack_publish.py","JACK_TUNE_HASH"),("jack_autolearn_loop.py","JACK_TUNE_PAUSE")):
        p = H / rel
        health["marks"][rel] = (mark in p.read_text(encoding="utf-8", errors="ignore")) if p.is_file() else False
    out = H / "jack_health_now.json"
    out.write_text(json.dumps(health, indent=2, ensure_ascii=False))
    print(json.dumps({k: health[k] for k in ("ts", "ssh_xiaomi", "heartbeats", "tune", "marks")}, ensure_ascii=False))
    return 0 if health["ssh_xiaomi"] == "OK" else 1

if __name__ == "__main__":
    raise SystemExit(main())
