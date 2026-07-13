#!/usr/bin/env python3
"""
JACK Gedaechtnis-Wartung
Laeuft taeglich. Markiert veraltete Eintraege, bereinigt Duplikate.
"""
import sqlite3, os, json
from datetime import datetime, timedelta

DB = os.path.expanduser("~/jack/kortex_memory.db")

def run():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    bericht = []

    # Stale-Marking: access_count=0 und aelter als 7 Tage
    grenze = (datetime.now() - timedelta(days=7)).isoformat()
    c.execute("""UPDATE memories SET tags = tags || ' stale'
        WHERE access_count = 0
        AND timestamp < ?
        AND tags NOT LIKE '%stale%'
        AND importance < 8""", (grenze,))
    stale = c.rowcount
    if stale > 0:
        bericht.append(f"{stale} Eintraege als 'stale' markiert")

    # Wichtige Eintraege (importance>=8) nie stale
    c.execute("UPDATE memories SET tags = REPLACE(tags, ' stale', '') WHERE importance >= 8")

    # Statistik
    total = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    stale_total = c.execute("SELECT COUNT(*) FROM memories WHERE tags LIKE '%stale%'").fetchone()[0]
    bericht.append(f"Gesamt: {total} Eintraege | Stale: {stale_total}")

    conn.commit()
    conn.close()

    import jack_log
    jack_log.log_decision("MEMORY-MAINTENANCE", " | ".join(bericht))
    return " | ".join(bericht)

if __name__ == "__main__":
    print(run())
