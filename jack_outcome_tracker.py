"""Outcome-Tracking: Jede Ausfuehrung wird gespeichert (Qwen 21.08.)
JACK lernt welche Befehle funktionieren, welche nicht."""
import sqlite3, os, datetime

J = os.path.expanduser("~/jack")
DB_PATH = os.path.join(J, "jack_outcomes.db")

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            cmd TEXT,
            rc INTEGER,
            output TEXT,
            success INTEGER
        )
    """)
    con.commit()
    con.close()

def log_outcome(cmd, rc, output):
    try:
        con = sqlite3.connect(DB_PATH, timeout=5)
        success = 1 if rc == 0 and 'error' not in output.lower() else 0
        con.execute("""
            INSERT INTO outcomes (timestamp, cmd, rc, output, success)
            VALUES (?, ?, ?, ?, ?)
        """, (
            datetime.datetime.now().isoformat(),
            cmd[:500],
            rc,
            output[:1000],
            success
        ))
        con.commit()
        con.close()
    except Exception:
        pass

def get_stats(limit=20):
    try:
        con = sqlite3.connect(DB_PATH, timeout=5)
        rows = con.execute("""
            SELECT cmd, COUNT(*) as total, 
                   SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successes
            FROM outcomes
            GROUP BY cmd
            ORDER BY total DESC
            LIMIT ?
        """, (limit,)).fetchall()
        con.close()
        return rows
    except Exception:
        return []

def get_recent(limit=10):
    try:
        con = sqlite3.connect(DB_PATH, timeout=5)
        rows = con.execute("""
            SELECT timestamp, cmd, rc, success
            FROM outcomes
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        con.close()
        return rows
    except Exception:
        return []

init_db()
