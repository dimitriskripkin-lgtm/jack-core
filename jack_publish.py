#!/usr/bin/env python3
"""Veroeffentlicht SANITIERTEN JACK-Kontext oeffentlich fuer Claude/andere KIs.
NIEMALS Secrets/Keys/Tokens - nur Struktur, Status, Logbuch-Zusammenfassung."""
import os, subprocess, datetime, re
H=os.path.expanduser("~/jack")
OUT=os.path.expanduser("~/jack-context")
BAD=re.compile(r'(AQ\.[A-Za-z0-9_-]{10}|sk_[a-zA-Z0-9]{10}|AIza[A-Za-z0-9_-]{10}|gh[ps]_[A-Za-z0-9]{10}|[0-9]{9,10}:AA[A-Za-z0-9_-]{10})')

def sh(c,cwd=None):
    try: return subprocess.run(c,shell=True,capture_output=True,text=True,timeout=25,cwd=cwd).stdout.strip()
    except Exception: return ""

def scrub(t):
    return "\n".join("[ZEILE ENTFERNT: Secret]" if BAD.search(l) else l for l in t.split("\n"))

def build():
    sh(f"cd {H} && python3 jack_snapshot.py")
    p=[f"# JACK LIVE-KONTEXT (auto, {datetime.datetime.now().isoformat()})\n"]
    try: p.append(open(f"{H}/jack_context.md").read())
    except Exception as e: p.append(f"(snapshot fehlt: {e})")
    p.append("\n## Letzte 20 Aktionen (Logbuch)\n")
    p.append(sh(f"tail -20 {H}/jack_decisions.log") or "(kein Log)")
    try:
        import jack_budget; p.append("\n## Budget heute\n"+jack_budget.status())
    except Exception: pass
    text=scrub("\n".join(p))
    os.makedirs(OUT,exist_ok=True)
    open(f"{OUT}/context.md","w").write(text)
    return text

if __name__=="__main__":
    build()
    print(sh("git add -A && git commit -m auto-context && git branch -M main && git push -u origin main", cwd=OUT) or "(nichts neu)")
