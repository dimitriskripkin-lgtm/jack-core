#!/usr/bin/env python3
"""
JACK Morgen-Briefing - 08:00 Uhr
Nur senden wenn etwas zu melden ist. Stiller Fixmann.
"""
import sqlite3, os, sys, json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.expanduser("~/jack"))
ERRORS_DB = os.path.expanduser("~/jack/jack_errors.db")
PROFILE = os.path.expanduser("~/jack/kortex_profile.json")

def run():
    meldungen = []

    # Offene Fehler
    try:
        conn = sqlite3.connect(ERRORS_DB)
        seit = (datetime.now() - timedelta(hours=12)).isoformat()
        rows = conn.execute(
            "SELECT module, error_msg, COUNT(*) as n FROM errors "
            "WHERE resolved=0 AND timestamp > ? GROUP BY module ORDER BY n DESC LIMIT 5",
            (seit,)
        ).fetchall()
        conn.close()
        if rows:
            zeilen = [f"  {r[0]}: {r[2]}x {r[1][:50]}" for r in rows]
            meldungen.append("Offene Fehler letzte 12h:\n" + "\n".join(zeilen))
    except Exception as e:
        meldungen.append(f"Fehler-Check fehlgeschlagen: {e}")

    # Selbstverbesserungs-Vorschlaege
    try:
        fixes = json.load(open(os.path.expanduser("~/jack/jack_fixes.json")))
        offen = [k for k,v in fixes.items()]
        if offen:
            meldungen.append(f"Offene Fix-Vorschlaege: {len(offen)}\n  " + "\n  ".join(
                [f"/approve_{k}" for k in offen[:3]]
            ))
    except Exception:
        pass

    # Letzter Log-Eintrag
    try:
        lines = open(os.path.expanduser("~/jack/jack_decisions.log")).readlines()
        letzte = [l.strip() for l in lines[-3:] if l.strip()]
        if letzte:
            meldungen.append("Letzte Aktionen:\n  " + "\n  ".join(letzte))
    except Exception:
        pass

    if not meldungen:
        return None  # Alles OK, nichts senden

    ts = datetime.now().strftime("%d.%m.%Y %H:%M")
    return f"[JACK Briefing {ts}]\n\n" + "\n\n".join(meldungen)

if __name__ == "__main__":
    result = run()
    if result:
        import urllib.request, json as _json
        SEC = os.path.expanduser("~/.jack_secrets")
        def _sec(k):
            for l in open(SEC):
                if k in l and "=" in l:
                    return l.split('"')[1] if '"' in l else l.split("=",1)[1].strip()
        tok = _sec("TELEGRAM_BOT_TOKEN")
        cid = _sec("TELEGRAM_CHAT_ID")
        if tok and cid:
            d = _json.dumps({"chat_id": cid, "text": result}).encode()
            r = urllib.request.Request(
                f"https://api.telegram.org/bot{tok}/sendMessage",
                data=d, headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(r, timeout=10)
            print("Briefing gesendet.")
        else:
            print(result)
    else:
        print("Nichts zu melden.")
