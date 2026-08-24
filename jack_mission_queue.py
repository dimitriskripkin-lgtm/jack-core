#!/data/data/com.termux/files/usr/bin/python3
"""Einfache Mission-Queue: JSON-Liste, nächste aktiv setzen."""
import json, sys
from pathlib import Path
H = Path("/data/data/com.termux/files/home/jack")
QUEUE = H / "jack_mission_queue.json"
ACTIVE = H / "jack_mission_active.json"

def load_q():
    if QUEUE.is_file():
        return json.loads(QUEUE.read_text())
    return []

def save_q(q):
    QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False))

def enqueue(mission: dict):
    q = load_q()
    q.append(mission)
    save_q(q)
    print("ENQUEUED", mission.get("id"), "len", len(q))

def next_active():
    q = load_q()
    if not q:
        print("QUEUE_EMPTY"); return 1
    m = q.pop(0)
    save_q(q)
    if m.get("forbidden") is None:
        print("FAIL_CLOSED: forbidden missing in queued mission"); return 2
    ACTIVE.write_text(json.dumps(m, indent=2, ensure_ascii=False))
    print("ACTIVE", m.get("id"), "rest", len(q))
    return 0

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "next":
        raise SystemExit(next_active())
    print("Usage: jack_mission_queue.py next | or import enqueue()")
