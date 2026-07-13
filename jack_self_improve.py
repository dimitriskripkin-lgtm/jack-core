#!/usr/bin/env python3
"""
JACK Selbstverbesserung - Stiller Fixmann
Analysiert Fehler, generiert Fix-Vorschlaege, legt sie in Werkstatt ab.
Fuehrt NICHTS selbst aus. Dima bestaetigt per Telegram.
"""
import sqlite3, json, os, sys, hashlib, py_compile, shutil
from datetime import datetime, timedelta

ERRORS_DB = os.path.expanduser("~/jack/jack_errors.db")
MEMORY_DB = os.path.expanduser("~/jack/kortex_memory.db")
WERKSTATT  = os.path.expanduser("~/jack_werkstatt")
FIXES_LOG  = os.path.expanduser("~/jack/jack_fixes.json")
JACK_PATH  = os.path.expanduser("~/jack")

sys.path.insert(0, JACK_PATH)

# ── Bekannte Fix-Muster ─────────────────────────────────────────────────────
PATTERNS = [
    {
        "id": "cortex_ssh_timeout",
        "modul": "jack_cortex",
        "erkennung": "SSH-Timeout",
        "beschreibung": "Xiaomi SSH wiederholt nicht erreichbar. WiFi-Recovery-Timeout erhoehen.",
        "search": "capture_output=True, text=True, timeout=15",
        "replace": "capture_output=True, text=True, timeout=25",
        "datei": "jack_cortex.py"
    },
    {
        "id": "publish_silent_fail",
        "modul": "jack_publish",
        "erkennung": "SILENT-FAIL jack_publish",
        "beschreibung": "Publish-Fehler wiederholt aufgetreten. Vorschlag: Retry-Logik hinzufuegen.",
        "search": None,
        "replace": None,
        "datei": None
    }
]

def analyse():
    """Liest jack_errors.db, findet Muster, gibt Liste mit Treffern zurueck."""
    conn = sqlite3.connect(ERRORS_DB)
    seit = (datetime.now() - timedelta(days=7)).isoformat()
    rows = conn.execute(
        "SELECT module, error_type, error_msg, COUNT(*) as n FROM errors "
        "WHERE resolved=0 AND timestamp > ? GROUP BY module, error_type "
        "ORDER BY n DESC LIMIT 20", (seit,)
    ).fetchall()
    conn.close()

    treffer = []
    for row in rows:
        modul, etype, emsg, n = row
        for p in PATTERNS:
            if p["modul"] in modul and p["erkennung"] in (emsg or "") and n >= 5:
                treffer.append({
                    "pattern_id": p["id"],
                    "modul": modul,
                    "n": n,
                    "beschreibung": p["beschreibung"],
                    "search": p["search"],
                    "replace": p["replace"],
                    "datei": p["datei"]
                })
                break
    return treffer

def fix_vorbereiten(treffer):
    """Legt Fix-Script in Werkstatt ab. Gibt Fix-ID zurueck."""
    if not treffer.get("search") or not treffer.get("datei"):
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fix_id = f"fix_{treffer['pattern_id']}_{ts}"
    ziel = os.path.join(WERKSTATT, f"{fix_id}.py")
    quell = os.path.join(JACK_PATH, treffer["datei"])

    if not os.path.exists(quell):
        return None

    script = f'''#!/usr/bin/env python3
"""
AUTO-FIX: {fix_id}
Generiert: {datetime.now().isoformat()}
Modul: {treffer["datei"]}
Beschreibung: {treffer["beschreibung"]}
ACHTUNG: Nur ausfuehren nach Dimas Bestaetigung via Telegram.
"""
import shutil, py_compile, os

quell = "{quell}"
bak = quell + ".bak_autofix"
shutil.copy2(quell, bak)
print(f"Backup: {{bak}}")

content = open(quell).read()
if "{treffer["search"]}" not in content:
    print("FEHLER: Anker nicht gefunden. Abbruch.")
else:
    content = content.replace("{treffer["search"]}", "{treffer["replace"]}", 1)
    open(quell, "w").write(content)
    try:
        py_compile.compile(quell, doraise=True)
        print("OK: Fix eingespielt und Syntax geprueft.")
    except Exception as e:
        shutil.copy2(bak, quell)
        print(f"SYNTAX-FEHLER: {{e}} — Rollback!")
'''

    os.makedirs(WERKSTATT, exist_ok=True)
    open(ziel, "w").write(script)
    return fix_id, ziel

def in_memory_speichern(beschreibung, fix_id):
    """Schreibt Selbstdiagnose in kortex_memory.db."""
    try:
        conn = sqlite3.connect(MEMORY_DB)
        ts = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO memories (timestamp,category,content,source,tags) VALUES (?,?,?,?,?)",
            (ts, "selbstdiagnose", beschreibung, "jack_self_improve",
             f"autofix {fix_id if fix_id else 'kein_fix'}")
        )
        conn.commit()
        conn.close()
    except Exception as e:
        import jack_log
        jack_log.log_decision("SELF-IMPROVE-MEMORY-FEHLER", str(e)[:100])

def run():
    treffer_liste = analyse()

    if not treffer_liste:
        import jack_log
        jack_log.log_decision("SELF-IMPROVE", "Analyse abgeschlossen, keine Muster gefunden.")
        return "Keine Verbesserungsvorschlaege."

    meldungen = []
    fixes_heute = []

    for t in treffer_liste:
        result = fix_vorbereiten(t)
        fix_id = None
        if result:
            fix_id, fix_pfad = result
            fixes_heute.append({
                "fix_id": fix_id,
                "pfad": fix_pfad,
                "beschreibung": t["beschreibung"],
                "modul": t["modul"],
                "n": t["n"]
            })
            meldung = (f"[JACK Selbstdiagnose] {t['modul']}: "
                      f"{t['n']}x in 7 Tagen.\n"
                      f"{t['beschreibung']}\n"
                      f"Fix bereit: /approve_{fix_id}")
        else:
            meldung = (f"[JACK Selbstdiagnose] {t['modul']}: "
                      f"{t['n']}x Fehler in 7 Tagen.\n"
                      f"{t['beschreibung']}\n"
                      f"(Kein automatischer Fix verfuegbar - manuell pruefen)")

        in_memory_speichern(meldung, fix_id)
        meldungen.append(meldung)
        import jack_log
        jack_log.log_decision("SELF-IMPROVE", f"{t['modul']} {t['n']}x, fix={fix_id}")

    # Fixes-Log aktualisieren
    bestehend = {}
    try:
        bestehend = json.load(open(FIXES_LOG))
    except Exception:
        pass
    for f in fixes_heute:
        bestehend[f["fix_id"]] = f
    json.dump(bestehend, open(FIXES_LOG, "w"), indent=2, ensure_ascii=False)

    return "\n\n".join(meldungen)

if __name__ == "__main__":
    print(run())
