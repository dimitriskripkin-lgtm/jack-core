#!/data/data/com.termux/files/usr/bin/python3
"""Kurz-Health: Dienste, SSH, Heartbeats → jack_health_now.json"""
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
    out = H / "jack_health_now.json"
    out.write_text(json.dumps(health, indent=2, ensure_ascii=False))
    print(json.dumps({k: health[k] for k in ("ts", "ssh_xiaomi", "heartbeats")}, ensure_ascii=False))
    return 0 if health["ssh_xiaomi"] == "OK" else 1

if __name__ == "__main__":
    raise SystemExit(main())
