#!/usr/bin/env python3
"""JACK Skill-Builder: liest den Fingerabdruck, findet Luecken, generiert Skills.
Erster auto-generierter Skill - kein Zufall, Messung entscheidet."""
import os, json, sqlite3, datetime

H = os.path.expanduser("~/jack")

def lade_fingerabdruck():
    pfad = os.path.join(H, "jack_fingerprint.json")
    if not os.path.exists(pfad):
        return None
    return json.load(open(pfad))

def bekannte_skills():
    db = os.path.join(H, "jack_skills.db")
    try:
        c = sqlite3.connect(db)
        names = [r[0] for r in c.execute("SELECT name FROM skills").fetchall()]
        c.close()
        return set(names)
    except Exception:
        return set()

def finde_luecken(fp, vorhanden):
    """Vergleicht verfuegbare Faehigkeiten mit bekannten Skills. Gibt Luecken zurueck."""
    luecken = []
    api = fp.get("termux_api", {})
    mapping = {
        "termux-battery-status": ("akku_status", "Akkustand auslesen"),
        "termux-wifi-connectioninfo": ("wifi_status", "WLAN-Verbindung anzeigen"),
        "termux-telephony-deviceinfo": ("geraet_info", "Geraeteinformationen auslesen"),
        "termux-location": ("standort", "GPS-Standort bestimmen"),
        "termux-sensor": ("sensoren_liste", "Verfuegbare Sensoren auflisten"),
    }
    for befehl, (skill_name, beschreibung) in mapping.items():
        info = api.get(befehl, {})
        verfuegbar = info.get("vorhanden") or info.get("funktioniert")
        if verfuegbar and skill_name not in vorhanden:
            luecken.append({
                "befehl": befehl,
                "skill_name": skill_name,
                "beschreibung": beschreibung
            })
    return luecken

def generiere_skill_code(befehl, skill_name, beschreibung):
    """Erzeugt Code fuer einen einfachen Termux-API-Skill."""
    if "battery" in befehl:
        code = chr(10).join([
            "import subprocess, json",
            "r = subprocess.run(['" + befehl + "'], capture_output=True, text=True, timeout=8)",
            "try:",
            "    d = json.loads(r.stdout)",
            "    for k,v in d.items(): print(str(k) + ': ' + str(v))",
            "except Exception:",
            "    print(r.stdout.strip()[:500])",
        ])
        erwartet = "Schluessel-Wert-Paare der Akkuinformationen"
    elif "wifi" in befehl:
        code = chr(10).join([
            "import subprocess, json",
            "r = subprocess.run(['" + befehl + "'], capture_output=True, text=True, timeout=8)",
            "try:",
            "    d = json.loads(r.stdout)",
            "    print('SSID: ' + str(d.get('ssid','?')))",
            "    print('IP: ' + str(d.get('ip','?')))",
            "    print('Signal: ' + str(d.get('rssi','?')) + ' dBm')",
            "except Exception:",
            "    print(r.stdout.strip()[:500])",
        ])
        erwartet = "SSID, IP-Adresse, Signalstaerke"
    elif "telephony" in befehl:
        code = chr(10).join([
            "import subprocess, json",
            "r = subprocess.run(['" + befehl + "'], capture_output=True, text=True, timeout=8)",
            "try:",
            "    d = json.loads(r.stdout)",
            "    for k,v in d.items(): print(str(k) + ': ' + str(v))",
            "except Exception:",
            "    print(r.stdout.strip()[:500])",
        ])
        erwartet = "Geraeteinformationen wie IMEI, Netzwerk, Betreiber"
    elif "location" in befehl:
        code = chr(10).join([
            "import subprocess, json",
            "r = subprocess.run(['" + befehl + "', '-p', 'network', '-r', 'once'], capture_output=True, text=True, timeout=15)",
            "try:",
            "    d = json.loads(r.stdout)",
            "    print('Lat: ' + str(d.get('latitude','?')))",
            "    print('Lon: ' + str(d.get('longitude','?')))",
            "    print('Genauigkeit: ' + str(d.get('accuracy','?')) + 'm')",
            "except Exception:",
            "    print(r.stdout.strip()[:500])",
        ])
        erwartet = "Breitengrad, Laengengrad, Genauigkeit in Metern"
    else:
        code = chr(10).join([
            "import subprocess",
            "r = subprocess.run(['" + befehl + "'], capture_output=True, text=True, timeout=8)",
            "print(r.stdout.strip()[:1000] if r.stdout.strip() else 'Kein Output')",
        ])
        erwartet = "Output des Befehls " + befehl

    return code, erwartet

def speichere_skill(skill_name, zweck, befehl, code, erwartet):
    db = os.path.join(H, "jack_skills.db")
    c = sqlite3.connect(db)
    try:
        c.execute("""INSERT INTO skills
            (name, zweck, trigger, abhaengigkeiten, code, erwartete_ausgabe, status, erstellt)
            VALUES (?,?,?,?,?,?,?,?)""",
            (skill_name, zweck, befehl, json.dumps([befehl]), code,
             erwartet, "offen", datetime.datetime.now().isoformat()))
        c.commit()
        print("Gespeichert: " + skill_name)
    except sqlite3.IntegrityError:
        print("Existiert schon: " + skill_name)
    c.close()

def run():
    fp = lade_fingerabdruck()
    if not fp:
        print("Kein Fingerabdruck. Erst: python3 jack_scout.py")
        return []

    print("Fingerabdruck: " + fp.get("hash","?") + " (" + fp.get("geraet","?") + ")")
    vorhanden = bekannte_skills()
    print("Bekannte Skills: " + str(len(vorhanden)))

    luecken = finde_luecken(fp, vorhanden)
    print("Luecken gefunden: " + str(len(luecken)))

    neue = []
    for l in luecken:
        print("Generiere: " + l["skill_name"] + " fuer " + l["befehl"])
        code, erwartet = generiere_skill_code(l["befehl"], l["skill_name"], l["beschreibung"])
        speichere_skill(l["skill_name"], l["beschreibung"], l["befehl"], code, erwartet)
        neue.append(l["skill_name"])


    # Python-Skills aus Verhaltens-Luecken
    py_luecken = python_luecken(vorhanden)
    for l in py_luecken:
        print("Python-Skill generiere: " + l["name"])
        speichere_skill(l["name"], l["beschreibung"], "python", l["code"], l["erwartet"])
        neue.append(l["name"])
    if not neue:
        print("Keine neuen Skills noetig - alle verfuegbaren Faehigkeiten haben Skills.")
    else:
        print("Neu generiert: " + str(neue))
    return neue

if __name__ == "__main__":
    neu = run()
    if neu:
        print(chr(10) + "Jetzt verifizieren:")
        for n in neu:
            print("  python3 -c \"import jack_skills_db; print(jack_skills_db.run_skill('" + n + "'))\"")


def python_luecken(vorhanden):
    """Findet Python-basierte Luecken - Skills die JACK selbst braucht."""
    kandidaten = [
        {
            "name": "fehler_zusammenfassung",
            "beschreibung": "Fasst offene Fehler aus jack_errors.db zusammen",
            "code": chr(10).join([
                "import sqlite3, os",
                "c = sqlite3.connect(os.path.expanduser(\"~/jack/jack_errors.db\"))",
                "rows = c.execute(\"SELECT module, error_msg FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 5\").fetchall()",
                "c.close()",
                "if not rows: print(\"Keine offenen Fehler\")",
                "else:",
                "    for r in rows: print(r[0] + \": \" + r[1][:80])",
            ]),
            "erwartet": "Liste offener Fehler oder: Keine offenen Fehler",
            "abh": ["sqlite3"],
        },
        {
            "name": "memory_statistik",
            "beschreibung": "Zeigt Gedaechtnis-Statistik: Eintraege, stale, Kategorien",
            "code": chr(10).join([
                "import sqlite3, os",
                "dbs = [",
                "    (\"jack_memory.db\", \"memory\"),",
                "    (\"kortex_memory.db\", \"memories\"),",
                "]",
                "for db_name, tbl in dbs:",
                "    pfad = os.path.expanduser(\"~/jack/\" + db_name)",
                "    if not os.path.exists(pfad): continue",
                "    c = sqlite3.connect(pfad)",
                "    try:",
                "        n = c.execute(\"SELECT COUNT(*) FROM \" + tbl).fetchone()[0]",
                "        print(db_name + \": \" + str(n) + \" Eintraege\")",
                "    except: pass",
                "    c.close()",
            ]),
            "erwartet": "Anzahl Eintraege pro Gedaechtnis-Datenbank",
            "abh": ["sqlite3"],
        },
        {
            "name": "api_budget_check",
            "beschreibung": "Zeigt aktuellen API-Budgetstand",
            "code": chr(10).join([
                "import sys, os",
                "sys.path.insert(0, os.path.expanduser(\"~/jack\"))",
                "import jack_budget",
                "print(jack_budget.status())",
            ]),
            "erwartet": "Text oder Vision Calls und Token-Verbrauch",
            "abh": ["jack_budget"],
        },
    ]
    return [k for k in kandidaten if k["name"] not in vorhanden]


def speichere_skill(skill_name, zweck, befehl, code, erwartet):
    """Ueberschrieben: schreibt ins echte Schema (state/plan_json) - Mantel ueber Alt-Version."""
    import sqlite3 as _sq, json as _js, time as _tm, os as _os
    _db = _os.path.expanduser('~/jack/jack_skills.db')
    _plan = {"name": skill_name, "steps": [{"type": "exec", "cmd": befehl, "desc": str(zweck)[:80]}]}
    if erwartet:
        _plan["success_criteria"] = [{"type": "contains", "value": str(erwartet)[:60], "step": 1}]
    _c = _sq.connect(_db, timeout=5)
    try:
        _c.execute("INSERT OR IGNORE INTO skills (name, description, plan_json, state, executions, successes, created_ts, last_ts) VALUES (?,?,?,?,0,0,?,?)",
            (skill_name, str(zweck)[:200], _js.dumps(_plan), 'CANDIDATE', int(_tm.time()), int(_tm.time())))
        _c.commit()
    finally:
        _c.close()
    return True
