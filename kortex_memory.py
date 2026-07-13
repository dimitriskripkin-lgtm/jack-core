import sqlite3, json, os, sys
from datetime import datetime

DB_PATH = os.path.expanduser("~/jack/kortex_memory.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        category TEXT DEFAULT 'general',
        content TEXT NOT NULL,
        source TEXT DEFAULT 'manual',
        tags TEXT DEFAULT '')""")
    c.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
        USING fts5(content, category, tags,
        content='memories', content_rowid='id')""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS mem_ai
        AFTER INSERT ON memories BEGIN
            INSERT INTO memories_fts(rowid, content, category, tags)
            VALUES (new.id, new.content, new.category, new.tags);
        END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS mem_ad
        AFTER DELETE ON memories BEGIN
            INSERT INTO memories_fts(memories_fts, rowid, content, category, tags)
            VALUES ('delete', old.id, old.content, old.category, old.tags);
        END""")
    conn.commit()
    conn.close()

def add_memory(content, category="general", source="manual", tags=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = datetime.now().isoformat()
    c.execute("INSERT INTO memories (timestamp,category,content,source,tags) VALUES (?,?,?,?,?)",
        (ts, category, content, source, tags))
    conn.commit()
    mid = c.lastrowid
    conn.close()
    return {"id": mid, "timestamp": ts, "status": "saved"}

def search_memory(query, limit=10):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("""SELECT m.id, m.timestamp, m.category, m.content, m.tags
            FROM memories_fts
            JOIN memories m ON memories_fts.rowid = m.id
            WHERE memories_fts MATCH ? ORDER BY rank LIMIT ?""", (query, limit))
        rows = c.fetchall()
        if rows:
            ids = ",".join(str(r[0]) for r in rows)
            c.execute(f"UPDATE memories SET access_count = access_count + 1 WHERE id IN ({ids})")
            conn.commit()
    except Exception as e:
        conn.close()
        return {"error": str(e)}
    conn.close()
    return [{"id":r[0],"timestamp":r[1],"category":r[2],"content":r[3],"tags":r[4]} for r in rows]

def get_recent(limit=20):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id,timestamp,category,content,tags FROM memories ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"id":r[0],"timestamp":r[1],"category":r[2],"content":r[3],"tags":r[4]} for r in rows]

init_db()
