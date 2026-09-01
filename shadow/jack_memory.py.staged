import sqlite3, os, hashlib
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
from datetime import datetime

DB = os.path.expanduser('~/jack/jack_memory.db')

def init():
    conn = sqlite3.connect(DB)
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=5000')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memory
                 (id TEXT PRIMARY KEY, cmd TEXT, result TEXT, intent TEXT,
                  time TEXT, timestamp TEXT, source TEXT,
                  parent_id TEXT DEFAULT NULL, kontext_typ TEXT DEFAULT "chat")''')
    c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
                 USING fts5(cmd, result)''')
    conn.commit()
    conn.close()

def save(cmd, result, intent='unknown'):
    init()
    import jack_db_queue as _dq
    uid = hashlib.md5((cmd + str(datetime.now())).encode()).hexdigest()[:16]
    ts = str(datetime.now())
    ok, rowid = _dq.write(DB,
        'INSERT OR REPLACE INTO memory(id,cmd,result,intent,time,timestamp,source) VALUES(?,?,?,?,?,?,?)',
        (uid, cmd, result, intent, ts, ts, 'manual'),
        wait=True)
    if ok:
        # FTS sync: erst loeschen, dann neu einfuegen - verhindert Duplikate
        _dq.write(DB, 'DELETE FROM memory_fts WHERE rowid IN (SELECT rowid FROM memory WHERE id=?)', (uid,))
        _dq.write(DB, 'INSERT INTO memory_fts(rowid,cmd,result) SELECT rowid,cmd,result FROM memory WHERE id=?', (uid,))
    return ok

def query(text, n=5):
    init()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('SELECT cmd, result FROM memory_fts WHERE memory_fts MATCH ? LIMIT ?', (text, n))
    rows = c.fetchall()
    if not rows:
        c.execute('SELECT cmd, result FROM memory WHERE cmd LIKE ? OR result LIKE ? LIMIT ?',
                  (f'%{text}%', f'%{text}%', n))
        rows = c.fetchall()
    conn.close()
    return rows

if __name__ == '__main__':
    save('Xiaomi Status abfragen', 'Akku 87%, Load 0.5', 'status')
    print('Query Akku:', query('Akku'))
