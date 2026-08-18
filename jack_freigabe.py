#!/usr/bin/env python3
"""Gegenstueck zum AutoFixer-Kill-Switch: Vorschlaege ansehen und freigeben.
Freigabe nur wenn die Quelldatei seit dem Vorschlag unveraendert ist (Hash-Bindung)."""
import os, sys, json, hashlib, shutil, difflib, subprocess, time
V = os.path.expanduser("~/jack/patch_vorschlaege")
BACKUP = os.path.expanduser("~/jack/backups")

def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""): h.update(b)
    return h.hexdigest()

def _metas():
    if not os.path.isdir(V): return []
    r = []
    for f in sorted(os.listdir(V)):
        if f.endswith(".meta.json"):
            try:
                m = json.load(open(os.path.join(V, f)))
                m["_meta"] = f; m["_basis"] = f[:-10]
                r.append(m)
            except Exception: pass
    return r

def liste():
    ms = _metas()
    if not ms: return "Keine offenen Patch-Vorschlaege."
    z = ["Offene Vorschlaege (" + str(len(ms)) + "):"]
    for i, m in enumerate(ms, 1):
        quelle = m.get("source_realpath", "?")
        aktuell = _sha(quelle) if os.path.exists(quelle) else "WEG"
        frisch = "gueltig" if aktuell == m.get("source_sha256") else "VERALTET"
        z.append(str(i) + ") " + os.path.basename(quelle) + " [" + frisch + "] " +
                 str(m.get("summary", ""))[:60])
        z.append("   id=" + m["_basis"])
    z.append("\nAnsehen: python3 jack_freigabe.py zeige <nr>")
    z.append("Freigeben: python3 jack_freigabe.py freigabe <nr>")
    z.append("Verwerfen: python3 jack_freigabe.py verwirf <nr>")
    return "\n".join(z)

def _hole(nr):
    ms = _metas()
    try: return ms[int(nr) - 1]
    except Exception: return None

def zeige(nr):
    m = _hole(nr)
    if not m: return "Vorschlag " + str(nr) + " nicht gefunden."
    quelle = m["source_realpath"]
    vorschlag = os.path.join(V, m["_basis"] + ".vorschlag")
    if not os.path.exists(quelle) or not os.path.exists(vorschlag):
        return "Datei fehlt."
    a = open(quelle, encoding="utf-8", errors="replace").readlines()
    b = open(vorschlag, encoding="utf-8", errors="replace").readlines()
    d = list(difflib.unified_diff(a, b, "AKTUELL", "VORSCHLAG", n=2))
    kopf = ["Datei: " + quelle, "Grund: " + str(m.get("summary","")),
            "Erstellt: " + str(m.get("created_at","")),
            "Quelle unveraendert: " + ("JA" if _sha(quelle) == m.get("source_sha256") else "NEIN - VERALTET"),
            "Diff-Zeilen: " + str(len(d)), ""]
    return "\n".join(kopf) + "".join(d[:120])

def freigabe(nr):
    m = _hole(nr)
    if not m: return "Vorschlag nicht gefunden."
    quelle = m["source_realpath"]
    vorschlag = os.path.join(V, m["_basis"] + ".vorschlag")
    if os.path.islink(quelle) or os.path.islink(vorschlag):
        return "BLOCKIERT: Symlink im Pfad."
    if not os.path.exists(quelle) or not os.path.exists(vorschlag):
        return "BLOCKIERT: Datei fehlt."
    if _sha(quelle) != m.get("source_sha256"):
        return "BLOCKIERT: Quelldatei hat sich seit dem Vorschlag geaendert. Verwirf ihn und lass neu erzeugen."
    if _sha(vorschlag) != m.get("proposal_sha256"):
        return "BLOCKIERT: Vorschlagsdatei wurde manipuliert."
    r = subprocess.run(["python3","-m","py_compile",vorschlag], capture_output=True, text=True)
    if r.returncode != 0:
        return "BLOCKIERT: Vorschlag kompiliert nicht: " + r.stderr[:200]
    os.makedirs(BACKUP, exist_ok=True)
    bak = os.path.join(BACKUP, os.path.basename(quelle) + ".vor_freigabe_" + str(int(time.time())))
    shutil.copy2(quelle, bak)
    tmp = quelle + ".neu"
    shutil.copy2(vorschlag, tmp)
    os.replace(tmp, quelle)
    pruef = subprocess.run(["python3","-m","py_compile",quelle], capture_output=True, text=True)
    if pruef.returncode != 0:
        shutil.copy2(bak, quelle)
        return "ROLLBACK: nach Anwendung defekt, Original wiederhergestellt."
    for e in (".vorschlag", ".meta.json"):
        try: os.remove(os.path.join(V, m["_basis"] + e))
        except Exception: pass
    try:
        import jack_log; jack_log.log_decision("PATCH-FREIGABE", os.path.basename(quelle))
    except Exception: pass
    return "ANGEWANDT: " + os.path.basename(quelle) + "\nBackup: " + bak + "\nDienst ggf. neu starten."

def verwirf(nr):
    m = _hole(nr)
    if not m: return "Nicht gefunden."
    for e in (".vorschlag", ".meta.json"):
        try: os.remove(os.path.join(V, m["_basis"] + e))
        except Exception: pass
    return "Verworfen: " + m["_basis"]

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "liste"
    n = sys.argv[2] if len(sys.argv) > 2 else "1"
    print({"liste": lambda: liste(), "zeige": lambda: zeige(n),
           "freigabe": lambda: freigabe(n), "verwirf": lambda: verwirf(n)}.get(a, liste)())
