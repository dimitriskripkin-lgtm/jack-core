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
    risk=jack_coder.assess_risk(open(path).read())
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
