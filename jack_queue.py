#!/usr/bin/env python3
"""JACK Queue: Thread-safe Write-Queue fuer DB-Operationen."""
import queue,threading,sqlite3,os

_q=queue.Queue()
_lock=threading.Lock()

def enqueue(fn,*args,**kwargs):
    _q.put((fn,args,kwargs))

def _worker():
    while True:
        fn,args,kwargs=_q.get()
        try:
            with _lock: fn(*args,**kwargs)
        except Exception as e:
            try: import jack_log; jack_log.log_decision('QUEUE-ERR',str(e)[:100])
            except Exception: pass
        finally: _q.task_done()

_t=threading.Thread(target=_worker,daemon=True)
_t.start()
