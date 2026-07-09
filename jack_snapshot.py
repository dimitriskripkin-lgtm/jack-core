#!/usr/bin/env python3
import os, json, subprocess, sqlite3, datetime
H="/data/data/com.termux/files/home/jack"
def sh(c):
    try: return subprocess.run(c,shell=True,capture_output=True,text=True,timeout=15).stdout.strip()
    except Exception: return ""
try: idn=json.load(open(f"{H}/jack_identity.json"))
except Exception: idn={}
mods=sorted([f for f in os.listdir(H) if f.endswith(".py")])
gitlog=sh(f"cd {H} && git log --oneline -15")
try:
    c=sqlite3.connect(f"{H}/jack_errors.db"); oe=c.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]; c.close()
except Exception: oe="?"
try:
    c=sqlite3.connect(f"{H}/jack_memory.db"); mm=c.execute("SELECT COUNT(*) FROM memory").fetchone()[0]; c.close()
except Exception: mm="?"
svc=sh("sv status jack_cortex jack_telegram jack_autolearn ollama")
facts="\n".join("- "+f for f in idn.get("learned_facts",[]))
modlist="\n".join("- "+m for m in mods)
md=f"""# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: {datetime.datetime.now().isoformat()}

## Owner / Kern
- Owner: {idn.get('owner','?')}
- Hardware: {idn.get('hardware','?')}
- Vision: {idn.get('vision','?')}
- WICHTIG: {idn.get('wichtig','')}

## Was JACK ueber Dima gelernt hat
{facts}

## Aktive Module ({len(mods)})
{modlist}

## System-Status
- Offene Fehler: {oe}
- Erinnerungen: {mm}
- Dienste:
{svc}

## Letzte Aenderungen
{gitlog}

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.234.166.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
"""
open(f"{H}/jack_context.md","w").write(md)
print("jack_context.md geschrieben ("+str(len(md))+" Zeichen)")
