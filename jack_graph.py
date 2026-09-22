#!/usr/bin/env python3
MODULE_VERSION = 2
import os,re,sqlite3,time,sys
from jack_log import get_logger
log = get_logger("jack_graph")
DB=os.path.join(os.path.expanduser("~"),"jack","jack_graph.db")
TYPS=("person","geraet","fakt","skill","chat","persona","ziel")
RELS=("hat","widerspricht","betrifft","folgt_aus")
def norm(s):
    s=(s or "").lower()
    for a,b in (("ae","ae"),("oe","oe"),("ue","ue"),("ss","ss")): pass
    return re.sub(r"[^a-z0-9_]+","_",s)[:48].strip("_") or "x"
def nid(typ,name):
    return typ+":"+norm(name)
def con():
    c=sqlite3.connect(DB,timeout=5)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY,typ TEXT,name TEXT,wert TEXT,src TEXT,ts REAL)")
    c.execute("CREATE TABLE IF NOT EXISTS edges(id INTEGER PRIMARY KEY,a TEXT,rel TEXT,b TEXT,src TEXT,ts REAL)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS euniq ON edges(a,rel,b)")
    return c
def put_node(typ,name,wert="",src="seed"):
    import jack_corr as _jc; _jc.audit("put_node","jack_graph.db",str(typ)+":"+str(name),"jack_graph")
    if typ not in TYPS: return None
    if _is_suspicious(name) or _is_suspicious(wert): return None  # JACK_TUNE_BUGD
    i=nid(typ,name); t=time.time()
    c=con()
    c.execute("INSERT INTO nodes(id,typ,name,wert,src,ts) VALUES(?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET wert=excluded.wert,src=excluded.src,ts=excluded.ts",
              (i,typ,name,str(wert)[:200],src,t))
    c.commit(); c.close(); return i

SUSPICIOUS = [
    "sektor", "sector", "zone-", "node-", "id-0x", "ref-",
    "koordinat", "cluster", "grid", "segment-", "block-7",
    "halluzin", "fehler-", "error-node", "unknown-"
]

def _is_suspicious(text):
    low = (text or "").lower()
    return any(s in low for s in SUSPICIOUS)

def put_edge(a,rel,b,src="seed"):
    import jack_corr as _jc; _jc.audit("put_edge","jack_graph.db",str(a)+"->"+str(b),"jack_graph")
    if rel not in RELS: return
    c=con(); t=time.time()
    c.execute("INSERT OR IGNORE INTO edges(a,rel,b,src,ts) VALUES(?,?,?,?,?)",(a,rel,b,src,t))
    c.commit(); c.close()
def seed():
    d=put_node("person","Dima","owner", "seed")
    j=put_node("geraet","JACK","lebens-os honor+xiaomi","seed")
    h=put_node("geraet","Honor","gehirn","seed")
    x=put_node("geraet","Xiaomi","muskel","seed")
    f=put_node("fakt","Hund","nein","seed")
    put_node("fakt","Nachtschicht-Pflicht","nein nicht annehmen","seed")
    put_edge(d,"hat",j); put_edge(d,"hat",h); put_edge(d,"hat",x); put_edge(d,"hat",f)
    put_edge(j,"betrifft",h); put_edge(j,"betrifft",x)
    return True
def recall(q,limit=8):
    c=con()
    toks=[w for w in re.split(r"[^a-zA-Z0-9äöüÄÖÜß]+",(q or "").lower()) if len(w)>2][:6]
    if not toks: toks=["dima","jack"]
    ids=set()
    for w in toks+["dima","jack"]:
        for row in c.execute("SELECT id FROM nodes WHERE name LIKE ? OR wert LIKE ? OR id LIKE ? LIMIT 6",("%"+w+"%","%"+w+"%","%"+w+"%")):
            ids.add(row[0])
    extra=set()
    for i in list(ids):
        for row in c.execute("SELECT a,rel,b FROM edges WHERE a=? OR b=? LIMIT 12",(i,i)):
            extra.add(row[0]); extra.add(row[2])
    ids |= extra
    lines=[]
    for i in list(ids)[:20]:
        n=c.execute("SELECT typ,name,wert FROM nodes WHERE id=?",(i,)).fetchone()
        if n: lines.append(n[0]+" "+n[1]+("="+n[2] if n[2] else ""))
    for row in c.execute("SELECT a,rel,b FROM edges WHERE a IN ({}) OR b IN ({})".format(",".join("?"*len(ids)),",".join("?"*len(ids))), tuple(ids)+tuple(ids)):
        lines.append(row[0]+" -"+row[1]+"> "+row[2])
        if len(lines)>=limit: break
    c.close()
    out=[]; seen=set()
    for l in lines:
        if l not in seen:
            seen.add(l); out.append(l)
        if len(out)>=limit: break
    return "\n".join(out)
def prompt_block(q):
    r=recall(q,8)
    return "GRAPH (nur Fakten, nicht vorlesen):\n"+r if r else ""
if __name__=="__main__":
    seed()
    q=" ".join(sys.argv[1:]) or "Hund Dima"
    print(prompt_block(q))

def fakt_aus_satz(satz, src="telegram"):  # JACK_TUNE_FAKT1
    """Zerlegt einen Satz per LLM in Fakt-Name/Wert, haengt ihn an person:dima."""
    try:
        import jack_gemini_bridge as _jgb, json as _j
        p = ('Zerlege den Satz in einen kurzen Fakt-Namen (1-2 Woerter) und einen Wert. '
             'Antworte NUR mit JSON. Kein Fakt -> {}. '
             '"Ich habe eine Katze namens Bibi" -> {"name":"katze","wert":"Bibi"}. '
             '"Ich spiele gerne Playstation 5" -> {"name":"hobby","wert":"Playstation 5"}. '
             'Satz: ') + str(satz)[:200]
        r = _jgb.ask_gemini(p)
        if not r or r.lstrip().startswith(("[Analyse]", "[Talk]", "[Ollama]")):
            return None
        r = r.strip().strip("`")
        d = _j.loads(r[r.find("{"):r.rfind("}") + 1])
        n = str(d.get("name", "")).strip()
        w = str(d.get("wert", "")).strip()
        if not n or not w:
            return None
        i = put_node("fakt", n, w, src=src)
        if not i:
            return None
        put_edge("person:dima", "hat", i, src=src)
        return i
    except Exception:
        return None

def embed_lokal(text):  # JACK_TUNE_EMBLOKAL
    """Embedding ueber das lokale Ollama auf dem Honor, kein Xiaomi-Umweg."""
    try:
        import urllib.request, json as _j
        data = _j.dumps({'model': 'nomic-embed-text', 'prompt': text}).encode('utf-8')
        req = urllib.request.Request('http://localhost:11434/api/embeddings', data=data,
                                      headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as res:
            return _j.loads(res.read().decode('utf-8'))['embedding']
    except Exception:
        return None

# aehnlicher_knoten entfernt 22.09.2026 — fakt_vec-Tabelle existiert nicht (JACK_TUNE_EMBLOKAL)
