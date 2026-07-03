#!/usr/bin/env python3
import json, subprocess, os, sqlite3
from datetime import datetime
from pathlib import Path

JACK_HOME = "/data/data/com.termux/files/home"
MEMORY_DB = f"{JACK_HOME}/jack/jack_memory.db"
IDENTITY_FILE = f"{JACK_HOME}/jack/jack_identity.json"
HANDSHAKE_FILE = f"{JACK_HOME}/jack/jack_handshake.json"

def load_identity():
    try:
        with open(IDENTITY_FILE) as f:
            return json.load(f)
    except:
        return {}

def get_recent_errors(limit=5):
    try:
        with sqlite3.connect(MEMORY_DB) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute("SELECT * FROM errors ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]
    except:
        return []

def get_last_screenshot():
    path = f"{JACK_HOME}/xiaomi_screen.png"
    if os.path.exists(path):
        stat = os.stat(path)
        return {"path": path, "size": stat.st_size, "mtime": datetime.fromtimestamp(stat.st_mtime).isoformat()}
    return None

def get_system_status():
    try:
        result = subprocess.run("curl -s http://192.168.178.154:8081/api/status", shell=True, capture_output=True, text=True, timeout=5)
        return json.loads(result.stdout) if result.returncode == 0 else {}
    except:
        return {}
def generate_handshake():
    handshake = {
        "timestamp": datetime.now().isoformat(),
        "identity": load_identity(),
        "recent_errors": get_recent_errors(5),
        "last_screenshot": get_last_screenshot(),
        "xiaomi_status": get_system_status(),
        "ready": True
    }
    with open(HANDSHAKE_FILE, 'w') as f:
        json.dump(handshake, f, indent=2)
    return handshake

if __name__ == "__main__":
    hs = generate_handshake()
    print("[HANDSHAKE] ✓ Generated")
    print(json.dumps(hs, indent=2))
