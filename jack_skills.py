#!/usr/bin/env python3
"""JACK Skill-Bibliothek: erfolgreiche Code-Bausteine speichern + kostenlos wiederverwenden."""
import os, json, subprocess, shutil, re
DIR=os.path.expanduser("~/jack_skills")
IDX=os.path.join(DIR,"index.json")
WERK=os.path.expanduser("~/jack_werkstatt")

def _index():
    try: return json.load(open(IDX))
    except Exception: return {}

def _safe(name):
    return re.sub(r'[^A-Za-z0-9_-]','_',name.strip()) or "skill"

def save_skill(name, quell_datei, beschreibung=""):
    os.makedirs(DIR,exist_ok=True)
    n=_safe(name)
    src=os.path.join(WERK, quell_datei) if quell_datei else ""
    if not src or not os.path.exists(src):
        return False, "Keine Quelldatei. Erst /code <aufgabe>, dann /skill save <name>."
    shutil.copy2(src, os.path.join(DIR, n+".py"))
    idx=_index(); idx[n]=beschreibung or "gespeichert"
    json.dump(idx, open(IDX,"w"), ensure_ascii=False, indent=2)
    import jack_log; jack_log.log_decision("SKILL-GESPEICHERT", n)
    return True, f"Skill '{n}' gespeichert. Aufruf jederzeit: /skill {n} (kostet KEINE API)"

def list_skills():
    idx=_index()
    if not idx: return "Noch keine Skills. Bau einen: /code ... dann /skill save <name>"
    return "Skills (kostenlos aufrufbar via /skill <name>):\n"+"\n".join(f"- {k}: {v}" for k,v in idx.items())

def run_skill(name, timeout=10):
    import jack_coder
    n=_safe(name); path=os.path.join(DIR, n+".py")
    if not os.path.exists(path):
        return False, f"Skill '{n}' gibt es nicht. /skills zeigt alle."
    risk=assess_skill_risk(open(path).read())
    if risk: return False, f"BLOCKIERT - gefaehrliches Muster: {risk!r}"
    try:
        p=subprocess.run(["python3",path],capture_output=True,text=True,timeout=timeout,cwd=DIR)
        out=(p.stdout+p.stderr).strip()
        import jack_log; jack_log.log_decision("SKILL-AUSGEFUEHRT", n)
        return True, out[:1500] if out else "(kein Output)"
    except subprocess.TimeoutExpired:
        return False, f"Abgebrochen (>{timeout}s)"
    except Exception as e:
        return False, str(e)

# === SKILL-GATE (Weg 1): eigenes engeres Gate. subprocess erlaubt, aber nur Whitelist-Befehle ===
SKILL_KILL = [
 "rm -rf","rmtree","os.remove","os.unlink","os.rmdir","shutil.rmtree","shutil.move",
 "drop table","delete from",":(){","mkfs","dd if=","> /dev","chmod -r","chown -r",
 "eval(","exec(","__import__","compile(","os.environ","getenv","jack_secrets",
 "api_key",".env","id_jack","authorized_keys",".ssh/","socket","urllib","requests.",
 "http.client","ftplib","paramiko","curl","wget"," nc ","netcat","scp ","telnet","ssh ",
]
SKILL_ALLOW = {
 "sv","free","df","ls","cat","head","tail","grep","wc","echo","date","uptime","pwd",
 "ollama","git","sqlite3","termux-battery-status","termux-wifi-connectioninfo",
 "termux-wifi-scaninfo","termux-telephony-signalstrength","termux-torch","termux-volume",
 "termux-notification","termux-tts-speak","termux-clipboard-get","termux-vibrate",
 "termux-toast","termux-location","termux-sensor","termux-brightness",
}
_SP = re.compile(r"(subprocess\.\w+|os\.system|os\.popen)\s*\(")
_CS = re.compile(r"""(?:subprocess\.\w+|os\.system|os\.popen)\s*\(\s*\[?\s*["']([^"']+)["']""")

def assess_skill_risk(code):
    low = code.lower()
    for p in SKILL_KILL:
        if p in low: return "KILLER: " + p.strip()
    calls = _SP.findall(code)
    if calls:
        cmds = _CS.findall(code)
        if len(cmds) < len(calls):
            return "Shell-Aufruf ohne direktes Kommando (fail-closed)"
        for c in cmds:
            w = c.strip().split()
            first = w[0] if w else ""
            if first not in SKILL_ALLOW:
                return "Befehl nicht auf Whitelist: " + first
    return None
