#!/usr/bin/env python3
import os, re, datetime

WERKSTATT = os.path.expanduser("~/jack_werkstatt")

def _safe_name(name):
    name = os.path.basename(name.strip())
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    if not name:
        name = "notiz.txt"
    if "." not in name:
        name += ".txt"
    return name

def propose(filename, content):
    fn = _safe_name(filename)
    preview = content if len(content) <= 200 else content[:200] + "..."
    return {
        "filename": fn,
        "path": os.path.join(WERKSTATT, fn),
        "content": content,
        "preview": preview
    }

def commit_write(filename, content):
    fn = _safe_name(filename)
    path = os.path.join(WERKSTATT, fn)
    real = os.path.realpath(path)
    if not real.startswith(os.path.realpath(WERKSTATT) + os.sep):
        return False, "BLOCKIERT: Pfad ausserhalb der Werkstatt"
    try:
        with open(path, "w") as f:
            f.write(content)
        return True, f"Geschrieben: {fn} ({len(content)} Zeichen) in ~/jack_werkstatt"
    except Exception as e:
        return False, f"Fehler: {e}"

if __name__ == "__main__":
    p = propose("test datei", "Hallo aus der Werkstatt")
    print("Vorschlag:", p["path"])
    ok, msg = commit_write(p["filename"], p["content"])
    print(ok, msg)
    # Sicherheitstest: Ausbruch aus der Werkstatt
    ok2, msg2 = commit_write("../../HACK.txt", "sollte blockiert sein")
    print("Ausbruch-Test:", ok2, msg2)
