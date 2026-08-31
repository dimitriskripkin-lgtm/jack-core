#!/usr/bin/env python3
"""JACK Missionen: asynchrone Aufgabenliste in SQLite.
Dima wirft Aufgaben rein, JACK arbeitet sie ab, Ergebnis wartet.
Sicherheit: Code-Missionen enden IMMER bei wartet_freigabe,
nie Auto-Apply auf lebende Module. Max 3 Versuche gegen Endlosschleifen."""
import os, sqlite3, time
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

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
    except Exception as _le:
        _jlog and _jlog.fehler("jack_missions","unbenannt",_le)

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
    """CRIT-006: atomarer Claim. SELECT+UPDATE in einer Transaktion,
    damit zwei Worker nie dieselbe Mission ziehen."""
    init()
    c = _con()
    try:
        c.isolation_level = None
        c.execute("BEGIN IMMEDIATE")
        r = c.execute("""SELECT * FROM missions
            WHERE status='offen' AND versuche < ?
            ORDER BY prioritaet ASC, id ASC LIMIT 1""", (MAX_VERSUCHE,)).fetchone()
        if not r:
            c.execute("COMMIT"); c.close(); return None
        cur = c.execute("""UPDATE missions SET status='laeuft', gestartet=?,
            versuche=versuche+1 WHERE id=? AND status='offen' AND versuche < ?""",
            (_jetzt(), r["id"], MAX_VERSUCHE))
        if cur.rowcount != 1:
            c.execute("ROLLBACK"); c.close(); return None
        c.execute("COMMIT")
        d = dict(r); d["status"] = "laeuft"; d["_geclaimt"] = True
        c.close(); return d
    except Exception as e:
        try: c.execute("ROLLBACK")
        except Exception: pass
        c.close(); _log("CLAIM-FEHLER", str(e)[:100]); return None

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


MIN_FREI_MB = 800

def ressourcen_ok():
    """Liest /proc/meminfo direkt - kein Subprozess, gerade bei knappem RAM wichtig."""
    try:
        werte = {}
        for z in open("/proc/meminfo"):
            t = z.split(":")
            if len(t) == 2:
                werte[t[0].strip()] = int(t[1].strip().split()[0])
        frei_mb = werte.get("MemAvailable", 0) // 1024
        if frei_mb < MIN_FREI_MB:
            return False, "RAM knapp: " + str(frei_mb) + "MB frei, brauche " + str(MIN_FREI_MB) + "MB"
        return True, str(frei_mb) + "MB frei"
    except Exception as e:
        return False, "BLOCKIERT: RAM-Messung fehlgeschlagen: " + str(e)[:60]


def _fehlschlag(mid, versuche_bisher, grund):
    """Zurueck auf offen - oder endgueltig fehler wenn Limit erreicht."""
    if versuche_bisher + 1 >= MAX_VERSUCHE:
        setze_status(mid, "fehler", "Aufgegeben nach " + str(MAX_VERSUCHE) + ": " + str(grund)[:300])
        return "fehler"
    setze_status(mid, "offen", str(grund)[:300])
    return "offen"


def _run_fix(m):
    """FIX-Mission: Backup+Patch+py_compile+Verify. Rollback bei Fehler."""
    import os, shutil
    act = m.get("act","")
    raw_file = m.get("file","")
    fpath = os.path.expanduser(raw_file)
    JACK = os.path.expanduser("~/jack")
    if not fpath.startswith(JACK):
        return False, "Pfad-Tabu: nur ~/jack/ erlaubt"
    if not os.path.exists(fpath):
        return False, "Datei nicht gefunden: " + fpath
    bak = fpath + ".fix.bak"
    shutil.copy2(fpath, bak)
    try:
        content = open(fpath, errors="ignore").read()
        if act in ("sed_replace","py_replace"):
            old = m.get("old",""); new = m.get("new","")
            if not old: os.remove(bak); return False, "old fehlt"
            if old not in content: os.remove(bak); return False, "old nicht gefunden: "+old[:40]
            count = content.count(old)
            content = content.replace(old, new, 1 if act=="py_replace" else count)
            open(fpath,"w").write(content)
            info = act+" OK "+str(count)+"x: "+old[:30]
        else:
            os.remove(bak); return False, "Unbekannter Fix-Act: "+act
        if fpath.endswith(".py"):
            import subprocess
            r = subprocess.run(["python3","-m","py_compile",fpath],
                capture_output=True, text=True, timeout=10)
            if r.returncode != 0:
                shutil.copy2(bak,fpath); os.remove(bak)
                return False, "py_compile FAIL Rollback: "+r.stderr[:80]
        verify_act = m.get("verify_act")
        if verify_act:
            vm = {"act":verify_act,"file":raw_file,
                  "pattern":m.get("verify_pattern",""),
                  "expect_max":m.get("verify_expect_max",0),"expect":"PASS"}
            ok2,vinfo = _run_check(vm)
            if not ok2:
                shutil.copy2(bak,fpath); os.remove(bak)
                return False, "Verify FAIL Rollback: "+vinfo
            info += " | verify="+vinfo
        os.remove(bak); return True, info
    except Exception as e:
        try: shutil.copy2(bak,fpath); os.remove(bak)
        except Exception: pass
        return False, "Exception Rollback: "+str(e)[:80]

def dispatch_once():
    """Arbeitet GENAU EINE offene Mission ab. Gibt dict zurueck oder None."""
    m = naechste()
    if not m:
        return None
    mid = m["id"]
    typ = m.get("typ") or ("check" if m.get("act") in {"grep_count","line_count","file_exists","line_check","mtime_fresh","no_secret"} else None)
    aufgabe = m["aufgabe"]
    vers = m["versuche"]
    if typ == "code":
        frei_ok, frei_info = ressourcen_ok()
        if not frei_ok:
            _log("MISSION-VERSCHOBEN", "#" + str(mid) + " " + frei_info)
            return {"id": mid, "typ": typ, "status": "verschoben", "text": frei_info}
    # bereits durch naechste() geclaimt

    if typ == "notiz":
        setze_status(mid, "fertig", "Notiz vermerkt, keine Ausfuehrung")
        return {"id": mid, "typ": typ, "status": "fertig", "text": aufgabe[:200]}

    if typ == "befehl":
        try:
            import jack_oracle
            cmd, alias = jack_oracle.resolve_alias(aufgabe)
            safe, grund = jack_oracle.is_safe(cmd)
            if not safe:
                setze_status(mid, "blockiert", "Gate: " + str(grund))
                return {"id": mid, "typ": typ, "status": "blockiert", "text": str(grund)}
            ergebnis = jack_oracle.run_cmd(cmd)
            setze_status(mid, "fertig", ergebnis)
            return {"id": mid, "typ": typ, "status": "fertig", "text": str(ergebnis)[:500]}
        except Exception as e:
            st = _fehlschlag(mid, vers, "Ausfuehrfehler: " + str(e)[:150])
            return {"id": mid, "typ": typ, "status": st, "text": str(e)[:200]}

    if typ == "code":
        try:
            import jack_coder
            fn, code, msg = jack_coder.write_code(aufgabe)
            if not fn:
                st = _fehlschlag(mid, vers, "Coder: " + str(msg)[:150])
                return {"id": mid, "typ": typ, "status": st, "text": str(msg)[:200]}
            setze_status(mid, "wartet_freigabe",
                         "In Werkstatt: " + str(fn) + " (" + str(msg) + ")")
            return {"id": mid, "typ": typ, "status": "wartet_freigabe", "text": str(fn)}
        except Exception as e:
            st = _fehlschlag(mid, vers, "Coderfehler: " + str(e)[:150])
            return {"id": mid, "typ": typ, "status": st, "text": str(e)[:200]}

    if typ == "fix":
        try:
            ok, info = _run_fix(dict(m))
            if ok:
                setze_status(mid, "fertig", info)
                return {"id": mid, "typ": typ, "status": "fertig", "text": info}
            else:
                st = _fehlschlag(mid, vers, info)
                return {"id": mid, "typ": typ, "status": st, "text": info}
        except Exception as e:
            st = _fehlschlag(mid, vers, str(e)[:150])
            return {"id": mid, "typ": typ, "status": st, "text": str(e)[:200]}

    setze_status(mid, "fehler", "Unbekannter Typ: " + str(typ))
    return {"id": mid, "typ": typ, "status": "fehler", "text": "Unbekannter Typ"}


LEASE_MINUTEN = 10

def recover_stale():
    """Holt Missionen zurueck, die im Zustand laeuft haengengeblieben sind
    (Worker gestorben, OOM, Dienst-Neustart). Versuchszaehler bleibt stehen,
    nach MAX_VERSUCHE ist endgueltig Schluss."""
    init()
    c = _con()
    try:
        rows = c.execute("""SELECT id, aufgabe, versuche, gestartet FROM missions
            WHERE status='laeuft' AND gestartet IS NOT NULL
              AND gestartet < datetime('now','localtime','-""" + str(LEASE_MINUTEN) + """ minutes')""").fetchall()
        n = 0
        for r in rows:
            if r["versuche"] >= MAX_VERSUCHE:
                c.execute("UPDATE missions SET status='fehler', beendet=?, ergebnis=? WHERE id=?",
                    (_jetzt(), "Aufgegeben: Lease abgelaufen nach " + str(r["versuche"]) + " Versuchen", r["id"]))
            else:
                c.execute("UPDATE missions SET status='offen' WHERE id=? AND status='laeuft'", (r["id"],))
            n += 1
        c.commit()
        if n: _log("MISSION-RECOVER", str(n) + " haengende Mission(en) zurueckgeholt")
        return n
    except Exception as e:
        _log("RECOVER-FEHLER", str(e)[:100]); return 0
    finally:
        c.close()
