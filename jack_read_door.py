#!/usr/bin/env python3
"""JACK_TUNE_READDOOR Graph, dann Memory, dann Identity. Eine Suche."""
import json, os, sqlite3
J = "/data/data/com.termux/files/home/jack"

def _graph(q):
    db = J + "/jack_graph.db"
    if not os.path.isfile(db):
        return []
    con = sqlite3.connect(db)
    try:
        cols = [r[1] for r in con.execute("PRAGMA table_info(nodes)")]
        bis = ", gueltig_bis" if "gueltig_bis" in cols else ""
        rows = con.execute(
            "SELECT name, wert%s FROM nodes WHERE name LIKE ? OR wert LIKE ? ORDER BY ts DESC LIMIT 5" % bis,
            ("%"+q+"%", "%"+q+"%"),
        ).fetchall()
    except Exception:
        rows = []
    con.close()
    out = []
    for r in rows:
        item = {"quelle": "graph", "name": r[0], "wert": r[1]}
        if len(r) > 2:
            item["gueltig_bis"] = r[2]
        out.append(item)
    return out

def _memory(q):
    db = J + "/jack_memory.db"
    if not os.path.isfile(db):
        return []
    con = sqlite3.connect(db)
    try:
        rows = con.execute(
            "SELECT cmd, result FROM memory WHERE cmd LIKE ? OR result LIKE ? ORDER BY id DESC LIMIT 3",
            ("%"+q+"%", "%"+q+"%"),
        ).fetchall()
    except Exception:
        rows = []
    con.close()
    return [{"quelle": "memory", "name": (r[0] or "")[:80], "wert": (r[1] or "")[:160]} for r in rows]

def _identity(q):
    p = J + "/jack_identity.json"
    if not os.path.isfile(p):
        return []
    try:
        data = json.loads(open(p, encoding="utf-8").read())
    except Exception:
        return []
    hits = []
    if isinstance(data, dict):
        for k, v in data.items():
            if q.lower() in str(k).lower() or q.lower() in str(v).lower():
                hits.append({"quelle": "identity", "name": str(k)[:80], "wert": str(v)[:160]})
            if len(hits) >= 3:
                break
    return hits

def lesen(q):
    q = (q or "").strip()
    if not q:
        return []
    for fn in (_graph, _memory, _identity):
        hits = fn(q)
        if hits:
            return hits
    return []
