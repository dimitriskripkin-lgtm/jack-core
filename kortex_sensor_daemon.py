#!/usr/bin/env python3
"""
KORTEX Sensor Daemon (Simplified für Termux)
"""

import sqlite3
import json
import time
from datetime import datetime
import os

DB_PATH = os.path.expanduser("~/jack/kortex_sensors.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gps
                 (timestamp TEXT, lat REAL, lon REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bluetooth
                 (timestamp TEXT, device_count INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ambient
                 (timestamp TEXT, db_level REAL)''')
    conn.commit()
    conn.close()
    print(f"[KORTEX] DB initialized: {DB_PATH}")

def store_data(table, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    if table == "gps":
        c.execute("INSERT INTO gps VALUES (?,?,?)", (timestamp, data.get("lat"), data.get("lon")))
    elif table == "bluetooth":
        c.execute("INSERT INTO bluetooth VALUES (?,?)", (timestamp, data.get("count", 0)))
    elif table == "ambient":
        c.execute("INSERT INTO ambient VALUES (?,?)", (timestamp, data.get("db", 45.0)))
    
    conn.commit()
    conn.close()

def main():
    print("[KORTEX] Sensor Daemon started")
    print(f"[KORTEX] DB: {DB_PATH}")
    
    init_db()
    
    cycle = 0
    while True:
        cycle += 1
        now = datetime.now().isoformat()
        
        # Dummy GPS (later: integrate with actual location)
        store_data("gps", {"lat": 51.456, "lon": 7.012})
        print(f"[{now}] Cycle {cycle}: GPS logged")
        
        # Dummy Bluetooth
        store_data("bluetooth", {"count": 3})
        print(f"[{now}] Cycle {cycle}: BT scan logged")
        
        # Dummy Ambient
        store_data("ambient", {"db": 45.0})
        print(f"[{now}] Cycle {cycle}: Ambient logged")
        
        time.sleep(50)

if __name__ == "__main__":
    main()
