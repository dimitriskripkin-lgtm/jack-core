import sqlite3
import json

def get_ptr(db_path='/data/data/com.termux/files/home/jack/jack_memory.db'):
    conn = sqlite3.connect(db_path)
    conn.enable_load_extension(True)
    conn.load_extension('/data/data/com.termux/files/home/jack/vec0')
    conn.enable_load_extension(False)
    return conn

def store_embedding(row_id, embedding_vec):
    conn = get_ptr()
    conn.execute('INSERT INTO memory_vec(rowid, embedding) VALUES (?, ?);', (int(row_id), json.dumps(embedding_vec)))
    conn.commit()
    conn.close()

def search_similar(embedding_vec, limit=5, max_distance=0.7):
    conn = get_ptr()
    cursor = conn.execute("""
        SELECT m.id, m.cmd, m.result, v.distance, m.timestamp
        FROM memory m 
        JOIN memory_vec v ON m.rowid = v.rowid 
        WHERE v.embedding MATCH ? AND v.k = ? AND v.distance <= ?
        ORDER BY v.distance ASC, m.timestamp DESC
    """, (json.dumps(embedding_vec), limit, max_distance))
    res = cursor.fetchall()
    conn.close()
    return res
import threading
import queue

memory_queue = queue.Queue()

def _async_worker():
    while True:
        data = memory_queue.get()
        if data is None: break
        text, vector_data = data
        try: pass 
        finally: memory_queue.task_done()

worker_thread = threading.Thread(target=_async_worker, daemon=True)
worker_thread.start()

def queue_new_memory(text, vector_data):
    memory_queue.put((text, vector_data))
