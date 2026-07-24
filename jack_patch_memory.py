#!/usr/bin/env python3
"""JACK Code-Gedaechtnis: merkt sich welche Patches durchkamen und welche nicht.
Zweck: nie zweimal derselbe gescheiterte Patch. Wird VOR Gemini gefragt,
spart damit API-Calls bei bekannten Fehlschlaegen."""
import os, sqlite3, time, hashlib

H = os.path.expanduser("~/jack")
DB = os.path.join(H, "jack_patch_memory.db")
URTEILE = ("bereit", "syntax", "semantik", "sandbox", "rollback", "angewendet")

def _con():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = _con()
    c.execute("""CREATE TABLE IF NOT EXISTS patches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code_hash TEXT NOT NULL,
        modul TEXT,
        urteil TEXT NOT NULL,
        grund TEXT,
        beschreibung TEXT,
        zeitpunkt TEXT,
        treffer INTEGER DEFAULT 0
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS idx_hash ON patches(code_hash)")
    c.commit()
    c.close()

def hash_code(code):
    norm = chr(10).join([z.rstrip() for z in str(code).split(chr(10)) if z.strip()])
    return hashlib.sha256(norm.encode()).hexdigest()[:16]

def merke(code, modul, urteil, grund="", beschreibung=""):
    if urteil not in URTEILE:
        return None, "Unbekanntes Urteil: " + str(urteil)
    init()
    h = hash_code(code)
    c = _con()
    c.execute("""INSERT INTO patches (code_hash,modul,urteil,grund,beschreibung,zeitpunkt)
                 VALUES (?,?,?,?,?,?)""",
              (h, str(modul)[:100], urteil, str(grund)[:400],
               str(beschreibung)[:200], time.strftime("%Y-%m-%d %H:%M:%S")))
    c.commit()
    c.close()
    return h, "OK"

def kenne_ich(code):
    """Gibt frueheres Urteil zurueck oder None. Zaehlt Treffer mit."""
    init()
    h = hash_code(code)
    c = _con()
    r = c.execute("""SELECT * FROM patches WHERE code_hash=?
                     ORDER BY id DESC LIMIT 1""", (h,)).fetchone()
    if r:
        c.execute("UPDATE patches SET treffer=treffer+1 WHERE id=?", (r["id"],))
        c.commit()
    c.close()
    return dict(r) if r else None

def war_schlecht(code):
    """True wenn dieser Code schon mal blockiert oder zurueckgerollt wurde."""
    r = kenne_ich(code)
    if not r:
        return False, None
    if r["urteil"] in ("syntax", "semantik", "sandbox", "rollback"):
        return True, r
    return False, r

def statistik():
    init()
    c = _con()
    r = c.execute("SELECT urteil, COUNT(*) n FROM patches GROUP BY urteil").fetchall()
    t = c.execute("SELECT SUM(treffer) s FROM patches").fetchone()
    c.close()
    if not r:
        return "Code-Gedaechtnis leer."
    teile = [x["urteil"] + ": " + str(x["n"]) for x in r]
    gespart = (t["s"] or 0)
    return " | ".join(teile) + " | gesparte Wiederholungen: " + str(gespart)

def letzte(limit=5):
    init()
    c = _con()
    r = c.execute("SELECT * FROM patches ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(x) for x in r]

def selbsttest():
    print("=== CODE-GEDAECHTNIS SELBSTTEST ===")
    init()
    schlecht = "def f(d):" + chr(10) + "    x = cmd" + chr(10) + "    cmd = d"
    gut = "def f(d):" + chr(10) + "    return d"

    h1, _ = merke(schlecht, "test.py", "semantik", "UnboundLocalError", "Scope-Bug")
    print("1 merken          :", h1 is not None)

    r = kenne_ich(schlecht)
    print("2 wiedererkannt   :", r is not None and r["urteil"] == "semantik")

    bad, info = war_schlecht(schlecht)
    print("3 als schlecht    :", bad, "|", (info or {}).get("grund", "")[:40])

    bad2, _ = war_schlecht(gut)
    print("4 unbekannt ok    :", not bad2, "(noch nie gesehen)")

    variante = "def f(d):" + chr(10) + "" + chr(10) + "    x = cmd  " + chr(10) + "    cmd = d"
    bad3, _ = war_schlecht(variante)
    print("5 Whitespace egal :", bad3, "(Leerzeilen/Spaces normalisiert)")

    merke(gut, "test.py", "angewendet", "", "sauber")
    bad4, info4 = war_schlecht(gut)
    print("6 gut bleibt gut  :", not bad4, "|", (info4 or {}).get("urteil"))

    print("7 Statistik       :", statistik())
    print("=== FERTIG ===")

if __name__ == "__main__":
    selbsttest()
