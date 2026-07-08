#!/usr/bin/env python3
"""
KORTEX Profiler
Analysiert Sensor-Daten, baut User-Profil
"""

import sqlite3
import json
from datetime import datetime, timedelta
import os

DB_PATH = os.path.expanduser("~/jack/kortex_sensors.db")
PROFILE_PATH = os.path.expanduser("~/jack/kortex_profile.json")

def analyze_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # GPS: Standorte
    c.execute("SELECT lat, lon, COUNT(*) as freq FROM gps GROUP BY lat, lon ORDER BY freq DESC LIMIT 5")
    top_locations = c.fetchall()
    
    # Bluetooth: Welche Devices sind immer da?
    c.execute("SELECT device_count, COUNT(*) as freq FROM bluetooth GROUP BY device_count ORDER BY freq DESC")
    bt_patterns = c.fetchall()
    
    # Ambient: Durchschnitt
    c.execute("SELECT AVG(db_level), MIN(db_level), MAX(db_level) FROM ambient")
    ambient_stats = c.fetchone()
    
    conn.close()
    
    profile = {
        "generated": datetime.now().isoformat(),
        "top_locations": [
            {"lat": loc[0], "lon": loc[1], "frequency": loc[2]}
            for loc in top_locations
        ],
        "bluetooth_patterns": [
            {"device_count": bt[0], "frequency": bt[1]}
            for bt in bt_patterns
        ],
        "ambient": {
            "avg_db": ambient_stats[0],
            "min_db": ambient_stats[1],
            "max_db": ambient_stats[2]
        }
    }
    
    with open(PROFILE_PATH, "w") as f:
        json.dump(profile, f, indent=2)
    
    print(f"[PROFILER] Profile updated: {PROFILE_PATH}")
    print(json.dumps(profile, indent=2))

if __name__ == "__main__":
    analyze_data()
