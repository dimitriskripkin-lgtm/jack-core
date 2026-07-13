#!/usr/bin/env python3
"""
JACK Session-Konsolidierung
Liest die letzten Logs und Gedaechtnis-Zugriffe,
schreibt eine Zusammenfassung als neuen Memory-Eintrag.
Laeuft automatisch nach jeder Session (Trigger: Waechter oder manuell).
"""
import sqlite3, os, sys, json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.expanduser("~/jack"))
DB = os.path.expanduser("~/jack/kortex_memory.db")
LOG = os.path.expanduser("~/jack/jack_decisions.log")

def run():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Was wurde in den letzten 12h abgerufen?
    seit = (datetime.now() - timedelta(hours=12)).isoformat()
    zugegriffen = c.execute(
        "SELECT category, content FROM memories WHERE last_accessed > ? ORDER BY access_count DESC LIMIT 5",
        (seit,)
    ).fetchall()

    # Was wurde in den letzten 12h gemacht? (Logs)
    try:
        lines = open(LOG).readlines()
        letzte_logs = [l.strip() for l in lines[-10:] if l.strip()]
    except Exception:
        letzte_logs = []

    if not zugegriffen and not letzte_logs:
        return "Nichts zu konsolidieren."

    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    teile = [f"Session-Zusammenfassung {ts}:"]

    if letzte_logs:
        teile.append("Aktionen: " + " | ".join([l.split("] ")[1] if "] " in l else l for l in letzte_logs[-5:]]))

    if zugegriffen:
        teile.append("Genutzte Eintraege: " + ", ".join([f"{r[1][:40]}" for r in zugegriffen]))

    inhalt = "\n".join(teile)

    # Nur speichern wenn Session substanziell war (min 3 Log-Eintraege)
    if len(letzte_logs) >= 3:
        c.execute(
            "INSERT INTO memories (timestamp, category, content, source, tags, importance) VALUES (?,?,?,?,?,?)",
            (datetime.now().isoformat(), "session", inhalt, "consolidate", "auto session", 6)
        )
        conn.commit()
        import jack_log
        jack_log.log_decision("CONSOLIDATE", f"Session gespeichert: {len(letzte_logs)} Logs, {len(zugegriffen)} Zugriffe")
        conn.close()
        return f"Konsolidiert: {len(letzte_logs)} Logs + {len(zugegriffen)} Gedaechtnis-Zugriffe"

    conn.close()
    return "Session zu kurz fuer Konsolidierung."

if __name__ == "__main__":
    print(run())
