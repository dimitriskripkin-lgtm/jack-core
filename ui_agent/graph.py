#!/usr/bin/env python3
"""ui_agent/graph.py - UI-Transition-Graph Abfragen."""
import sqlite3, os
DB = "/data/data/com.termux/files/home/jack/jack_memory.db"

def successors(before_hash, limit=10):
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT after_hash, action, target, package, COUNT(*) as n FROM ui_transitions "
        "WHERE before_hash LIKE ? AND success=1 GROUP BY after_hash, action ORDER BY n DESC LIMIT ?",
        (before_hash[:16]+"%", limit)
    ).fetchall()
    con.close()
    return rows

def packages():
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT package, COUNT(*) FROM ui_transitions WHERE package IS NOT NULL GROUP BY package ORDER BY 2 DESC"
    ).fetchall()
    con.close()
    return rows

if __name__ == "__main__":
    print("=== Packages im Graph ===")
    for p, n in packages():
        print(f"  {n:4d}  {p}")
    print("\n=== Nachfolger von Home-Hash ===")
    for r in successors("13bdf63b"):
        print(r)
