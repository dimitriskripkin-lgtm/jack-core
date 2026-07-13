#!/usr/bin/env python3
"""
JACK Morgen-Briefing - 07:55 Uhr
Nur senden wenn etwas zu melden ist. Stiller Fixmann.
"""
import sqlite3, os, sys, json, subprocess
from datetime import datetime, timedelta

sys.path.insert(0, os.path.expanduser("~/jack"))
ERRORS_DB = os.path.expanduser("~/jack/jack_errors.db")
MEMORY_DB = os.path.expanduser("~/jack/kortex_memory.db")

def _sec(k):
    for l in open(os.path.expanduser("~/.jack_secrets")):
        if k in l and "=" in l:
            return l.split('"')[1] if '"' in l else l.split("=",1)[1].strip()

def batteriestand():
    try:
        r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        d = json.loads(r.stdout)
        pct = d.get("percentage", "?")
        status = d.get("status", "?")
        return f"Honor: {pct}% ({status})"
    except Exception:
        return "Honor: Akku-Daten nicht verfuegbar"

def letzte_sessions():
    try:
        conn = sqlite3.connect(MEMORY_DB)
        rows = conn.execute(
            "SELECT content FROM memories WHERE category='session' ORDER BY timestamp DESC LIMIT 3"
        ).fetchall()
        conn.close()
        if not rows:
            return None
        return "Letzte Sessions:\n" + "\n---\n".join([r[0][:200] for r in rows])
    except Exception:
        return None

def offene_fehler():
    try:
        conn = sqlite3.connect(ERRORS_DB)
        seit = (datetime.now() - timedelta(hours=12)).isoformat()
        rows = conn.execute(
            "SELECT module, error_msg, COUNT(*) as n FROM errors "
            "WHERE resolved=0 AND timestamp > ? GROUP BY module ORDER BY n DESC LIMIT 5",
            (seit,)
        ).fetchall()
        conn.close()
        if not rows:
            return None
        zeilen = [f"  {r[0]}: {r[2]}x - {r[1][:60]}" for r in rows]
        return "Offene Fehler letzte 12h:\n" + "\n".join(zeilen)
    except Exception as e:
        return f"Fehler-Check fehlgeschlagen: {e}"

def offene_fixes():
    try:
        fixes = json.load(open(os.path.expanduser("~/jack/jack_fixes.json")))
        offen = list(fixes.keys())
        if not offen:
            return None
        return f"Offene Fix-Vorschlaege: {len(offen)}\n" + "\n".join([f"  /approve_{k}" for k in offen[:3]])
    except Exception:
        return None

def dienste_status():
    try:
        r = subprocess.run(
            ["sv", "status", "jack_telegram", "jack_waechter", "jack_cortex",
             "jack_autolearn", "jack_publisher", "kortex_bridge", "ollama"],
            capture_output=True, text=True, timeout=8
        )
        tote = [l.split(":")[1].strip() for l in r.stdout.splitlines() if l.startswith("down:")]
        if tote:
            return f"DIENSTE TOT: {', '.join(tote)}"
        return None  # Alles OK -> nicht melden
    except Exception:
        return "Dienste-Check fehlgeschlagen"

def run():
    meldungen = []
    ts = datetime.now().strftime("%d.%m.%Y %H:%M")

    # Immer: Batteriestand
    meldungen.append(batteriestand())

    # Nur wenn was nicht stimmt: Dienste
    d = dienste_status()
    if d:
        meldungen.append(d)

    # Offene Fehler
    f = offene_fehler()
    if f:
        meldungen.append(f)

    # Offene Fixes
    fx = offene_fixes()
    if fx:
        meldungen.append(fx)

    # Letzte Sessions (immer, gibt Kontext)
    s = letzte_sessions()
    if s:
        meldungen.append(s)

    # Letzte 3 Log-Eintraege
    try:
        lines = open(os.path.expanduser("~/jack/jack_decisions.log")).readlines()
        letzte = [l.strip() for l in lines[-3:] if l.strip()]
        if letzte:
            meldungen.append("Letzte Aktionen:\n  " + "\n  ".join(letzte))
    except Exception:
        pass

    # Nur senden wenn mehr als nur Akku da ist
    if len(meldungen) <= 1:
        return None

    return f"[JACK Briefing {ts}]\n\n" + "\n\n".join(meldungen)

if __name__ == "__main__":
    result = run()
    if result:
        import urllib.request, json as _json
        tok = _sec("TELEGRAM_BOT_TOKEN")
        cid = _sec("TELEGRAM_CHAT_ID")
        if tok and cid:
            d = _json.dumps({"chat_id": cid, "text": result}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{tok}/sendMessage",
                data=d, headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=10)
            print("Briefing gesendet.")
    else:
        print("Nichts kritisches zu melden.")
