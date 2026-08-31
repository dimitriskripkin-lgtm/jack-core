#!/usr/bin/env python3
import os,re,sqlite3,time,sys
DB="/data/data/com.termux/files/home/jack/jack_graph.db"
TYPS=("person","geraet","fakt","skill","chat")
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
    if typ not in TYPS: return None
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
