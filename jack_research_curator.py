#!/usr/bin/env python3
import os
import sys
import sqlite3

JACK_DIR = os.path.expanduser("~/jack")
sys.path.insert(0, JACK_DIR)

import jack_web_ingest

DB_PATH = os.path.expanduser("~/jack/jack_memory.db")

def init_curated_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS curated_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_url TEXT,
            topic TEXT,
            summary TEXT,
            code_snippets TEXT,
            relevance_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def distill_and_store(url, topic):
    # Liest die frisch geholten Chunks aus ingested_context und fasst sie zusammen
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM ingested_context WHERE source LIKE ? ORDER BY id DESC LIMIT 10", (f"%{url}%",))
    rows = cursor.fetchall()
    
    if not rows:
        print(f"[CURATOR] Keine Chunks für {url} in DB gefunden.")
        conn.close()
        return False

    raw_chunks = [r[0] for r in rows]
    combined_text = "\n\n".join(raw_chunks)
    
    # Destillations-Schritt: Nimm die prägnantesten Aussagen
    clean_lines = [line.strip() for line in combined_text.splitlines() if len(line.strip()) > 30]
    compact_summary = f"Thema: {topic}\nQuelle: {url}\n\nKernaussagen:\n" + "\n".join(clean_lines[:12])

    cursor.execute('''
        INSERT INTO curated_knowledge (source_url, topic, summary, relevance_score)
        VALUES (?, ?, ?, ?)
    ''', (url, topic, compact_summary[:1500], 5))
    conn.commit()
    conn.close()

    print(f"[OK] Kuriertes Wissen erfolgreich synthetisiert und gespeichert! ({len(compact_summary)} Zeichen)")
    return True

def run_curated_research(url, topic):
    print(f"[RESEARCH] Starte kurierte Recherche für: {topic} ({url})...")
    success = jack_web_ingest.fetch_and_ingest_url(url, source_label="curator_raw")
    if success:
        return distill_and_store(url, topic)
    else:
        print(f"[ERR] Fehler beim Ingest von {url}")
        return False

if __name__ == "__main__":
    init_curated_db()
    run_curated_research("https://wiki.termux.com/wiki/Python", "Termux Python Environment")
