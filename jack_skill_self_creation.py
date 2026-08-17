#!/usr/bin/env python3
import sqlite3
import os
import json
from datetime import datetime

DB_SKILLS = os.path.expanduser("~/jack/jack_skills.db")

def create_skill_from_audit():
    print("=== SCHRITT 1: AUDIT REPORT LESEN ===")
    if not os.path.exists('audit_report.md'):
        print("FEHLER: audit_report.md nicht gefunden.")
        return
    
    with open('audit_report.md', 'r', encoding='utf-8') as f:
        report_content = f.read()
    
    # Metriken extrahieren (einfaches Parsing)
    lines = report_content.split('\n')
    skills_count = "Unbekannt"
    context_count = "Unbekannt"
    for line in lines:
        if "Skills gesamt:" in line:
            skills_count = line.split(":")[1].strip()
        if "Context Eintraege:" in line:
            context_count = line.split(":")[1].strip()
            
    print(f"EXTRAKTION_OK: Skills={skills_count}, Context={context_count}")

    print("=== SCHRITT 2: NEUEN SKILL DEFINIEREN ===")
    skill_name = "daily_system_health_check"
    description = f"Automatischer System-Check. Verifiziert DB-Integrität und archiviert .bak Dateien. (Stand: {skills_count} Skills, {context_count} Context-Einträge)"
    
    # Der Plan ist ein Aufruf an das soeben bewährte Skript
    plan_json = json.dumps({
        "name": "daily_system_health_check",
        "steps": [
            {"type": "exec", "cmd": "cd ~/jack && python3 jack_audit_run.py", "timeout": 60}
        ],
        "success_criteria": [
            {"type": "contains", "value": "AUDIT_COMPLETE", "step": 1, "desc": "Audit erfolgreich durchlaufen"}
        ]
    }, indent=2)

    print("PLAN_JSON_GENERIERT")

    print("=== SCHRITT 3: SKILL IN DB SPEICHERN (CANDIDATE) ===")
    conn = sqlite3.connect(DB_SKILLS)
    c = conn.cursor()
    
    # Prüfen ob Skill schon existiert, wenn ja, updaten
    c.execute("SELECT name FROM skills WHERE name=?", (skill_name,))
    if c.fetchone():
        c.execute("""
            UPDATE skills 
            SET description=?, plan_json=?, last_ts=CURRENT_TIMESTAMP 
            WHERE name=?
        """, (description, plan_json, skill_name))
        print("SKILL_AKTUALISIERT")
    else:
        c.execute("""
            INSERT INTO skills (name, description, plan_json, state, executions, successes, created_ts, last_ts)
            VALUES (?, ?, ?, 'CANDIDATE', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (skill_name, description, plan_json))
        print("SKILL_ERSTELLT")
        
    conn.commit()
    conn.close()

    print("=== SCHRITT 4: VERIFIZIERUNG ===")
    conn = sqlite3.connect(DB_SKILLS)
    c = conn.cursor()
    c.execute("SELECT name, state FROM skills WHERE name=?", (skill_name,))
    result = c.fetchone()
    conn.close()
    
    if result and result[1] == 'CANDIDATE':
        print(f"ERFOLG: Skill '{result[0]}' ist als {result[1]} in der DB registriert.")
    else:
        print("FEHLER: Skill konnte nicht verifiziert werden.")

if __name__ == "__main__":
    try:
        create_skill_from_audit()
    except Exception as e:
        print(f"FEHLER: {e}")
        import traceback
        traceback.print_exc()
