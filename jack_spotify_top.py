#!/usr/bin/env python3
"""JACK_TUNE_SPOTIFYTOP (26.10.2026, Kap 306): Herz-Songs, Topliste, Tagessicherung,
Playlist "JACK – Lieblinge nach Hoerdauer". Nutzt jack_spotify._http (Token, 401/429)."""
import collections, datetime, json, os, pathlib, sys
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
import jack_spotify as sp

ROOT = pathlib.Path("/data/data/com.termux/files/home/jack")
SNAP = ROOT / "logs" / "spotify_snapshot"
NAME = "JACK – Lieblinge nach Hoerdauer"

def _alle(path, params=None, maxn=5000):
    off, out = 0, []
    while len(out) < maxn:
        p = dict(params or {}); p.update({"limit": 50, "offset": off})
        page = sp._http("GET", path, params=p)
        arr = page.get("items") or []
        out += arr; off += len(arr)
        if not arr or not page.get("next"):
            break
    return out

def herz():
    rows = _alle("/me/tracks")
    res = []
    for r in rows:
        t = r.get("track") or r.get("item") or {}
        if t.get("uri", "").startswith("spotify:track:"):
            res.append({"uri": t["uri"], "name": t.get("name", ""),
                        "kuenstler": ", ".join(a.get("name", "") for a in t.get("artists", [])),
                        "added_at": r.get("added_at", "")})
    return res

def top(zeitraum):
    rows = _alle("/me/top/tracks", {"time_range": zeitraum}, maxn=100)
    return [t.get("uri") for t in rows if t.get("uri")]

def verlauf_zaehler():
    c = collections.Counter()
    p = ROOT / "logs" / "spotify_verlauf.jsonl"
    if p.exists():
        for l in p.read_text(encoding="utf-8").splitlines():
            try: c[json.loads(l)["uri"]] += 1
            except (ValueError, KeyError): pass
    return c

def tagessicherung():
    SNAP.mkdir(parents=True, exist_ok=True); os.chmod(SNAP, 0o700)
    pl = [{"id": p.get("id"), "name": p.get("name"), "owner": (p.get("owner") or {}).get("display_name"),
           "total": (p.get("items") or p.get("tracks") or {}).get("total"), "snapshot_id": p.get("snapshot_id")}
          for p in sp.playlists()]
    h = herz()
    ziel = SNAP / (datetime.date.today().isoformat() + ".json")
    sp._save(ziel, {"zeit": datetime.datetime.now().isoformat(timespec="seconds"), "playlisten": pl, "herz": h})
    return {"playlisten": len(pl), "herz": len(h), "datei": str(ziel)}

def rangliste():
    """Herz-Songs: zuerst nach Spotify-Topliste (lang, mittel, kurz), dann eigener Verlauf, Rest zum Schluss."""
    h = herz()
    ranks = {}
    for gewicht, zr in ((1.0, "long_term"), (1.5, "medium_term"), (2.0, "short_term")):
        for i, u in enumerate(top(zr)):
            ranks[u] = min(ranks.get(u, 1e9), (i + 1) * gewicht)
    zahl = verlauf_zaehler()
    def schluessel(s):
        r = ranks.get(s["uri"])
        return (0, r) if r is not None else (1, -zahl.get(s["uri"], 0), s["added_at"] and -int(s["added_at"][:10].replace("-", "")) or 0)
    return sorted(h, key=schluessel), len([s for s in h if s["uri"] in ranks])

def lieblinge_playlist():
    liste, mit_rang = rangliste()
    uris = [s["uri"] for s in liste]
    if not uris:
        raise RuntimeError("Keine Herz-Songs gefunden")
    vorhanden = [p for p in sp.playlists() if p.get("name") == NAME]
    if vorhanden:
        pid = vorhanden[0]["id"]
    else:
        pid = sp._http("POST", "/me/playlists", {"name": NAME, "public": False,
            "description": "Von JACK: deine Herz-Songs, oben am meisten gehoert, unten am wenigsten."})["id"]
    sp._http("PUT", "/playlists/" + pid + "/items", {"uris": uris[:100]})
    for i in range(100, len(uris), 100):
        sp._http("POST", "/playlists/" + pid + "/items", {"uris": uris[i:i + 100]})
    return {"playlist_id": pid, "titel": len(uris), "mit_rang": mit_rang, "neu": not vorhanden,
            "top5": [s["name"] + " - " + s["kuenstler"] for s in liste[:5]]}

if __name__ == "__main__":
    print(json.dumps(tagessicherung(), ensure_ascii=False))
