# JACK_TUNE_KORREKTUR: Fakten korrigieren ohne Verlust. Alter Wert wandert in Tabelle korrekturen, der Knoten bekommt den neuen Wert.
import os, re, time, sqlite3
_DB = os.path.expanduser("~/jack/jack_graph.db")
_SPLIT = re.compile(r"\s*(=>|->|→)\s*")
_GEHEIM = ("token", "passwort", "password", "secret", "bearer", "api_key", "apikey")

def _con():
    c = sqlite3.connect(_DB, timeout=10)
    c.execute("create table if not exists korrekturen(id integer primary key, node text, alt text, neu text, ts real, von text)")
    return c

def korrigiere(alt, neu, von="telegram"):
    alt = (alt or "").strip(); neu = (neu or "").strip()
    if len(alt) < 3 or not neu:
        return "Nutzung: /korrigiere <altes Stichwort> => <neuer Wert>\nBeispiel: /korrigiere Starlight => Starfield auf PS5"
    low = neu.lower()
    if any(g in low for g in _GEHEIM) or re.search(r"[A-Za-z0-9+/=_-]{30,}", neu):
        return "Nicht korrigiert (sieht nach Geheimnis aus)."
    c = _con()
    try:
        pat = "%" + alt.replace("%", "").replace("_", "") + "%"
        rows = c.execute("select id, name, wert from nodes where typ='fakt' and (wert like ? or name like ?) limit 6", (pat, pat)).fetchall()
        if not rows:
            return "Kein Fakt mit '%s' gefunden." % alt[:40]
        if len(rows) > 1:
            return "Mehrere Treffer, bitte genauer:\n" + "\n".join("- %s: %s" % (r[1][:30], (r[2] or "")[:60]) for r in rows)
        nid, name, wert = rows[0]
        t = time.time()
        c.execute("insert into korrekturen(node, alt, neu, ts, von) values(?,?,?,?,?)", (nid, wert, neu[:200], t, von))
        c.execute("update nodes set wert=?, src='korrektur', ts=? where id=?", (neu[:200], t, nid))
        c.commit()
        try:
            import jack_corr as _jc
            _jc.audit("korrigiere", "jack_graph.db", nid, "jack_korrektur")
        except Exception:
            pass
        return "Korrigiert (%s): '%s' -> '%s'. Alter Wert ist in der Historie gesichert." % (name[:30], (wert or "")[:50], neu[:50])
    finally:
        c.close()

def antwort(arg):
    p = _SPLIT.split(arg or "", maxsplit=1)
    if len(p) == 3:
        return korrigiere(p[0], p[2])
    return korrigiere("", "")
