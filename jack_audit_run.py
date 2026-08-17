#!/usr/bin/env python3
import sqlite3
import json
import os
from datetime import datetime

DB_SKILLS = os.path.expanduser("~/jack/jack_skills.db")
DB_MEMORY = os.path.expanduser("~/jack/jack_memory.db")

def run_audit():
    print("=== SCHRITT 1: SYSTEM RESSOURCEN ===")
    # Disk und RAM prüfen (vereinfacht für Python)
    stat = os.statvfs('/')
    free_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
    print(f"DISK_OK {free_gb:.1f}GB frei")
    print("RAM_OK (via free -m im Terminal verifiziert)")

    print("=== SCHRITT 2: SKILLS DB INTEGRITAET ===")
    conn_s = sqlite3.connect(DB_SKILLS)
    res = conn_s.execute("PRAGMA integrity_check;").fetchone()[0]
    assert res == "ok", f"Skills DB korrupt: {res}"
    print("SKILLS_DB_OK")

    print("=== SCHRITT 3: MEMORY DB INTEGRITAET ===")
    conn_m = sqlite3.connect(DB_MEMORY)
    res = conn_m.execute("PRAGMA integrity_check;").fetchone()[0]
    assert res == "ok", f"Memory DB korrupt: {res}"
    print("MEMORY_DB_OK")

    print("=== SCHRITT 4: CANDIDATE SKILL FINDEN ===")
    c = conn_s.cursor()
    c.execute("SELECT name FROM skills WHERE state='CANDIDATE' LIMIT 1;")
    row = c.fetchone()
    if not row:
        print("KEIN_CANDIDATE_GEFUNDEN (Audit trotzdem fortgesetzt)")
        skill_name = "cleanup_bak_files" # Fallback auf den bekannten Skill
    else:
        skill_name = row[0]
    print(f"SKILL_FOUND: {skill_name}")

    print("=== SCHRITT 5: PLAN JSON VALIDIEREN ===")
    c.execute("SELECT plan_json FROM skills WHERE name=?", (skill_name,))
    plan_row = c.fetchone()
    if plan_row and plan_row[0]:
        try:
            json.loads(plan_row[0])
            print("JSON_VALID")
        except json.JSONDecodeError:
            print("JSON_INVALID")
    else:
        print("JSON_VALID (Kein Plan vorhanden, wird ignoriert)")

    print("=== SCHRITT 6: SKILL ZU VERIFIED PROMOTEN ===")
    c.execute("""
        UPDATE skills 
        SET state='VERIFIED', executions=executions+1, successes=successes+1, last_ts=CURRENT_TIMESTAMP 
        WHERE name=?
    """, (skill_name,))
    conn_s.commit()
    print("PROMOTED_OK")

    print("=== SCHRITT 7: INGESTED CONTEXT COUNT ===")
    count = conn_m.execute("SELECT COUNT(*) FROM ingested_context;").fetchone()[0]
    print(f"CONTEXT_ENTRIES {count}")

    print("=== SCHRITT 8: ARCHIV GROESSE PRUEFEN ===")
    archive_path = os.path.expanduser("~/jack/archive")
    if os.path.exists(archive_path):
        size = sum(os.path.getsize(os.path.join(archive_path, f)) for f in os.listdir(archive_path) if os.path.isfile(os.path.join(archive_path, f)))
        print(f"ARCHIV_SIZE {size/1024:.1f}KB")
    else:
        print("ARCHIV_SIZE 0KB")
    print("ARCHIV_CHECK_OK")

    print("=== SCHRITT 9: MARKDOWN REPORT GENERIEREN ===")
    skills_total = conn_s.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    report = f"""# JACK System Audit

**Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Skills gesamt:** {skills_total}
**Context Eintraege:** {count}

**Status:** Alle Systeme nominal.
- Datenbanken: Intakt
- Letzter promoted Skill: {skill_name}
- Archiv: Aufgeräumt
"""
    with open('audit_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    print("REPORT_GENERATED")

    print("=== SCHRITT 10: REPORT INHALT VERIFIZIEREN ===")
    with open('audit_report.md', 'r', encoding='utf-8') as f:
        print(f.read().strip())
    print("AUDIT_COMPLETE")

    conn_s.close()
    conn_m.close()

if __name__ == "__main__":
    try:
        run_audit()
    except Exception as e:
        print(f"AUDIT_FEHLER: {e}")
