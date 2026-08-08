#!/usr/bin/env python3
"""JACK Nacht-Reflexions-Loop.
Laeuft nachts wenn JACK idle ist. Geht Aktionen durch,
bewertet sie, schreibt Schlussfolgerungen, schiebt
wichtiges ins Langzeitgedaechtnis."""
import os, sqlite3, uuid, datetime, json

H = os.path.expanduser("~/jack")
COG_DB = os.path.join(H, "jack_cognition.db")
MEM_DB = os.path.join(H, "kortex_memory.db")

def neue_aktions_id():
    return str(uuid.uuid4())[:16]

def log_aktion(typ, beschreibung, ergebnis=None):
    """Jede JACK-Aktion bekommt eine eindeutige ID."""
    uid = neue_aktions_id()
    ts = datetime.datetime.now().isoformat()
    try:
        c = sqlite3.connect(COG_DB)
        c.execute("""INSERT INTO aktionen (uuid, ts, typ, beschreibung, ergebnis)
                     VALUES (?,?,?,?,?)""", (uid, ts, typ, beschreibung, ergebnis))
        c.commit(); c.close()
    except Exception as e:
        pass
    return uid

def hole_unreflektierte(limit=20):
    """Aktionen die noch keine Schlussfolgerung haben."""
    try:
        c = sqlite3.connect(COG_DB)
        c.row_factory = sqlite3.Row
        rows = c.execute("""SELECT * FROM aktionen
                            WHERE schlussfolgerung IS NULL
                            AND ts < datetime('now', '-1 hour')
                            ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
        c.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def reflexion_durchfuehren(aktion):
    """Bewertet eine Aktion und schreibt Schlussfolgerung."""
    try:
        import jack_gemini_bridge as jg
        frage = chr(10).join([
            "Du bist JACK, ein autonomes KI-System.",
            "Bewerte diese vergangene Aktion kurz und lerne daraus:",
            "Typ: " + str(aktion.get("typ","")),
            "Beschreibung: " + str(aktion.get("beschreibung",""))[:200],
            "Ergebnis: " + str(aktion.get("ergebnis",""))[:200],
            "",
            "Antworte NUR mit JSON:",
            "{",
            '  "bewertung": "gut/neutral/schlecht",',
            '  "schlussfolgerung": "Ein Satz was ich daraus lerne",',
            '  "ins_langzeitgedaechtnis": true/false',
            "}"
        ])
        antwort = jg.ask_gemini(frage)
        if not antwort:
            return None
        start = antwort.find("{")
        ende = antwort.rfind("}") + 1
        if start >= 0 and ende > start:
            return json.loads(antwort[start:ende])
    except Exception as e:
        pass
    return None

def speichere_reflexion(aktion, analyse):
    """Schreibt Bewertung und Schlussfolgerung zurueck."""
    try:
        c = sqlite3.connect(COG_DB)
        c.execute("""UPDATE aktionen SET bewertung=?, schlussfolgerung=?,
                     ins_langzeitgedaechtnis=? WHERE uuid=?""",
                  (analyse.get("bewertung"),
                   analyse.get("schlussfolgerung"),
                   1 if analyse.get("ins_langzeitgedaechtnis") else 0,
                   aktion["uuid"]))
        if analyse.get("ins_langzeitgedaechtnis"):
            ts = datetime.datetime.now().isoformat()
            c.execute("""INSERT INTO reflexionen (ts, aktion_uuid, erkenntnis, staerke)
                         VALUES (?,?,?,?)""",
                      (ts, aktion["uuid"], analyse.get("schlussfolgerung",""), 2))
        c.commit(); c.close()
        return True
    except Exception:
        return False

def ins_langzeitgedaechtnis_schieben():
    """Starke Erkenntnisse kommen ins kortex_memory."""
    try:
        cog = sqlite3.connect(COG_DB)
        cog.row_factory = sqlite3.Row
        rows = cog.execute("""SELECT * FROM reflexionen
                              WHERE angewendet=0 AND staerke >= 2
                              ORDER BY id DESC LIMIT 10""").fetchall()
        cog.close()

        if not rows:
            return 0

        mem = sqlite3.connect(MEM_DB)
        count = 0
        for r in rows:
            try:
                mem.execute("""INSERT OR IGNORE INTO memories (content, tags, timestamp)
                               VALUES (?,?,?)""",
                            ("[JACK-LERNEN] " + r["erkenntnis"],
                             "reflexion,lernen",
                             datetime.datetime.now().isoformat()))
                cog2 = sqlite3.connect(COG_DB)
                cog2.execute("UPDATE reflexionen SET angewendet=1 WHERE id=?", (r["id"],))
                cog2.commit(); cog2.close()
                count += 1
            except Exception:
                pass
        mem.commit(); mem.close()
        return count
    except Exception:
        return 0

def nacht_loop():
    """Einmal durchlaufen: reflektieren + ins Gedaechtnis."""
    aktionen = hole_unreflektierte(10)
    if not aktionen:
        return {"reflektiert": 0, "ins_gedaechtnis": 0}

    reflektiert = 0
    for a in aktionen:
        analyse = reflexion_durchfuehren(a)
        if analyse:
            speichere_reflexion(a, analyse)
            reflektiert += 1

    ins_mem = ins_langzeitgedaechtnis_schieben()
    return {"reflektiert": reflektiert, "ins_gedaechtnis": ins_mem}

def status():
    """Kurzstatus fuer Telegram."""
    try:
        c = sqlite3.connect(COG_DB)
        total = c.execute("SELECT COUNT(*) FROM aktionen").fetchone()[0]
        offen = c.execute("SELECT COUNT(*) FROM aktionen WHERE schlussfolgerung IS NULL").fetchone()[0]
        r_total = c.execute("SELECT COUNT(*) FROM reflexionen").fetchone()[0]
        r_mem = c.execute("SELECT COUNT(*) FROM reflexionen WHERE angewendet=1").fetchone()[0]
        c.close()
        return (f"Aktionen: {total} ({offen} unreflektiert) | "
                f"Erkenntnisse: {r_total} ({r_mem} im Langzeitgedaechtnis)")
    except Exception as e:
        return "Fehler: " + str(e)[:50]

if __name__ == "__main__":
    print("=== JACK Reflexions-Status ===")
    print(status())
    print()
    print("=== Teste log_aktion ===")
    uid = log_aktion("test", "Manueller Test der Reflexions-Pipeline", "OK")
    print("Neue Aktions-ID:", uid)
    print()
    print("=== Status danach ===")
    print(status())
