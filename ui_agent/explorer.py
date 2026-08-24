#!/usr/bin/env python3
"""ui_agent/explorer.py - Guckt, setzt Ziel, probiert, lernt."""
import sys, time, random
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")

from preflight import ensure_ready
from capture import capture
from logger import log_transition
from action import tap_text
from skills import save_skill
from graph import successors

# echte App-Namen bevorzugen
PREFERRED = ["chrome", "telegram", "einstellung", "settings", "kalender", "kamera",
             "galerie", "telefon", "nachricht", "play store", "clock", "uhr", "wetter",
             "chatgpt", "claude", "shizuku", "termux", "files", "dateien"]

def pick_target(st):
    els = [e for e in st.get("elements", []) if e.get("clickable") and len(e["label"]) > 2]
    if not els:
        return None
    bad = ["werbung", "zustimmen", "cookie", "login", "anmelden", "usw.", "ordner"]
    good = [e for e in els if not any(b in e["label"].lower() for b in bad)]
    if not good:
        good = els
    # bevorzugte Apps nach vorne
    preferred = [e for e in good if any(p in e["label"].lower() for p in PREFERRED)]
    pool = preferred if preferred else good
    return random.choice(pool[:6])["label"]

def explore_step():
    st = ensure_ready()
    print(f"\n[Explorer] {st.get('package')} hash={st.get('hash','')[:10]} els={len(st.get('elements',[]))}")
    known = successors(st["hash"])
    if known:
        print(f"  Graph kennt {len(known)} Nachfolger")

    target = pick_target(st)
    if not target:
        print("  nichts Klickbares")
        return None

    print(f"  → probiere: {target}")
    before = st
    try:
        res = tap_text(target)
        print("   ", res.get("msg"))
        time.sleep(2.2)  # länger warten
    except Exception as e:
        print("    Fehler:", e)
        return None

    after = capture()
    success = after.get("hash") != before.get("hash")
    log_transition(before["hash"], "explore", target, after["hash"], success,
                   {"pkg": after.get("package"), "from": before.get("package")})
    print(f"  {before['hash'][:8]} → {after['hash'][:8]}  pkg={after.get('package')}  success={success}")
    return {
        "before": before["hash"][:16], "action": "explore", "target": target,
        "after": after["hash"][:16], "pkg": after.get("package"), "success": success
    }

def run(steps=4):
    print(f"=== SELF-EXPLORER ({steps} Schritte) ===")
    trail = []
    for i in range(steps):
        step = explore_step()
        if step and step["success"]:
            trail.append(step)
        time.sleep(0.6)
        if len(trail) >= 2 and trail[-1]["after"] == trail[-2]["after"]:
            print("  Guard: kein Fortschritt")
            break
    if len(trail) >= 2:
        name = f"explore_{int(time.time()) % 10000}"
        save_skill(name, trail, trail[0]["before"], trail[-1]["after"])
        print(f"\nNeuer Skill: {name} ({len(trail)} Schritte)")
    else:
        print("\nKeine stabile Sequenz")
    print("=== Ende ===")

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4
    run(n)
