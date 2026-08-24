#!/usr/bin/env python3
"""ui_agent/loop.py - Minimaler autonomer UI-Loop mit Logging."""
import sys, os, time, random
sys.path.insert(0, os.path.expanduser("\~/jack"))
sys.path.insert(0, os.path.expanduser("\~/jack/ui_agent"))

from capture import capture
from action import tap_text
from logger import log_transition

def run_loop(steps=5, prefer=None):
    print(f"=== UI-Loop start ({steps} Schritte) ===")
    for i in range(1, steps+1):
        st = capture()
        print(f"\n[{i}] {st['package']}/{st['activity']}  hash={st['hash'][:8]}")
        els = [e for e in st.get("elements", []) if e.get("clickable") or len(e["label"]) > 3]
        if not els:
            print("  keine Elemente – warte")
            time.sleep(1.5)
            continue

        # einfache Wahl: prefer-Label oder erstes brauchbares
        target = None
        if prefer:
            for e in els:
                if prefer.lower() in e["label"].lower():
                    target = e["label"]
                    break
        if not target:
            # nimm etwas anderes als die letzten bekannten
            candidates = [e["label"] for e in els if "Mods" not in e["label"] and "Player" not in e["label"]]
            target = random.choice(candidates) if candidates else els[0]["label"]

        print(f"  → tippe: {target}")
        res = tap_text(target)
        print(f"  {res['msg']}")
        t = res["transition"]
        print(f"  Transition: {t['before'][:8]} → {t['after'][:8]}  success={t['success']}")
        time.sleep(1.8)
    print("\n=== Loop Ende ===")

if __name__ == "__main__":
    steps = 5
    prefer = None
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        steps = int(sys.argv[1])
    if len(sys.argv) > 2:
        prefer = " ".join(sys.argv[2:])
    run_loop(steps, prefer)
