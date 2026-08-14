#!/usr/bin/env python3
import os
import sqlite3
import time

DB_PATH = os.path.expanduser("~/jack/jack_memory.db")

def mark_stale_memories(days_threshold=30):
    if not os.path.exists(DB_PATH):
        print("[WARN] jack_memory.db nicht gefunden.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Sicherstellen, dass is_stale Spalte existiert
    try:
        cursor.execute("ALTER TABLE ingested_context ADD COLUMN is_stale INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # Spalte existiert bereits
        
    cutoff_seconds = time.time() - (days_threshold * 86400)
    cursor.execute("""
        UPDATE ingested_context 
        SET is_stale = 1 
        WHERE strftime('%s', created_at) < ? AND is_stale = 0
    """, (cutoff_seconds,))
    
    updated = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"[OK] {updated} veraltete Einträge als 'stale' markiert.")

if __name__ == "__main__":
    mark_stale_memories()
