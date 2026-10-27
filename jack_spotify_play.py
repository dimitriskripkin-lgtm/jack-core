#!/usr/bin/env python3
"""JACK_TUNE_SPOTIFYPLAY (26.10.2026, Kap 306): Song suchen, in Spotify oeffnen, Play-Taste per Shizuku/rish."""
import subprocess, sys, time
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
import jack_spotify as sp

def spiele(suche):
    r = sp._http("GET", "/search", params={"q": suche, "type": "track", "limit": 1})
    arr = (r.get("tracks") or {}).get("items") or []
    if not arr:
        return {"ok": False, "fehler": "nichts gefunden", "suche": suche}
    t = arr[0]
    subprocess.run(["termux-open-url", t["uri"] + ":play"], timeout=10)
    time.sleep(3)
    subprocess.run(["rish", "-c", "input keyevent 126"], timeout=15)
    return {"ok": True, "titel": t["name"], "kuenstler": ", ".join(a["name"] for a in t["artists"]), "uri": t["uri"]}

if __name__ == "__main__":
    print(spiele(" ".join(sys.argv[1:])))
