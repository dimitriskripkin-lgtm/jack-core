#!/usr/bin/env python3
"""ui_agent/logger.py - Zentrale Transition- + Activity-Logs + UTG."""
import os, json, time, sqlite3

H = "/data/data/com.termux/files/home/jack"
DB = os.path.join(H, "jack_memory.db")
TRANS_DIR = os.path.join(H, "ui_agent", "transitions")
os.makedirs(TRANS_DIR, exist_ok=True)

def _conn():
    return sqlite3.connect(DB, timeout=10)

def log_transition(before_hash, action, target, after_hash, success, extra=None):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    extra = extra or {}
    entry = {
        "ts": ts, "before": before_hash, "action": action,
        "target": str(target)[:80], "after": after_hash,
        "success": bool(success), "extra": extra
    }
    day = time.strftime("%Y%m%d")
    path = os.path.join(TRANS_DIR, f"transitions_{day}.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    try:
        con = _conn()
        con.execute(
            "INSERT INTO activity_log (ts, device, event_type, details, summary) VALUES (?,?,?,?,?)",
            (ts, "xiaomi", "ui_transition",
             json.dumps(entry, ensure_ascii=False),
             f"{action}:{str(target)[:40]} → {after_hash[:8]} ({'ok' if success else 'fail'})")
        )
        con.execute(
            "INSERT INTO ui_transitions (ts, before_hash, after_hash, action, target, success, package, activity, extra) VALUES (?,?,?,?,?,?,?,?,?)",
            (ts, before_hash, after_hash, action, str(target)[:80], 1 if success else 0,
             extra.get("pkg") or extra.get("package"), extra.get("act") or extra.get("activity"),
             json.dumps(extra, ensure_ascii=False))
        )
        con.commit()
        con.close()
    except Exception as e:
        print(f"[logger] DB Fehler: {e}", flush=True)
    return entry

def log_vision(analysis, source="ui_agent"):
    try:
        con = _conn()
        con.execute("INSERT INTO vision_log (ts, analysis, source) VALUES (?,?,?)",
                    (time.strftime("%Y-%m-%dT%H:%M:%S"), analysis[:2000], source))
        con.commit()
        con.close()
    except Exception as e:
        print(f"[logger] vision_log Fehler: {e}", flush=True)
