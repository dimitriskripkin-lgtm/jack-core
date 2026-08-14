#!/usr/bin/env python3
import os
import sqlite3
import json
import time

DB_PATH = os.path.expanduser("~/jack/jack_memory.db")

def run_consolidation():
    if not os.path.exists(DB_PATH):
        print("[WARN] DB path not found for consolidation.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Tabelle für synthetisiertes Langzeitwissen anlegen
    c.execute('''
        CREATE TABLE IF NOT EXISTS consolidated_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT,
            summary TEXT,
            source_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Un-synthetisierte Ingest-Einträge holen
    c.execute("SELECT id, source, content FROM ingested_context WHERE is_stale = 0 ORDER BY id DESC LIMIT 50")
    rows = c.fetchall()

    if len(rows) < 5:
        print("[INFO] Zu wenige neue Memories für Konsolidierung (< 5).")
        conn.close()
        return

    sources = set(r[1] for r in rows)
    total_len = sum(len(r[2]) for r in rows)

    summary_text = f"Synthetisiert aus {len(rows)} Memory-Blöcken. Quellen: {', '.join(list(sources)[:3])}. Gesamtzeichen: {total_len}."

    c.execute("INSERT INTO consolidated_knowledge (topic, summary, source_count) VALUES (?, ?, ?)",
              ("Auto-Synthesis", summary_text, len(rows)))

    conn.commit()
    conn.close()
    print(f"[OK] Memory Consolidation abgeschlossen: {len(rows)} Items verarbeitet.")

if __name__ == "__main__":
    run_consolidation()
