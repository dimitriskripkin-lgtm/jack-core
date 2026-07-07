#!/usr/bin/env python3
import os, sys, shutil, subprocess, sqlite3, argparse
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/jack"))
import jack_xiaomi

JACK_HOME = "/data/data/com.termux/files/home"
ERROR_DB = f"{JACK_HOME}/jack/jack_errors.db"
MEMORY_DB = f"{JACK_HOME}/jack/jack_memory.db"

def get_cortex_status():
    try:
        res = subprocess.run(["pgrep", "-f", "jack_cortex.py"], capture_output=True, text=True)
        return f"RUNNING (PID {res.stdout.strip()})" if res.stdout.strip() else "STOPPED"
    except:
        return "UNKNOWN"

def get_db_stats(db_path):
    if not os.path.exists(db_path):
        return "NOT FOUND"
    size_kb = os.path.getsize(db_path) / 1024
    try:
        with sqlite3.connect(db_path) as con:
            cursor = con.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            return f"{size_kb:.1f} KB ({len(tables)} Tabellen)"
    except:
        return f"{size_kb:.1f} KB (GEBLOCKT/ERR)"

def get_pending_errors():
    if not os.path.exists(ERROR_DB):
        return 0
    try:
        with sqlite3.connect(ERROR_DB) as con:
            cursor = con.execute("SELECT COUNT(*) FROM errors WHERE resolved = 0")
            return cursor.fetchone()[0]
    except:
        return "ERR"

def get_storage_info():
    try:
        total, used, free = shutil.disk_usage(JACK_HOME)
        return f"{used / (1024**3):.1f}GB / {total / (1024**3):.1f}GB ({free / (1024**3):.1f}GB frei)"
    except:
        return "UNKNOWN"

def main():
    ap = argparse.ArgumentParser()
    ap.parse_args()

    x_stats = jack_xiaomi.get_status()

    print("\n╔════════════════════════════════════════════════════")
    print(f"║ JACK HEALTH DASHBOARD — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("╠════════════════════════════════════════════════════")
    print(f"║ [NODE 01] Honor 8 (Lokal)")
    print(f"║   Speicher:    {get_storage_info()}")
    print(f"║   Cortex:      {get_cortex_status()}")
    print(f"║   Memory DB:   {get_db_stats(MEMORY_DB)}")
    print(f"║   Error DB:    {get_db_stats(ERROR_DB)}")
    print(f"║   Offene Bugs: {get_pending_errors()}")
    print("╠════════════════════════════════════════════════════")
    print(f"║ [NODE 02] Xiaomi 11T Pro")
    print(f"║   IP:          {x_stats.get('ip', 'N/A')}")
    print(f"║   Erreichbar:  {x_stats.get('reachable', 'N/A')}")
    print(f"║   Akku:        {x_stats.get('battery', 'N/A')}")
    print(f"║   Uptime:      {x_stats.get('uptime', 'N/A')}")
    print(f"║   Shizuku:     {'RUNNING' if x_stats.get('shizuku_running') else 'STOPPED'}")
    print("╚════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    main()
