#!/usr/bin/env python3
import sys, json, sqlite3, datetime
sys.path.append('/data/data/com.termux/files/home/jack')
import jack_gemini_bridge

DB="/data/data/com.termux/files/home/jack/jack_memory.db"
IDENTITY="/data/data/com.termux/files/home/jack/jack_identity.json"

def learn_from_recent(n=30):
    con=sqlite3.connect(DB)
    rows=con.execute("SELECT cmd,result FROM memory ORDER BY timestamp DESC LIMIT ?",(n,)).fetchall()
    con.close()
    convo="\n".join([f"Dima: {c} | JACK: {r[:200]}" for c,r in rows])
    idn=json.load(open(IDENTITY))
    existing=idn.get("learned_facts",[])
    korrekturen=idn.get("korrekturen",[])
    prompt=("Du pflegst das Faktengedaechtnis ueber Dima (Mensch) und sein JACK-Projekt. "
        "Unten die BEKANNTEN FAKTEN und die NEUEN GESPRAECHE.\n"
        "WICHTIGE REGELN:\n"
        "- Wenn Dima in den Gespraechen etwas KORRIGIERT oder DEMENTIERT (z.B. 'ich habe keinen Hund', "
        "'das war nur ein Test', 'ich bin kein X sondern Y'): entferne den alten falschen Fakt KOMPLETT "
        "und ersetze ihn durch die Korrektur. Die AUSSAGE VON DIMA GEWINNT immer.\n"
        "- Widerspruechliche Fakten aufloesen, nie beide behalten.\n"
        "- Aehnliche zusammenfassen, keine Doppelungen, kein Smalltalk/Rauschen.\n"
        "- Nur was Dima ueber sich oder das Projekt gesagt hat, keine erfundenen Details.\n"
        "- VERBOTEN als Fakt: Commit-Hashes, Anzahl Erinnerungen, Fehlerzahlen, Handshake-Versionen, "
        "Dienst-Status, Uhrzeiten, Modell-Namen, alles Technische das sich AENDERT. "
        "Solche fluechtigen Systemdaten NIEMALS als Fakt speichern - die werden live abgefragt.\n"
        "Antworte NUR mit JSON-Liste kurzer Fakt-Strings, max 20, nichts anderes.\n\n"
        f"ABSOLUTE KORREKTUREN (entferne jeden widersprechenden Fakt, fuege ihn NIE wieder hinzu):\n{json.dumps(korrekturen,ensure_ascii=False)}\n\n"
        f"BEKANNTE FAKTEN:\n{json.dumps(existing,ensure_ascii=False)}\n\n"
        f"NEUE GESPRAECHE (Dimas Korrekturen haben Vorrang):\n{convo}")
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

    # Neue Fakten in kortex_memory.db schreiben
    try:
        from kortex_memory import add_memory
        alte = set(existing)
        for fakt in facts:
            if fakt not in alte:
                add_memory(fakt, category="fakt", source="jack_learn", tags="auto gelernt")
    except Exception as _e:
        import jack_log; jack_log.log_decision("LEARN-MEMORY-FEHLER", str(_e)[:120])

    return facts

if __name__=="__main__":
    new=learn_from_recent()
    print("Fakten jetzt:",json.dumps(new,ensure_ascii=False,indent=2))
