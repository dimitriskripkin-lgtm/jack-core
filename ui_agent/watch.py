#!/usr/bin/env python3
"""ui_agent/watch.py - Live zuschauen und lernen."""
import sys, os, time
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")

from capture import capture
from logger import log_transition, log_vision

def watch(interval=1.6):
    print("=== LIVE WATCH gestartet ===")
    print("Bedien das Handy normal. Strg+C zum Stoppen.\n")
    last_hash = None
    count = 0
    fails = 0
    try:
        while True:
            st = capture()
            h = st.get("hash", "unknown")
            pkg = st.get("package", "?")
            act = st.get("activity", "?")
            els = st.get("elements", [])

            if h == "unknown" or not st.get("ok"):
                fails += 1
                if fails < 3:
                    time.sleep(0.8)
                    continue
                fails = 0
                time.sleep(interval)
                continue

            fails = 0
            if h != last_hash:
                count += 1
                print(f"[{count}] {st.get("state","?")} {pkg}/{act}  hash={h[:10]}  els={len(els)}")
                for e in els[:5]:
                    print(f"      - {e['label'][:48]}")
                print()
                if last_hash and last_hash != "unknown":
                    log_transition(last_hash, "user_action", "manual", h, True,
                                   {"pkg": pkg, "act": act, "els": len(els)})
                labels = " | ".join(e["label"][:28] for e in els[:6])
                log_vision(f"Watch: {pkg}/{act} | {labels}", source="watch")
                last_hash = h
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n=== WATCH Ende – {count} Wechsel gelernt ===")

if __name__ == "__main__":
    watch()
