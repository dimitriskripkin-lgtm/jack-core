#!/usr/bin/env python3
"""Adapter: jack_skills.db Skills ueber gleiche Schnittstelle wie jack_skills.py.
Erweitert den Telegram-Bot um DB-gestuetzte Skills ohne die alte Datei-Logik zu brechen."""
import os, sqlite3, time, json
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

H = os.path.expanduser("~/jack")
DB = os.path.join(H, "jack_skills.db")
COG = os.path.join(H, "jack_cognition.db")

def _con():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c

def _cog():
    c = sqlite3.connect(COG, timeout=10)
    c.row_factory = sqlite3.Row
    return c

def list_skills():
    try:
        c = _con()
        rows = c.execute("SELECT name, zweck, status FROM skills ORDER BY name").fetchall()
        c.close()
        if not rows:
            return "Noch keine Skills in der DB."
        zeilen = ["Skills in jack_skills.db:"]
        for r in rows:
            symbol = "OK" if r["status"] == "verifiziert" else "??" if r["status"] == "offen" else "!!"
            zeilen.append("  [" + symbol + "] " + r["name"] + " - " + r["zweck"][:60])
        return chr(10).join(zeilen)
    except Exception as e:
        return "Fehler: " + str(e)[:80]

def run_skill(name, timeout=15):
    """JACK_TUNE_DB_SKILL_HALT (19.10.2026, F03): fail closed. Altpfad fuehrte DB-Code per exec ohne Timeout aus
    und setzte 'verifiziert' schon bei fehlender Exception. Kein aktiver Aufrufer. Plan-Skills laufen ueber jack_skill_lib."""
    return False, ("DB-Code-Skill nicht gestartet: Legacy-Ausfuehrung ist gesperrt (JACK_TUNE_DB_SKILL_HALT). "
                   "Neustart nur mit Schemaabgleich, eigenem Worker mit Timeout, Erfolgsvertrag und Promote-Freigabe.")


def _trace_update(trace_id, status, ergebnis, fehler, analyse=None):
    if not trace_id:
        return
    try:
        ts = __import__("datetime").datetime.now().isoformat()
        cog = _cog()
        cog.execute("""UPDATE traces SET status=?, ts_ende=?,
            tatsaechliches_ergebnis=?, fehler=?, rueckwaerts_analyse=?
            WHERE id=?""",
            (status, ts, ergebnis, fehler, analyse, trace_id))
        cog.commit()
        cog.close()
    except Exception as _le:
        _jlog and _jlog.fehler("jack_skills_db","unbenannt",_le)

def get_trace(skill_name, limit=3):
    """Letzte Traces fuer einen Skill - fuer den Rueckwaerts-Lauf."""
    try:
        cog = _cog()
        rows = cog.execute("""SELECT * FROM traces WHERE skill_name=?
            ORDER BY id DESC LIMIT ?""", (skill_name, limit)).fetchall()
        cog.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

if __name__ == "__main__":
    print(list_skills())
    print()
    print("=== Teste system_ram_diagnose ===")
    ok, out = run_skill("system_ram_diagnose")
    print("OK" if ok else "FEHLER")
    print(out[:300])
    print()
    t = get_trace("system_ram_diagnose", 1)
    if t:
        print("Letzter Trace: " + t[0]["status"] + " | " + str(t[0]["ts_ende"])[:19])
