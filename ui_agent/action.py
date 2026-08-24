#!/usr/bin/env python3
"""ui_agent/action.py - Tippen mit automatischem Transition-Log."""
import sys, os, time
sys.path.insert(0, os.path.expanduser("~/jack"))
sys.path.insert(0, os.path.expanduser("~/jack/ui_agent"))

from capture import capture
from preflight import ensure_ready
from logger import log_transition
import jack_vision_selector as vs

def tap_text(query: str, partial: bool = True) -> dict:
    before = ensure_ready()
    ok, msg = vs.tap_text(query, partial=partial)
    time.sleep(1.1)
    after = capture()
    success = ok and after.get("hash") != before.get("hash")
    entry = log_transition(
        before.get("hash", "unknown"),
        "tap_text",
        query,
        after.get("hash", "unknown"),
        success,
        {"msg": msg, "before_pkg": before.get("package"), "after_pkg": after.get("package")}
    )
    return {"ok": ok, "msg": msg, "transition": entry, "before": before, "after": after}

def list_now(max_items: int = 20):
    return capture()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python3 -m ui_agent.action list")
        print("         python3 -m ui_agent.action tap <text>")
        sys.exit(1)
    if sys.argv[1] == "list":
        st = list_now()
        print(f"Hash: {st.get('hash')}  {st.get('package')}/{st.get('activity')}")
        for i, e in enumerate(st.get("elements", [])[:15], 1):
            print(f"  {i:2d}. {e['label'][:50]}")
    else:
        q = " ".join(sys.argv[2:] if sys.argv[1] == "tap" else sys.argv[1:])
        res = tap_text(q)
        print(("OK: " if res["ok"] else "FEHLER: ") + res["msg"])
        t = res["transition"]
        print(f"Transition: {t['before'][:8]} → {t['after'][:8]} success={t['success']}")
