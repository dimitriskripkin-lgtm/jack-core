#!/usr/bin/env python3
import os, sys, shutil, subprocess, sqlite3, argparse
from datetime import datetime

JACK_HOME = "/data/data/com.termux/files/home"
ERROR_DB = f"{JACK_HOME}/jack/jack_errors.db"
MEMORY_DB = f"{JACK_HOME}/jack/jack_memory.db"
XIAOMI_IP = "192.168.178.154"

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

def connect_adb(port):
    print(f"[ADB] Verbindungsversuch mit {XIAOMI_IP}:{port}...")
    try:
        res = subprocess.run(["adb", "connect", f"{XIAOMI_IP}:{port}"], capture_output=True, text=True)
        print(f"[ADB] {res.stdout.strip()}")
    except:
        print("[ADB] Fehler: Ist 'android-tools' in Termux installiert?")

def get_xiaomi_node_stats():
    stats = {"status": "OFFLINE", "storage": "N/A", "shizuku": "N/A"}
    
    # 1. Ping Check
    try:
        ping_res = subprocess.run(["ping", "-c", "1", "-W", "1", XIAOMI_IP], capture_output=True)
        if ping_res.returncode != 0:
            return stats
        stats["status"] = "ONLINE (Ping ok)"
    except:
        stats["status"] = "PING ERROR"
        return stats

    # 2. ADB Check & Abfrage
    try:
        devices_res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        device_id = None
        for line in devices_res.stdout.split("\n"):
            if XIAOMI_IP in line and "device" in line:
                device_id = line.split()[0]
                break
        
        if device_id:
            stats["status"] = f"CONNECTED ({device_id})"
            
            # Speicher vom Xiaomi holen (Zeilenbasiert parsen ohne String-Filter)
            df_res = subprocess.run(["adb", "-s", device_id, "shell", "df", "-h", "/data"], capture_output=True, text=True)
            lines = [l.strip() for l in df_res.stdout.split("\n") if l.strip()]
            if len(lines) >= 2:
                p = lines[1].split()
                if len(p) >= 4:
                    stats["storage"] = f"{p[2]} / {p[1]} ({p[3]} frei)"
            
            # Shizuku Prozess auf Xiaomi prüfen
            ps_res = subprocess.run(["adb", "-s", device_id, "shell", "ps", "-A"], capture_output=True, text=True)
            if "shizuku" in ps_res.stdout.lower():
                stats["shizuku"] = "RUNNING (Aktiv)"
            else:
                stats["shizuku"] = "STOPPED"
        else:
            stats["status"] = "ONLINE (ADB nicht gekoppelt)"
    except Exception as e:
        pass
        
    return stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--connect", type=int, help="Aktuellen ADB-WLAN-Port des Xiaomis übergeben")
    args = ap.parse_args()

    if args.connect:
        connect_adb(args.connect)

    x_stats = get_xiaomi_node_stats()

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
    print(f"║   Status:      {x_stats['status']}")
    print(f"║   Speicher:    {x_stats['storage']}")
    print(f"║   Shizuku:     {x_stats['shizuku']}")
    print("╚════════════════════════════════════════════════════\n")

if __name__ == "__main__":
    main()
