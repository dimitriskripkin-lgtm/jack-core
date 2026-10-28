#!/usr/bin/env python3
"""JACK_TUNE_ERRDOOR Eine Lesetuer. Dateien bleiben."""
import os, sqlite3
J = "/data/data/com.termux/files/home/jack"
DBS = ["jack_outcomes.db", "jack_errors.db", "errors.db"]

def letzte(n=5):
    out = []
    for name in DBS:
        p = J + "/" + name
        if not os.path.isfile(p):
            continue
        con = sqlite3.connect(p)
        try:
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
            for t in tables[:3]:
                try:
                    rows = con.execute("SELECT * FROM %s ORDER BY rowid DESC LIMIT ?" % t, (n,)).fetchall()
                except Exception:
                    continue
                for r in rows:
                    out.append({"datei": name, "tabelle": t, "zeile": str(r)[:180]})
        except Exception as e:
            out.append({"datei": name, "fehler": str(e)[:80]})
        con.close()
    return out[:n]
