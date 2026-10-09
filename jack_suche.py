# JACK_TUNE_SUCHE: Volltextsuche (Zyklus-Test) (SQLite FTS5) ueber Handbuch, Arbeitsplatz, Entscheidungen, Missions-Logs. Nur lesen, kein LLM.
import os, re, json, sqlite3, time, glob, threading
H = os.path.expanduser("~/jack")
DB = os.path.join(H, "jack_suche.db")
_SEC = re.compile(r"(gh[opsu]_[A-Za-z0-9]{20}|AIza[A-Za-z0-9_-]{30}|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}|[A-Za-z0-9+/=_-]{40,}|bearer\s+\S{12,})", re.I)
_BAD = ("token", "secret", "passw", "config.ini", ".dima_secret")
_lock = threading.Lock()

def _con():
    c = sqlite3.connect(DB, timeout=10)
    c.execute("create virtual table if not exists docs using fts5(quelle, titel, text, tokenize='unicode61')")
    c.execute("create table if not exists seen(path text primary key, mt real)")
    return c

def _clean(t):
    return _SEC.sub("[X]", t or "")

def _chunks(t, n=900):
    out, cur = [], ""
    for p in re.split(r"\n\s*\n", t):
        if len(cur) + len(p) > n and cur:
            out.append(cur); cur = ""
        cur += p + "\n"
    if cur.strip():
        out.append(cur)
    return out

def _add_file(c, path, quelle):
    try:
        if any(b in path.lower() for b in _BAD):
            return 0
        mt = os.path.getmtime(path)
        r = c.execute("select mt from seen where path=?", (path,)).fetchone()
        if r and r[0] >= mt:
            return 0
        c.execute("delete from docs where titel=?", (path,))
        txt = open(path, encoding="utf-8", errors="replace").read()[:200000]
        for ch in _chunks(_clean(txt)):
            c.execute("insert into docs values(?,?,?)", (quelle, os.path.basename(path), ch))
        c.execute("insert or replace into seen values(?,?)", (path, mt))
        return 1
    except Exception:
        return 0

def reindex(max_logs=300):
    with _lock:
        c = _con()
        n = 0
        for pat, q in (("BETRIEBSHANDBUCH/*.md", "handbuch"), ("ARBEITSPLATZ/gemeinsam/*.md", "arbeitsplatz"),
                       ("*.md", "doku")):
            for p in sorted(glob.glob(os.path.join(H, pat))):
                n += _add_file(c, p, q)
        k = 0
        for p in sorted(glob.glob(os.path.join(H, "missions", "logs", "*.json")), reverse=True):
            if k >= max_logs:
                break
            try:
                mt = os.path.getmtime(p)
                if c.execute("select 1 from seen where path=?", (p,)).fetchone():
                    continue
                d = json.load(open(p, encoding="utf-8", errors="replace"))
                if isinstance(d, dict):
                    r = d.get("result") if isinstance(d.get("result"), dict) else d
                    t = "%s %s | %s | %s %s" % (d.get("ts", ""), d.get("act", r.get("act", "")),
                        d.get("description", d.get("desc", "")), str(r.get("note", ""))[:300], str(r.get("out", ""))[:300])
                    c.execute("insert into docs values(?,?,?)", ("mission", os.path.basename(p), _clean(t)))
                c.execute("insert or replace into seen values(?,?)", (p, mt))
                k += 1
            except Exception:
                try:
                    c.execute("insert or replace into seen values(?,?)", (p, 0))
                except Exception:
                    pass
        try:  # JACK_TUNE_SUCHEFAKT
            gc = sqlite3.connect(os.path.join(H, "jack_graph.db"), timeout=5)
            c.execute("delete from docs where quelle='fakt'")
            for nm, w in gc.execute("select name, wert from nodes where typ='fakt'"):
                c.execute("insert into docs values(?,?,?)", ("fakt", nm, _clean("%s: %s" % (nm, w))))
            gc.close()
        except Exception:
            pass
        dl = os.path.join(H, "jack_decisions.log")
        if os.path.exists(dl):
            c.execute("delete from docs where quelle='entscheidung'")
            try:
                lines = open(dl, encoding="utf-8", errors="replace").read().splitlines()[-1500:]
                for i in range(0, len(lines), 10):
                    c.execute("insert into docs values(?,?,?)", ("entscheidung", "jack_decisions.log", _clean("\n".join(lines[i:i + 10]))))
            except Exception:
                pass
        c.commit(); c.close()
        return n + k

def suche(q, n=5):
    terms = re.findall(r"\w+", q or "")[:6]
    if not terms:
        return []
    m = " ".join('"%s"*' % t for t in terms)
    c = _con()
    try:
        return c.execute("select quelle, titel, snippet(docs,2,'[',']',' ... ',18) from docs where docs match ? order by rank limit ?", (m, n)).fetchall()
    finally:
        c.close()

def antwort(q):
    if not (q or "").strip():
        return "Nutzung: /suche <Begriff>  (z.B. /suche Tunnel)"
    try:
        fresh = os.path.exists(DB) and time.time() - os.path.getmtime(DB) < 3600
    except Exception:
        fresh = False
    if not os.path.exists(DB):
        reindex(400)
    elif not fresh:
        threading.Thread(target=reindex, daemon=True).start()
    rows = suche(q)
    if not rows:
        return "Nichts gefunden zu: " + q[:60]
    return "\n\n".join("%d) [%s] %s\n%s" % (i + 1, a, b, " ".join(s.split())[:300]) for i, (a, b, s) in enumerate(rows))[:3500]
