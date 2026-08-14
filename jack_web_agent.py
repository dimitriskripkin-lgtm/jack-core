#!/usr/bin/env python3
import os
import sys
import re
import json
import sqlite3
import urllib.request
import urllib.parse
from html.parser import HTMLParser

DB_PATH = os.path.expanduser("~/jack/jack_memory.db")

class SimpleHTMLCleaner(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.fed = []
        self.links = []
        
    def handle_data(self, d):
        self.fed.append(d)
        
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for name, value in attrs:
                if name == 'href':
                    self.links.append(value)

    def get_data(self):
        return ''.join(self.fed)

def fetch_page(url, timeout=10):
    headers = {'User-Agent': 'Mozilla/5.0 (Android; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            html = response.read().decode('utf-8', errors='ignore')
            return html
    except Exception as e:
        print(f"[ERR] Failed to fetch {url}: {e}")
        return None

def analyze_web_page(url):
    print(f"[*] Browsing to {url}...")
    html = fetch_page(url)
    if not html:
        return None

    parser = SimpleHTMLCleaner()
    parser.feed(html)
    text_content = re.sub(r'\s+', ' ', parser.get_data()).strip()
    links = list(set(parser.links))[:15] # Top 15 Links

    result = {
        "url": url,
        "content_length": len(text_content),
        "text_sample": text_content[:300],
        "extracted_links": links
    }

    # Speichern des Web-Rezepts in jack_memory.db
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS web_recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT,
                    url TEXT,
                    sample_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            domain = urllib.parse.urlparse(url).netloc
            c.execute("INSERT INTO web_recipes (domain, url, sample_text) VALUES (?, ?, ?)",
                      (domain, url, text_content[:300]))
            conn.commit()
            conn.close()
            print(f"[OK] Web-Rezept für Domain '{domain}' gespeichert.")
        except Exception as e:
            print(f"[WARN] DB logging failed: {e}")

    return result

if __name__ == "__main__":
    test_url = "https://news.ycombinator.com"
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    res = analyze_web_page(test_url)
    if res:
        print(f"[OK] Web Agent Erfolgreich. Text-Länge: {res['content_length']}, Links gefunden: {len(res['extracted_links'])}")
