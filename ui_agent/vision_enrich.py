#!/usr/bin/env python3
"""ui_agent/vision_enrich.py - Einmal Vision (jack_vision), dann Memory."""
import sys, os, time
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")

from capture import capture
from preflight import ensure_ready
from logger import log_vision
import sqlite3

DB = "/data/data/com.termux/files/home/jack/jack_memory.db"


def ensure_unlocked():
    from capture import _su
    import time
    _su("input keyevent 224")
    time.sleep(0.25)
    _su("input keyevent 82")
    time.sleep(0.2)
    _su("input swipe 540 1600 540 900 180")
    time.sleep(0.6)

def already_known(screen_hash):
    con = sqlite3.connect(DB)
    row = con.execute(
        "SELECT analysis FROM vision_log WHERE analysis LIKE ? ORDER BY id DESC LIMIT 1",
        (f"%hash:{screen_hash[:12]}%",)
    ).fetchone()
    con.close()
    return row[0] if row else None

def enrich(force=False, frage="Was siehst du auf dem Screen? Kurze Beschreibung."):
    st = ensure_ready()
    h = st.get("hash", "unknown")
    if not force:
        known = already_known(h)
        if known:
            print("bereits bekannt:", known[:120])
            return known
    # echte Vision über bestehende Funktion
    try:
        import jack_vision
        result = jack_vision.analyze_screen(frage)
        desc = f"hash:{h[:12]} pkg:{st.get('package')} | vision: {str(result)[:400]}"
    except Exception as e:
        labels = " | ".join(e["label"][:30] for e in st.get("elements", [])[:8])
        desc = f"hash:{h[:12]} pkg:{st.get('package')} | fallback: {labels} | err:{e}"
    log_vision(desc, source="enrich")
    print("neu gelernt:", desc[:140])
    return desc

if __name__ == "__main__":
    force = "--force" in sys.argv
    frage = " ".join(a for a in sys.argv[1:] if a != "--force") or "Was siehst du auf dem Screen? Kurze Beschreibung."
    enrich(force=force, frage=frage)
