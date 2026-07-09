#!/usr/bin/env python3
"""JACK verbessert eigenen Code: Vorschlag -> Freigabe -> Patch -> Auto-Rollback."""
import os, subprocess
JACK=os.path.expanduser("~/jack")

def _mod(name):
    name=os.path.basename(name.strip())
    if not name.endswith(".py"): name+=".py"
    return os.path.join(JACK,name), name

def propose_improvement(module):
    path,name=_mod(module)
    if not os.path.exists(path):
        return None, f"Modul nicht gefunden: {name}"
    code=open(path).read()
    import jack_gemini_bridge as gb
    prompt=(
        "Du bist JACKs Code-Reviewer. Schlage GENAU EINE kleine, sichere Verbesserung "
        "vor (Robustheit/Klarheit/Fehlerbehandlung). KEINE grosse Umschreibung. "
        "Antworte NUR mit einem Block:\n"
        "<<<<<<< SEARCH\n(exakter Originaltext, buchstabengenau inkl. Einrueckung)\n"
        "=======\n(verbesserter Text)\n>>>>>>> REPLACE\n"
        "Wenn nichts sinnvoll ist: antworte exakt NICHTS_ZU_TUN.\n\n"
        f"MODUL {name}:\n{code}"
    )
    ans=gb.ask_gemini(prompt).strip()
    if "NICHTS_ZU_TUN" in ans and "SEARCH" not in ans:
        return None, "JACK sieht gerade nichts sinnvoll zu verbessern."
    return ans, name

def apply_improvement(module, gemini_answer):
    path,name=_mod(module)
    if not os.path.exists(path):
        return False, f"Modul weg: {name}"
    original=open(path).read()
    import jack_patch
    ok,msg,preview=jack_patch.safe_patch(path, gemini_answer)
    if not ok:
        return False, f"Patch abgelehnt (Datei unveraendert): {msg}"
    modname=name[:-3]
    r=subprocess.run(["python3","-c",f"import {modname}"],cwd=JACK,
                     capture_output=True,text=True,timeout=25)
    if r.returncode!=0:
        open(path,"w").write(original)
        return False, f"ZURUECKGEROLLT - Modul liess sich nicht laden:\n{r.stderr.strip()[:300]}"
    subprocess.run(["git","add",name],cwd=JACK,capture_output=True)
    subprocess.run(["git","commit","-m",f"Selbstverbesserung {name} (JACK-Vorschlag, Dima-Freigabe)"],cwd=JACK,capture_output=True)
    subprocess.run(["git","push"],cwd=JACK,capture_output=True)
    return True, f"Verbessert + gesichert: {name}\n\n{preview}"
