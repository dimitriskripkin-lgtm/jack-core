#!/usr/bin/env python3
"""
JACK Vinted Radar - Eigenstaendiger Bot
Separater Telegram-Bot fuer Vinted-Suche.
"""
import sqlite3, os, sys, re, gzip, json, time, urllib.request
from datetime import datetime

DB = os.path.expanduser("~/jack/jack_vinted.db")
CONFIG = os.path.expanduser("~/jack/jack_vinted_config.json")

DEFAULT_CONFIG = {
    "bot_token": "DEIN_NEUER_BOT_TOKEN",
    "chat_id": "DEINE_CHAT_ID",
    "searches": [
        {"keyword": "Hugo Boss Shirt", "max_preis": 25, "min_preis": 0},
        {"keyword": "Nike Hoodie", "max_preis": 40, "min_preis": 0}
    ],
    "interval_minutes": 30,
    "aktiv": True
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Honor Magic5 Pro) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

def init():
    conn = sqlite3.connect(DB)
    conn.execute("""CREATE TABLE IF NOT EXISTS gesehen (
        id TEXT PRIMARY KEY,
        titel TEXT,
        preis TEXT,
        url TEXT,
        keyword TEXT,
        timestamp TEXT
    )""")
    conn.commit()
    conn.close()
    if not os.path.exists(CONFIG):
        json.dump(DEFAULT_CONFIG, open(CONFIG, "w"), indent=2, ensure_ascii=False)
        print(f"Config erstellt: {CONFIG}")
        print("Bitte bot_token und chat_id eintragen!")
        sys.exit(0)

def load_config():
    return json.load(open(CONFIG))

def notify(tok, cid, text):
    d = json.dumps({"chat_id": cid, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        data=d, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram Fehler: {e}")

def suche_vinted(keyword, max_preis=None, min_preis=0):
    import urllib.parse
    import urllib.parse
    q = urllib.parse.quote(keyword)
    url = f"https://www.vinted.de/vetements?search_text={q}&order=newest_first"
    if max_preis:
        url += f"&price_to={max_preis}"
    try:
        resp = urllib.request.urlopen(
            urllib.request.Request(url, headers=HEADERS), timeout=15
        )
        html = resp.read()
        if html[:2] == b"\x1f\x8b":
            html = gzip.decompress(html)
        html = html.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"Fetch Fehler: {e}")
        return []

    items = re.findall(
        r'alt="([^"]+\d+,\d+\s*€[^"]*)"[^>]*data-testid="product-item-id-(\d+)--image--img"',
        html
    )
    results = []
    for alt, item_id in items:
        preis_m = re.search(r'(\d+[.,]\d+)\s*€', alt)
        preis_str = preis_m.group(1).replace(",", ".") if preis_m else "0"
        preis_num = float(preis_str) if preis_m else 0
        if min_preis and preis_num < min_preis:
            continue
        titel = alt.split(",")[0].strip()
        preis_display = f"{preis_m.group(0)}" if preis_m else "VB"
        results.append({
            "id": item_id,
            "titel": titel[:100],
            "preis": preis_display,
            "preis_num": preis_num,
            "url": f"https://www.vinted.de/items/{item_id}"
        })
    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)
    return unique[:20]

def verarbeite(items, keyword, tok, cid):
    conn = sqlite3.connect(DB)
    neue = 0
    for item in items:
        if not conn.execute("SELECT id FROM gesehen WHERE id=?", (item["id"],)).fetchone():
            conn.execute(
                "INSERT INTO gesehen (id,titel,preis,url,keyword,timestamp) VALUES (?,?,?,?,?,?)",
                (item["id"], item["titel"], item["preis"], item["url"], keyword, datetime.now().isoformat())
            )
            msg = (f"Vinted Radar: {keyword}\n\n"
                   f"Titel: {item['titel']}\n"
                   f"Preis: {item['preis']}\n"
                   f"Link: {item['url']}")
            notify(tok, cid, msg)
            neue += 1
            time.sleep(1)
    conn.commit()
    conn.close()
    return neue

def run():
    init()
    cfg = load_config()
    if not cfg.get("aktiv"):
        print("Radar deaktiviert.")
        return
    tok = cfg["bot_token"]
    cid = cfg["chat_id"]
    if tok == "DEIN_NEUER_BOT_TOKEN":
        print("Config nicht ausgefuellt! Bitte jack_vinted_config.json bearbeiten.")
        return
    gesamt = 0
    for s in cfg.get("searches", []):
        keyword = s.get("keyword", "")
        items = suche_vinted(keyword, s.get("max_preis"), s.get("min_preis", 0))
        n = verarbeite(items, keyword, tok, cid)
        gesamt += n
        print(f"{keyword}: {len(items)} gefunden, {n} neu")
    print(f"Gesamt neu: {gesamt}")

if __name__ == "__main__":
    run()
