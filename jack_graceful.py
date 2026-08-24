#!/data/data/com.termux/files/usr/bin/python3
"""Wenn Xiaomi offline: aktive Mission pausieren, Telegram kurz informieren."""
import json, subprocess, time
from pathlib import Path
H = Path("/data/data/com.termux/files/home/jack")
ACTIVE = H / "jack_mission_active.json"
PAUSED = H / "jack_mission_paused.json"

def ssh_ok():
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=4",
             "xiaomi-jack", "echo", "OK"],
            capture_output=True, text=True, timeout=8,
        )
        return r.returncode == 0 and "OK" in ((r.stdout or "") + (r.stderr or ""))
    except Exception:
        return False

def notify(msg):
    try:
        subprocess.run(
            ["python3", "-c", "import jack_telegram; jack_telegram.send(%r)" % msg],
            cwd=str(H), timeout=15, capture_output=True,
        )
    except Exception:
        pass

def main():
    if ssh_ok():
        # Resume falls paused
        if PAUSED.is_file() and not ACTIVE.is_file():
            PAUSED.rename(ACTIVE)
            notify("GRACEFUL: Xiaomi wieder da – Mission fortgesetzt")
            print("RESUMED")
            return 0
        print("ONLINE")
        return 0
    # Offline
    if ACTIVE.is_file():
        ACTIVE.rename(PAUSED)
        notify("GRACEFUL: Xiaomi offline – Mission pausiert")
        print("PAUSED")
        return 1
    print("OFFLINE_NO_MISSION")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
