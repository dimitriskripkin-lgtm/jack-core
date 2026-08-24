#!/usr/bin/env python3
"""ui_agent/skills.py - Skills aus Transitions / Demonstrationen."""
import json, time, sqlite3, os
DB = "/data/data/com.termux/files/home/jack/jack_memory.db"

def _conn():
    return sqlite3.connect(DB, timeout=10)

def save_skill(name, steps, start_hash, end_hash):
    con = _conn()
    con.execute(
        "INSERT INTO ui_skills (name, created_ts, steps, start_hash, end_hash) VALUES (?,?,?,?,?)",
        (name, time.strftime("%Y-%m-%dT%H:%M:%S"), json.dumps(steps, ensure_ascii=False), start_hash, end_hash)
    )
    con.commit()
    con.close()
    print(f"Skill gespeichert: {name} ({len(steps)} Schritte)")

def list_skills():
    con = _conn()
    rows = con.execute("SELECT id, name, success_count, fail_count, created_ts FROM ui_skills ORDER BY id DESC").fetchall()
    con.close()
    return rows

def get_skill(name):
    con = _conn()
    row = con.execute("SELECT steps, start_hash, end_hash FROM ui_skills WHERE name=? ORDER BY id DESC LIMIT 1", (name,)).fetchone()
    con.close()
    if not row:
        return None
    return {"steps": json.loads(row[0]), "start_hash": row[1], "end_hash": row[2]}

if __name__ == "__main__":
    print("=== Vorhandene Skills ===")
    for r in list_skills():
        print(r)
