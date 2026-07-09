#!/usr/bin/env python3
import sys, json, sqlite3, datetime
sys.path.append('/data/data/com.termux/files/home/jack')
import jack_gemini_bridge

DB="/data/data/com.termux/files/home/jack/jack_memory.db"
IDENTITY="/data/data/com.termux/files/home/jack/jack_identity.json"

def learn_from_recent(n=20):
    con=sqlite3.connect(DB)
    rows=con.execute("SELECT cmd,result FROM memory ORDER BY timestamp DESC LIMIT ?",(n,)).fetchall()
    con.close()
    convo="\n".join([f"Dima: {c} | JACK: {r[:200]}" for c,r in rows])
    idn=json.load(open(IDENTITY))
    existing=idn.get("learned_facts",[])
    prompt=("Du pflegst das Faktengedaechtnis ueber Dima (Mensch, Nachtschicht-Fernfahrer) "
        "und sein JACK-Projekt (autonomes lokales AI-OS). Unten BEKANNTE FAKTEN und neue "
        "GESPRAECHE. Gib eine SAUBERE Gesamtliste zurueck: bekannte + neue echte Fakten, "
        "aehnliche ZUSAMMENGEFASST, KEINE Doppelungen, kein Smalltalk/Mathe-Test/Rauschen. "
        "Antworte NUR mit JSON-Liste kurzer Fakt-Strings, max 20, nichts anderes.\n\n"
        f"BEKANNTE FAKTEN:\n{json.dumps(existing,ensure_ascii=False)}\n\n"
        f"NEUE GESPRAECHE:\n{convo}")
    ans=jack_gemini_bridge.ask_gemini(prompt).strip()
    if ans.startswith("```"): ans="\n".join(ans.split("\n")[1:])
    if ans.endswith("```"): ans="\n".join(ans.split("\n")[:-1])
    try:
        facts=json.loads(ans)
        if not isinstance(facts,list) or not facts: facts=existing
    except Exception:
        facts=existing
    facts=[f for f in facts if isinstance(f,str)][:20]
    idn["learned_facts"]=facts
    idn["last_learned"]=datetime.datetime.now().isoformat()
    json.dump(idn,open(IDENTITY,'w'),indent=2,ensure_ascii=False)
    return facts

if __name__=="__main__":
    new=learn_from_recent()
    print("Fakten jetzt:",json.dumps(new,ensure_ascii=False,indent=2))
