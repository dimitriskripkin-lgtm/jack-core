import sqlite3, os, hashlib
from datetime import datetime

DB = os.path.expanduser("~/jack/jack_memory.db")

_orig_connect = sqlite3.connect

def _connect_with_wal(*args, **kwargs):
    conn = _orig_connect(*args, **kwargs)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

sqlite3.connect = _connect_with_wal

def init():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memory
                 (id TEXT PRIMARY KEY, cmd TEXT, result TEXT, intent TEXT, time TEXT)''')
    # Full-Text-Search virtual table
    c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(cmd, result)''')
    conn.commit()
    conn.close()

def save(cmd, result, intent="unknown"):
    init()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    uid = hashlib.md5((cmd + str(datetime.now())).encode()).hexdigest()[:16]
    c.execute("INSERT OR REPLACE INTO memory VALUES (?,?,?,?,?)",
              (uid, cmd, result, intent, str(datetime.now())))
    c.execute("INSERT INTO memory_fts VALUES (?,?)", (cmd, result))
    conn.commit()
    conn.close()

def query(text, n=5):
    init()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    # FTS search
    c.execute("SELECT cmd, result FROM memory_fts WHERE memory_fts MATCH ? LIMIT ?", (text, n))
    rows = c.fetchall()
    if not rows:
        # Fallback LIKE
        c.execute("SELECT cmd, result FROM memory WHERE cmd LIKE ? OR result LIKE ? LIMIT ?",
                  (f"%{text}%", f"%{text}%", n))
        rows = c.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    save("Xiaomi Status abfragen", "Akku 87%, Load 0.5", "status")
    save("Scanner starten auf Xiaomi", "Prozess gestartet PID 1234", "shell")
    print("Query 'Akku':", query("Akku"))
    print("Query 'Status':", query("Status"))
