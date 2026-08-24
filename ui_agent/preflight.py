#!/usr/bin/env python3
"""ui_agent/preflight.py - Immer zuerst: entsperrt? wo bin ich?"""
import sys, time
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")

from capture import capture, _su

def ensure_ready(max_tries=3):
    """Entsperren falls nötig und aktuellen State zurückgeben."""
    for i in range(max_tries):
        st = capture()
        state = st.get("state", "unknown")
        pkg = st.get("package", "?")
        h = st.get("hash", "unknown")

        if state == "aod" or state == "unknown" or pkg in ("com.miui.aod", "com.android.systemui"):
            print(f"[preflight] Screen locked/AOD – unlock Versuch {i+1}")
            _su("input keyevent 224")
            time.sleep(0.3)
            _su("input keyevent 82")
            time.sleep(0.25)
            _su("input swipe 540 1600 540 900 180")
            time.sleep(0.8)
            continue

        print(f"[preflight] OK  state={state}  {pkg}  hash={h[:10]}")
        return st

    # letzter Versuch trotzdem zurückgeben
    st = capture()
    print(f"[preflight] FALLBACK  state={st.get('state')}  {st.get('package')}")
    return st

if __name__ == "__main__":
    st = ensure_ready()
    print("Elemente:", len(st.get("elements", [])))
    for e in st.get("elements", [])[:6]:
        print(" -", e["label"][:40])
