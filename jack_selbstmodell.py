# JACK_TUNE_SELBSTMODELL: Jack weiss, was sich an seinem Code und seiner Doku geaendert hat (nur lesen)
import os, subprocess, time, glob
J = os.path.expanduser("~/jack")

def aenderungen(stunden=10, maxn=6):
    """Kurzer Satz: Commits und geaenderte Handbuch-Kapitel im Zeitfenster. Leer wenn nichts."""
    out = []
    try:
        r = subprocess.run(["git", "log", "--since=%d hours ago" % int(stunden), "--format=%s", "-n", "30"],
                           cwd=J, capture_output=True, text=True, timeout=10)
        subj = [s.strip()[:90] for s in r.stdout.splitlines() if s.strip()]
        if subj:
            out.append("Code/Doku: %d Commits, zuletzt: %s" % (len(subj), " / ".join(subj[:3])))
    except Exception:
        pass
    try:
        cut = time.time() - int(stunden) * 3600
        neu = sorted((os.path.getmtime(p), os.path.basename(p)) for p in glob.glob(J + "/BETRIEBSHANDBUCH/*.md")
                     if os.path.getmtime(p) >= cut)
        if neu:
            out.append("Handbuch neu/geaendert: " + ", ".join(n.split("_")[0] for _, n in neu[-maxn:]))
    except Exception:
        pass
    return " | ".join(out)

if __name__ == "__main__":
    print(aenderungen(24) or "(nichts)")
