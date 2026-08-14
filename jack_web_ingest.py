#!/usr/bin/env python3
import os
import sys
import urllib.request
import re
import sqlite3
from html.parser import HTMLParser

JACK_DIR = os.path.expanduser("~/jack")
sys.path.insert(0, JACK_DIR)

import jack_context_ingest as ingest

class HTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []

    def handle_starttag(self, tag, attrs):
        if tag in ['p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'li']:
            self.fed.append("\n\n")

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def clean_html(raw_html):
    raw_html = re.sub(r'<script.*?>.*?</script>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    raw_html = re.sub(r'<style.*?>.*?</style>', '', raw_html, flags=re.DOTALL | re.IGNORECASE)
    
    parser = HTMLCleaner()
    parser.feed(raw_html)
    text = parser.get_data()
    
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]
    raw_text = '\n'.join(lines)
    clean_text = re.sub(r'\n{3,}', '\n\n', raw_text).strip()
    return clean_text

def fetch_and_ingest_url(url, source_label="web_ingest"):
    print(f"[FETCH] Lade Inhalt von: {url}...")
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Android; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0'}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            clean_text = clean_html(html)
            
            if len(clean_text) < 100:
                print("[WARN] Inhalt zu kurz oder geblockt.")
                return False
                
            print(f"[CLEAN] {len(clean_text)} Zeichen bereinigt. Starte Ingest...")
            
            extracted = ingest.process_plain_text(clean_text, source_name=f"{source_label}:{url}")
            if not extracted:
                print("[WARN] Keine Chunks >= 80 Zeichen extrahiert.")
                return False

            conn = sqlite3.connect(ingest.DB_PATH)
            ingest.init_db(conn)
            cursor = conn.cursor()
            
            added_count = 0
            skip_count = 0

            for source, text in extracted:
                h = ingest.md5_hash(text)
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
            return True

    except Exception as e:
        print(f"[ERR] Fehler beim Web-Ingest: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        fetch_and_ingest_url(target_url)
    else:
        print("Usage: python3 jack_web_ingest.py <URL>")
