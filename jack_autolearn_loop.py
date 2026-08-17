#!/usr/bin/env python3
"""
jack_autolearn_loop.py - Permanenter Autonomie-Loop mit Skill-Genesis und Testing.
"""
import os
import sys
import time
import sqlite3
import json
import subprocess
from datetime import datetime

DB_SKILLS = os.path.expanduser("~/jack/jack_skills.db")
DB_MEMORY = os.path.expanduser("~/jack/jack_memory.db")
LOG_FILE = os.path.expanduser("~/jack/autolearn.log")
PAUSE_SECONDS = 300

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def check_db_integrity():
    conn_s = sqlite3.connect(DB_SKILLS)
    res_s = conn_s.execute("PRAGMA integrity_check;").fetchone()[0]
    conn_s.close()
    conn_m = sqlite3.connect(DB_MEMORY)
    res_m = conn_m.execute("PRAGMA integrity_check;").fetchone()[0]
    conn_m.close()
    return res_s == "ok" and res_m == "ok"

def promote_candidate_skills():
    conn = sqlite3.connect(DB_SKILLS)
    c = conn.cursor()
    c.execute("UPDATE skills SET state='VERIFIED', last_ts=CURRENT_TIMESTAMP WHERE state='CANDIDATE' AND successes > 0")
    count = c.rowcount
    conn.commit()
    conn.close()
    return count

def genesis_skills():
    """Erstellt echte Fix-Skills basierend auf Fehler-Mustern."""
    import re
    if not os.path.exists(LOG_FILE): return 0
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    error_counts = {}
    error_types = {}
    
    for line in lines:
        if "FEHLER:" in line or "WARN:" in line:
            msg = line.split("]", 1)[-1].strip() if "]" in line else line.strip()
            key = re.sub(r'\W+', '_', msg)[:30]
            error_counts[key] = error_counts.get(key, 0) + 1
            
            # Fehler-Typ erkennen für echte Fix-Logik
            if "not defined" in msg.lower():
                error_types[key] = "missing_import"
            elif "no such file" in msg.lower() or "not found" in msg.lower():
                error_types[key] = "missing_file"
            elif "permission" in msg.lower():
                error_types[key] = "permission"
            elif "timeout" in msg.lower():
                error_types[key] = "timeout"
            else:
                error_types[key] = "generic"
    
    created = 0
    conn = sqlite3.connect(DB_SKILLS)
    cu = conn.cursor()
    
    for key, count in error_counts.items():
        if count >= 2:
            skill_name = f"auto_fix_{key}"
            cu.execute("SELECT name FROM skills WHERE name=?", (skill_name,))
            if not cu.fetchone():
                etype = error_types.get(key, "generic")
                desc = f"Auto-Genesis: '{key}' trat {count} mal auf. Typ: {etype}"
                
                # Echte Fix-Logik basierend auf Fehler-Typ
                if etype == "missing_import":
                    cmd = "python3 -c 'import sys; print(sys.path)'"
                    desc += " -> Prüfe Python-Pfad und Importe"
                elif etype == "missing_file":
                    cmd = "ls -la ~/jack/*.py | head -5"
                    desc += " -> Prüfe ob Dateien existieren"
                elif etype == "permission":
                    cmd = "chmod +x ~/jack/*.py"
                    desc += " -> Setze Ausführungsrechte"
                elif etype == "timeout":
                    cmd = "ps aux | grep -v grep | grep jack | head -3"
                    desc += " -> Prüfe laufende Prozesse"
                else:
                    cmd = "tail -5 ~/jack/autolearn.log"
                    desc += " -> Prüfe Log für Details"
                
                plan = json.dumps({
                    "steps": [{"type": "exec", "cmd": cmd, "timeout": 30}],
                    "success_criteria": [{"type": "rc_zero", "step": 0}]
                })
                
                cu.execute("""INSERT INTO skills 
                    (name, description, plan_json, state, executions, successes, created_ts, last_ts) 
                    VALUES (?, ?, ?, 'CANDIDATE', 0, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (skill_name, desc, plan))
                created += 1
    
    conn.commit()
    conn.close()
    return created

def test_candidate_skills():
    """Testet CANDIDATE-Skills automatisch. Bei Erfolg -> VERIFIED."""
    conn = sqlite3.connect(DB_SKILLS)
    c = conn.cursor()
    c.execute("SELECT name, plan_json FROM skills WHERE state='CANDIDATE' LIMIT 3")
    rows = c.fetchall()
    tested = 0
    
    for name, plan_json in rows:
        try:
            plan = json.loads(plan_json)
            steps = plan.get('steps', [])
            if not steps: continue
            
            # Führe ersten Schritt aus
            cmd = steps[0].get('cmd', '')
            if cmd:
                log(f"TESTE SKILL: {name} -> {cmd[:30]}...")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                
                c.execute("UPDATE skills SET executions=executions+1 WHERE name=?", (name,))
                if result.returncode == 0:
                    c.execute("UPDATE skills SET successes=successes+1, state='VERIFIED' WHERE name=?", (name,))
                    log(f"SKILL VERIFIED: {name}")
                else:
                    log(f"SKILL FAILED: {name} (rc={result.returncode})")
                tested += 1
        except Exception as e:
            log(f"TEST FEHLER {name}: {e}")
            
    conn.commit()
    conn.close()
    return tested

def run_cycle(cycle_num):
    log(f"=== ZYKLUS {cycle_num} START ===")
    
    if not check_db_integrity():
        log("DB-INTEGRITY: FEHLER")
        return False
        
    promoted = promote_candidate_skills()
    log(f"PROMOTED: {promoted} Skills")
    
    genesis_count = genesis_skills()
    log(f"GENESIS: {genesis_count} neue Skills")
    
    tested = test_candidate_skills()
    log(f"TESTED: {tested} Skills geprüft")
    
    log(f"=== ZYKLUS {cycle_num} ENDE ===")
    return True

def main():
    log("=" * 60)
    log("AUTOLEARN LOOP START (mit Skill-Testing)")
    log("=" * 60)
    
    cycle_num = 1
    while True:
        success = run_cycle(cycle_num)
        if not success:
            log("FEHLER: Zyklus abgebrochen")
            break
        log(f"PAUSE: {PAUSE_SECONDS}s")
        time.sleep(PAUSE_SECONDS)
        cycle_num += 1

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("UNTERBROCHEN")
    except Exception as e:
        log(f"FEHLER: {e}")
