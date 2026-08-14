#!/usr/bin/env python3
"""
jack_context_ingest.py - Ingestion pipeline for ChatGPT/Claude/MD exports.
Cleans HTML, filters short texts (<80 chars), deduplicates via MD5, inserts into SQLite.
"""
import os
import sys
import json
import re
import hashlib
import sqlite3

DB_PATH = os.path.expanduser("~/jack/jack_memory.db")

def clean_text(raw_text):
    if not raw_text:
        return ""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', raw_text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def init_db(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingested_context (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE,
            source TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

def process_chatgpt(json_data):
    extracted = []
    for conv in json_data:
        title = conv.get('title', 'Untitled')
        mapping = conv.get('mapping', {})
        for node_id, node in mapping.items():
            msg = node.get('message')
            if msg and msg.get('content') and msg.get('content').get('parts'):
                role = msg.get('author', {}).get('role', 'unknown')
                parts = msg.get('content', {}).get('parts', [])
                text_parts = [p for p in parts if isinstance(p, str)]
                full_text = " ".join(text_parts)
                cleaned = clean_text(full_text)
                if len(cleaned) >= 80:
                    extracted.append((f"chatgpt:{title}:{role}", cleaned))
    return extracted

def process_plain_text(text_content, source_name="text"):
    extracted = []
    chunks = re.split(r'\n\s*\n', text_content)
    for chunk in chunks:
        cleaned = clean_text(chunk)
        if len(cleaned) >= 80:
            extracted.append((source_name, cleaned))
    return extracted

def ingest_file(file_path, file_type="auto"):
    if not os.path.exists(file_path):
        print(f"[ERR] File not found: {file_path}")
        return

    print(f"[*] Ingesting {file_path}...")
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    extracted = []
    if file_type == "chatgpt" or file_path.endswith('.json'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    extracted = process_chatgpt(data)
        except Exception as e:
            print(f"[WARN] Failed JSON parse: {e}, falling back to plain text")

    if not extracted:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            extracted = process_plain_text(content, os.path.basename(file_path))

    added_count = 0
    skip_count = 0

    cursor = conn.cursor()
    for source, text in extracted:
        h = md5_hash(text)
        try:
            cursor.execute(
                "INSERT INTO ingested_context (hash, source, content) VALUES (?, ?, ?)",
                (h, source, text)
            )
            added_count += 1
        except sqlite3.IntegrityError:
            skip_count += 1

    conn.commit()
    conn.close()
    print(f"[OK] Ingestion complete: {added_count} added, {skip_count} deduplicated.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 jack_context_ingest.py <path_to_file> [type]")
        sys.exit(1)

    f_path = sys.argv[1]
    f_type = sys.argv[2] if len(sys.argv) > 2 else "auto"
    ingest_file(f_path, f_type)
