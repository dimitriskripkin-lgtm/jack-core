#!/usr/bin/env python3
# jack_aufraeumen.py - analysiert und archiviert. Loescht NIE.
import os, re, sys, json, shutil, sqlite3, subprocess
from datetime import datetime
H = os.path.expanduser("~/jack")
ARCH = os.path.expanduser("~/jack_archiv")
JOURNAL = os.path.join(ARCH, "journal.json")
TESTMUSTER = ("test_", "_test", "_ab_test", "calltest", "quick_", "install_", "inventur")

def py_dateien():
    return sorted(f for f in os.listdir(H) if f.endswith(".py"))

def lies(f):
    try:
        return open(os.path.join(H, f), encoding="utf-8", errors="replace").read()
    except Exception:
        return ""

def hat_main(f):
    return "__main__" in lies(f)

def import_graph():
    pys = py_dateien()
    namen = {f[:-3] for f in pys}
    imp = {}
    for f in pys:
        s = lies(f)
        for m in re.findall(r"^\s*(?:from|import)\s+([a-zA-Z_]\w*)", s, re.M):
            if m in namen and m != f[:-3]:
                imp.setdefault(m, set()).add(f[:-3])
    return imp

def externe_refs():
    """Sucht Modulnamen als String in sh, run-Skripten und crontab."""
    treffer = {}
    texte = []
    pfade = [os.environ.get("PREFIX", "") + "/var/service",
             os.path.expanduser("~/.termux/boot"), H]
    for p in pfade:
        if not os.path.isdir(p):
            continue
        for w, _, fs in os.walk(p):
            if "__pycache__" in w or "jack_archiv" in w:
                continue
            for fn in fs:
                if fn.endswith((".sh", ".py")) or fn == "run":
                    try:
                        texte.append(open(os.path.join(w, fn),
                                     encoding="utf-8", errors="replace").read())
                    except Exception:
                        pass
    try:
        texte.append(subprocess.check_output(["crontab", "-l"],
                     stderr=subprocess.DEVNULL, timeout=5).decode())
    except Exception:
        pass
    blob = "\n".join(texte)
    for f in py_dateien():
        n = blob.count(f)
        if n > 0:
            treffer[f[:-3]] = n
    return treffer

def klassifiziere():
    imp = import_graph()
    ext = externe_refs()
    aus = {"KERN": [], "DIENST": [], "WERKZEUG": [], "TEST": [], "KANDIDAT": []}
    for f in py_dateien():
        n = f[:-3]
        nutzer = len(imp.get(n, ()))
        extern = ext.get(n, 0)
        main = hat_main(f)
        if nutzer >= 1:
            aus["KERN"].append((n, nutzer, extern, main))
        elif extern >= 2:
            aus["DIENST"].append((n, nutzer, extern, main))
        elif any(t in n for t in TESTMUSTER):
            aus["TEST"].append((n, nutzer, extern, main))
        elif main:
            aus["WERKZEUG"].append((n, nutzer, extern, main))
        else:
            aus["KANDIDAT"].append((n, nutzer, extern, main))
    return aus

def analyse():
    a = klassifiziere()
    for k in ("KERN", "DIENST", "WERKZEUG", "TEST", "KANDIDAT"):
        print("=== " + k + " (" + str(len(a[k])) + ") ===")
        for n, nu, ex, mn in sorted(a[k]):
            print("  " + n.ljust(30) + " imp=" + str(nu) +
                  " ext=" + str(ex) + (" main" if mn else ""))
        print("")
    print("ARCHIV-KANDIDATEN: " + str(len(a["TEST"]) + len(a["KANDIDAT"])))
    print("Nichts wurde veraendert. Analyse only.")

def archiviere():
    a = klassifiziere()
    ziel = a["TEST"] + a["KANDIDAT"]
    if not ziel:
        print("Nichts zu archivieren.")
        return
    os.makedirs(ARCH, exist_ok=True)
    j = json.load(open(JOURNAL)) if os.path.exists(JOURNAL) else []
    ts = datetime.now().isoformat(timespec="seconds")
    for n, nu, ex, mn in ziel:
        src = os.path.join(H, n + ".py")
        dst = os.path.join(ARCH, n + ".py")
        if os.path.exists(src):
            shutil.move(src, dst)
            j.append({"datei": n + ".py", "ts": ts, "imp": nu, "ext": ex})
            print("ARCHIVIERT: " + n)
    json.dump(j, open(JOURNAL, "w"), indent=1)
    print("Journal: " + JOURNAL)
    print("Zurueck mit: python3 jack_aufraeumen.py zurueck DATEINAME")

def zurueck(name):
    src = os.path.join(ARCH, name)
    if not os.path.exists(src):
        print("Nicht im Archiv: " + name)
        return
    shutil.move(src, os.path.join(H, name))
    print("ZURUECK: " + name)

if __name__ == "__main__":
    m = sys.argv[1] if len(sys.argv) > 1 else "analyse"
    if m == "analyse":
        analyse()
    elif m == "archiv":
        archiviere()
    elif m == "zurueck" and len(sys.argv) > 2:
        zurueck(sys.argv[2])
    else:
        print("Modi: analyse | archiv | zurueck DATEI")
