#!/usr/bin/env python3
"""Zentraler SQLite Write-Queue: ein Thread schreibt, alle anderen queuen.
Loest das Thread-Safety Problem ohne Locking."""
import sqlite3, threading, queue, os, time
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

_queues = {}
_workers = {}
_lock = threading.Lock()

def _worker(db_path, q):
    while True:
        item = q.get()
        if item is None:
            break
        sql, params, result_q = item
        try:
            con = sqlite3.connect(db_path)
            con.execute('PRAGMA journal_mode=WAL')
            cur = con.execute(sql, params)
            con.commit()
            if result_q is not None:
                result_q.put(('ok', cur.lastrowid))
            con.close()
        except Exception as e:
            if result_q is not None:
                result_q.put(('err', str(e)))
        finally:
            q.task_done()

def _get_queue(db_path):
    with _lock:
        if db_path not in _queues:
            q = queue.Queue()
            t = threading.Thread(target=_worker, args=(db_path, q), daemon=True, name='dbwriter-' + os.path.basename(db_path))
            t.start()
            _queues[db_path] = q
            _workers[db_path] = t
        return _queues[db_path]

def write(db_path, sql, params=(), wait=False, timeout=5):
    """Schreibt sicher in SQLite via Queue. wait=True: wartet auf Ergebnis."""
    q = _get_queue(db_path)
    if wait:
        rq = queue.Queue()
        q.put((sql, params, rq))
        try:
            status, val = rq.get(timeout=timeout)
            return status == 'ok', val
        except queue.Empty:
            return False, 'timeout'
    else:
        q.put((sql, params, None))
        return True, None

def status():
    with _lock:
        return {os.path.basename(p): q.qsize() for p, q in _queues.items()}

if __name__ == '__main__':
    print('Queue-Status:', status())
