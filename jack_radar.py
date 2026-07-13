#!/usr/bin/env python3
"""
JACK Kleinanzeigen Radar
Durchsucht Kleinanzeigen.de nach Keywords, meldet neue Treffer per Telegram.
Speichert gesehene Anzeigen in SQLite um Duplikate zu vermeiden.
"""
import sqlite3, os, sys, json, time, hashlib, urllib.request, urllib.parse
from datetime import datetime

sys.path.insert(0, os.path.expanduser("~/jack"))
DB = os.path.expanduser("~/jack/jack_radar.db")
PROFILE = os.path.expanduser("~/jack/jack_radar_config.json")

DEFAULT_CONFIG = {
    "searches": [
        {"keyword": "ThinkCentre Mini PC", "max_preis": 100, "kategorie": "computer"},
        {"keyword": "Raspberry Pi", "max_preis": 80, "kategorie": "computer"}
    ],
    "interval_minutes": 30,
    "aktiv": True
}

def init_db():
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

def load_config():
    try:
        return json.load(open(PROFILE))
    except Exception:
        json.dump(DEFAULT_CONFIG, open(PROFILE, "w"), indent=2, ensure_ascii=False)
        return DEFAULT_CONFIG

def _sec(k):
    for l in open(os.path.expanduser("~/.jack_secrets")):
        if k in l and "=" in l:
            return l.split('"')[1] if '"' in l else l.split("=",1)[1].strip()

def notify(text):
    tok = _sec("TELEGRAM_BOT_TOKEN")
    cid = _sec("TELEGRAM_CHAT_ID")
    if not tok or not cid:
        return
    d = json.dumps({"chat_id": cid, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{tok}/sendMessage",
        data=d, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        import jack_log
        jack_log.log_decision("RADAR-NOTIFY-FEHLER", str(e)[:100])

def suche_kleinanzeigen(keyword, max_preis=None):
    """Sucht auf Kleinanzeigen.de und gibt Liste von Anzeigen zurueck."""
    q = urllib.parse.quote(keyword)
    url = f"https://www.kleinanzeigen.de/s-{q}/k0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9",
        "Accept": "text/html,application/xhtml+xml"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)
        html = resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        import jack_log
        jack_log.log_decision("RADAR-FETCH-FEHLER", f"{keyword}: {str(e)[:80]}")
        return []

    import re
    results = []
    parts = html.split('data-adid="')
    for part in parts[1:]:
        try:
            ad_id = part.split('"')[0]
            if not ad_id.isdigit():
                continue
            titel = ""
            m = re.search(r'"name":\s*"([^"]+)"', part)
            if m:
                titel = m.group(1).strip()
            preis = "VB"
            m2 = re.search(r'(\d[\d\.]+)\s*€', part)
            if m2:
                preis = m2.group(0).strip()
            ad_url = f"https://www.kleinanzeigen.de/s-anzeige/{ad_id}"
            if ad_id and titel:
                if max_preis and preis != "VB":
                    try:
                        num = float(preis.replace("€","").replace(".","").replace(",",".").strip())
                        if num > max_preis:
                            continue
                    except Exception:
                        pass
                results.append({"id": ad_id, "titel": titel[:100], "preis": preis, "url": ad_url})
        except Exception:
            continue
    seen = set()
    unique = []
    for r in results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)
    return unique[:10]
def verarbeite_ergebnisse(ergebnisse, keyword):
    """Filtert bereits gesehene Anzeigen, speichert neue."""
    conn = sqlite3.connect(DB)
    neue = []
    for e in ergebnisse:
        exists = conn.execute("SELECT id FROM gesehen WHERE id=?", (e["id"],)).fetchone()
        if not exists:
            conn.execute(
                "INSERT INTO gesehen (id,titel,preis,url,keyword,timestamp) VALUES (?,?,?,?,?,?)",
                (e["id"], e["titel"], e["preis"], e["url"], keyword, datetime.now().isoformat())
            )
            neue.append(e)
    conn.commit()
    conn.close()
    return neue

def run_einmal():
    init_db()
    config = load_config()
    if not config.get("aktiv", True):
        return "Radar deaktiviert."

    gesamt_neu = 0
    for search in config.get("searches", []):
        keyword = search.get("keyword", "")
        max_preis = search.get("max_preis")
        if not keyword:
            continue

        ergebnisse = suche_kleinanzeigen(keyword, max_preis)
        neue = verarbeite_ergebnisse(ergebnisse, keyword)
        gesamt_neu += len(neue)

        for a in neue:
            msg = (f"[JACK Radar] Neue Anzeige: {keyword}\n\n"
                   f"Titel: {a['titel']}\n"
                   f"Preis: {a['preis']}\n"
                   f"Link: {a['url']}")
            notify(msg)
            time.sleep(1)

    import jack_log
    jack_log.log_decision("RADAR", f"{gesamt_neu} neue Anzeigen gefunden")
    return f"Radar: {gesamt_neu} neue Treffer"

if __name__ == "__main__":
    print(run_einmal())
