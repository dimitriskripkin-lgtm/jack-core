#!/usr/bin/env python3
"""jack_circuit_breaker.py — Gemini Fehler-Counter + Ollama-Failover."""
MODULE_VERSION = 2

import os, sys, json, time
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_circuit_breaker")

STATE_FILE = os.path.join(J, "circuit_breaker_state.json")
MAX_FAILS  = 3
RESET_SECS = 1800  # 30min

def _load():
    try: return json.load(open(STATE_FILE))
    except Exception: return {"fails": 0, "open_since": 0, "state": "closed"}

def _save(s): json.dump(s, open(STATE_FILE,'w'))

def is_open() -> bool:
    s = _load()
    if s["state"] != "open": return False
    if time.time() - s["open_since"] > RESET_SECS:
        _save({"fails":0,"open_since":0,"state":"closed"})
        log.info("Circuit Breaker: reset nach 30min")
        return False
    return True

def record_fail():
    s = _load()
    s["fails"] += 1
    if s["fails"] >= MAX_FAILS:
        s["state"] = "open"
        s["open_since"] = time.time()
        log.warn(f"Circuit Breaker OPEN nach {s['fails']} Fails — Ollama-Fallback aktiv")
        try:
            import jack_telegram as _jt
            _jt.send(f"⚡ Circuit Breaker offen — Gemini {s['fails']}x gefailed. Ollama übernimmt für 30min.")
        except Exception: pass
    _save(s)

def record_success():
    s = _load()
    if s["fails"] > 0:
        s = {"fails":0,"open_since":0,"state":"closed"}
        _save(s)
        log.info("Circuit Breaker: reset nach Erfolg")

def status() -> dict: return _load()
