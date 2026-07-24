#!/usr/bin/env python3
"""JACK Missionen: asynchrone Aufgabenliste in SQLite.
Dima wirft Aufgaben rein, JACK arbeitet sie ab, Ergebnis wartet.
Sicherheit: Code-Missionen enden IMMER bei wartet_freigabe,
nie Auto-Apply auf lebende Module. Max 3 Versuche gegen Endlosschleifen."""
import os, sqlite3, time

H = os.path.expanduser("~/jack")
DB = os.path.join(H, "jack_missions.db")
MAX_VERSUCHE = 3
TYPEN = ("befehl", "code", "notiz")
STATI = ("offen", "laeuft", "wartet_freigabe", "fertig", "fehler", "blockiert")

def _con():
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = _con()
    c.execute("""CREATE TABLE IF NOT EXISTS missions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aufgabe TEXT NOT NULL,
        typ TEXT NOT NULL DEFAULT 'befehl',
        status TEXT NOT NULL DEFAULT 'offen',
        prioritaet INTEGER DEFAULT 5,
        erstellt TEXT,
        gestartet TEXT,
        beendet TEXT,
        ergebnis TEXT,
        versuche INTEGER DEFAULT 0
    )""")
    c.commit()
    c.close()

def _jetzt():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def _log(tag, msg):
    try:
        import jack_log
        jack_log.log_decision(tag, str(msg)[:120])
    except Exception:
        pass

def add(aufgabe, typ="befehl", prioritaet=5):
    if typ not in TYPEN:
        return None, "Unbekannter Typ: " + str(typ)
    aufgabe = str(aufgabe).strip()
    if not aufgabe:
        return None, "Leere Aufgabe"
    init()
    c = _con()
    cur = c.execute(
        "INSERT INTO missions (aufgabe,typ,status,prioritaet,erstellt) VALUES (?,?,?,?,?)",
        (aufgabe, typ, "offen", int(prioritaet), _jetzt()))
    mid = cur.lastrowid
    c.commit()
    c.close()
    _log("MISSION-NEU", "#" + str(mid) + " " + typ + ": " + aufgabe[:60])
    return mid, "OK"

def naechste():
    """Naechste offene Mission, hoechste Prioritaet zuerst (1 = wichtig)."""
    init()
    c = _con()
    r = c.execute("""SELECT * FROM missions
        WHERE status='offen' AND versuche < ?
        ORDER BY prioritaet ASC, id ASC LIMIT 1""", (MAX_VERSUCHE,)).fetchone()
    c.close()
    return dict(r) if r else None

def setze_status(mid, status, ergebnis=None):
    if status not in STATI:
        return False, "Unbekannter Status: " + str(status)
    init()
    c = _con()
    felder = ["status=?"]
    werte = [status]
    if status == "laeuft":
        felder.append("gestartet=?"); werte.append(_jetzt())
        felder.append("versuche=versuche+1")
    if status in ("fertig", "fehler", "blockiert", "wartet_freigabe"):
        felder.append("beendet=?"); werte.append(_jetzt())
    if ergebnis is not None:
        felder.append("ergebnis=?"); werte.append(str(ergebnis)[:4000])
    werte.append(mid)
    c.execute("UPDATE missions SET " + ",".join(felder) + " WHERE id=?", werte)
    c.commit()
    c.close()
    _log("MISSION-STATUS", "#" + str(mid) + " -> " + status)
    return True, "OK"

def liste(status=None, limit=10):
    init()
    c = _con()
    if status:
        r = c.execute("SELECT * FROM missions WHERE status=? ORDER BY id DESC LIMIT ?",
                      (status, limit)).fetchall()
    else:
        r = c.execute("SELECT * FROM missions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(x) for x in r]

def uebersicht():
    init()
    c = _con()
    r = c.execute("SELECT status, COUNT(*) n FROM missions GROUP BY status").fetchall()
    c.close()
    if not r:
        return "Keine Missionen."
    return " | ".join([x["status"] + ": " + str(x["n"]) for x in r])

def selbsttest():
    print("=== MISSIONS SELBSTTEST ===")
    init()
    mid, msg = add("free -h", "befehl", 3)
    print("1 anlegen        :", mid is not None, msg)
    n = naechste()
    print("2 naechste holen :", n is not None and n["id"] == mid)
    setze_status(mid, "laeuft")
    setze_status(mid, "fertig", "Testausgabe")
    n2 = naechste()
    print("3 fertig raus    :", n2 is None or n2["id"] != mid)
    bad, bmsg = add("x", "quatsch")
    print("4 Typ-Schutz     :", bad is None, bmsg)
    leer, lmsg = add("   ", "befehl")
    print("5 Leer-Schutz    :", leer is None, lmsg)
    mid2, _ = add("dauerlaeufer", "befehl", 9)
    for _ in range(MAX_VERSUCHE):
        setze_status(mid2, "laeuft")
        setze_status(mid2, "offen")
    n3 = naechste()
    geblockt = (n3 is None) or (n3["id"] != mid2)
    print("6 Versuchslimit  :", geblockt, "(nach " + str(MAX_VERSUCHE) + " Versuchen raus)")
    print("7 Uebersicht     :", uebersicht())
    print("=== FERTIG ===")

if __name__ == "__main__":
    selbsttest()
