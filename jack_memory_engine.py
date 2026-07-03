#!/usr/bin/env python3
import json, sqlite3, os, re
from datetime import datetime
from pathlib import Path

JACK_HOME = "/data/data/com.termux/files/home"
MEMORY_DB = f"{JACK_HOME}/jack/jack_memory.db"
IDENTITY_FILE = f"{JACK_HOME}/jack/jack_identity.json"

class MemoryEngine:
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(MEMORY_DB) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY,
                    ts TEXT,
                    logfile TEXT,
                    error_text TEXT,
                    solution TEXT,
                    fixed INTEGER DEFAULT 0
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS solutions (
                    id INTEGER PRIMARY KEY,
                    ts TEXT,
                    error_pattern TEXT,
                    solution_cmd TEXT,
                    success_rate REAL,
                    applied_count INTEGER DEFAULT 0
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id INTEGER PRIMARY KEY,
                    pattern TEXT,
                    frequency INTEGER,
                    last_seen TEXT,
                    severity TEXT
                )
            """)
            con.commit()
    
    def log_error(self, logfile, error_text, solution=""):
        with sqlite3.connect(MEMORY_DB) as con:
            con.execute(
                "INSERT INTO errors (ts, logfile, error_text, solution) VALUES (?, ?, ?, ?)",
                (datetime.now().isoformat(), logfile, error_text, solution)
            )
            con.commit()
    
    def log_solution(self, error_pattern, solution_cmd, success=True):
        with sqlite3.connect(MEMORY_DB) as con:
            con.execute(
                "INSERT INTO solutions (ts, error_pattern, solution_cmd, success_rate, applied_count) VALUES (?, ?, ?, ?, 1)",
                (datetime.now().isoformat(), error_pattern, solution_cmd, 1.0 if success else 0.0)
            )
            con.commit()
    
    def detect_pattern(self, error_text):
        patterns = {
            "connection_refused": r"connection refused|connection timeout",
            "timeout": r"timeout|timed out",
            "permission_denied": r"permission denied",
            "not_found": r"not found|no such file",
            "crash": r"crash|segfault|fatal",
        }
        for name, pattern in patterns.items():
            if re.search(pattern, error_text, re.IGNORECASE):
                return name
        return "unknown"
    
    def get_recent_solutions(self, pattern, limit=5):
        with sqlite3.connect(MEMORY_DB) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM solutions WHERE error_pattern = ? ORDER BY ts DESC LIMIT ?",
                (pattern, limit)
            ).fetchall()
            return [dict(r) for r in rows]
    
    def get_error_history(self, limit=20):
        with sqlite3.connect(MEMORY_DB) as con:
            con.row_factory = sqlite3.Row
            rows = con.execute(
                "SELECT * FROM errors ORDER BY ts DESC LIMIT ?", (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

if __name__ == "__main__":
    engine = MemoryEngine()
    print("[MEMORY] ✓ Engine initialized")
