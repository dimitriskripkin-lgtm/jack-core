#!/usr/bin/env python3
"""Diagnose-Snapshot - liest nur, schreibt eine einzige Datei."""
import os, subprocess as sp, sqlite3, json, glob
from datetime import datetime

OUT = "/sdcard/Download/jack_snapshot_" + datetime.now().strftime("%Y%m%d_%H%M") + ".txt"
os.makedirs(os.path.dirname(OUT), exist_ok=True)
lines = []

def run(cmd, timeout=10):
    try:
        r = sp.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return "FEHLER: " + str(e)

def add(title, content):
    lines.append("")
    lines.append("=" * 60)
    lines.append(title)
    lines.append("=" * 60)
    lines.append(str(content))

add("SNAPSHOT", datetime.now().isoformat())
add("UPTIME", run("uptime"))
add("FREE", run("free -h"))
add("DF", run("df -h /data /sdcard 2>/dev/null"))
add("TEMP", run("cat /sys/class/thermal/thermal_zone*/temp 2>/dev/null"))
add("PROZESSE", run("ps aux | grep -E 'jack_|ollama|mosquitto|sshd|crond|python3' | grep -v grep"))
add("RUNIT STATUS", run("sv status /data/data/com.termux/files/usr/var/service/* 2>/dev/null || sv status ~/.termux/service/* 2>/dev/null"))
add("CRONTAB", run("crontab -l"))
add("STOP-DATEIEN", run("ls -la ~/.jack_lerner_stop ~/.jack_explore_pause 2>&1"))
add("GIT STATUS", run("cd ~/jack && git log --oneline -5 && echo '---' && git status --short"))
add("PYTHON-DATEIEN ANZAHL", run("ls ~/jack/*.py 2>/dev/null | wc -l"))
add("JACK_STARTUP.SH", run("cat ~/jack/jack_startup.sh"))
add("JACK_CORTEX.PY GROESSE", run("wc -l ~/jack/jack_cortex.py 2>/dev/null"))

# DBs
add("DATENBANKEN UEBERSICHT", "")
for db_path in sorted(glob.glob(os.path.expanduser("~/jack/*.db"))):
    name = os.path.basename(db_path)
    size = os.path.getsize(db_path)
    try:
        con = sqlite3.connect(db_path)
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        rows_per_table = {}
        for t in tables:
            try:
                n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                rows_per_table[t] = n
            except: pass
        con.close()
        add(f"DB: {name} ({size} bytes)", json.dumps(rows_per_table, indent=2))
    except Exception as e:
        add(f"DB: {name} FEHLER", str(e))

# Logs letzte 20 Zeilen
for logname in ["orchestrator.log", "cortex_stdout.log", "autolearn.log", "startup.log", "autolearn_stdout.log"]:
    p = os.path.expanduser("~/jack/" + logname)
    if os.path.exists(p):
        add("LOG: " + logname, run(f"tail -20 {p}"))

for logname in ["vinted.log", "briefing.log", "maintenance.log"]:
    p = os.path.expanduser("~/jack/logs/" + logname)
    if os.path.exists(p):
        add("LOG: logs/" + logname, run(f"tail -20 {p}"))

# Config ohne Secrets
add("CONFIG.INI (ohne Secrets)", run("grep -v token ~/jack/config.ini 2>/dev/null"))

# faehigkeiten registry
add("FAEHIGKEITEN STAT", run("cd ~/jack && python3 jack_faehigkeiten.py liste 2>/dev/null | head -80"))

# skills stat
try:
    con = sqlite3.connect(os.path.expanduser("~/jack/jack_skills.db"))
    rows = con.execute("SELECT state, COUNT(*) FROM skills GROUP BY state").fetchall()
    con.close()
    add("SKILLS STAT", str(rows))
except Exception as e:
    add("SKILLS STAT FEHLER", str(e))

# errors stat
try:
    con = sqlite3.connect(os.path.expanduser("~/jack/jack_errors.db"))
    rows = con.execute("SELECT resolved, COUNT(*) FROM errors GROUP BY resolved").fetchall()
    last10 = con.execute("SELECT id, timestamp, module, error_msg FROM errors ORDER BY id DESC LIMIT 10").fetchall()
    con.close()
    add("ERRORS STAT", "Gruppiert: " + str(rows) + chr(10) + "Letzte 10:" + chr(10) + chr(10).join(str(r) for r in last10))
except Exception as e:
    add("ERRORS STAT FEHLER", str(e))

# services run-Skripte
add("DIENSTE IM SV", run("ls -la /data/data/com.termux/files/usr/var/service/ 2>/dev/null"))

# termux-boot
add("TERMUX-BOOT", run("ls ~/.termux/boot/ 2>/dev/null"))

# patch vorschlaege
add("PATCH_VORSCHLAEGE", run("ls -la ~/jack/patch_vorschlaege/ 2>/dev/null"))

with open(OUT, "w", encoding="utf-8") as f:
    f.write(chr(10).join(lines))

print("SNAPSHOT GESCHRIEBEN:", OUT)
print("Groesse:", os.path.getsize(OUT), "Bytes")
print("Zeilen:", len(lines))
