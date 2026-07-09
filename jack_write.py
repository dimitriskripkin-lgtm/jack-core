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
    # roher Pfad OHNE Saeuberung zur echten Grenzkontrolle
    raw = os.path.realpath(os.path.join(WERKSTATT, filename))
    root = os.path.realpath(WERKSTATT)
    if not (raw == root or raw.startswith(root + os.sep)):
        return False, "BLOCKIERT: Ausbruch aus der Werkstatt verhindert"
    fn = _safe_name(filename)
    path = os.path.join(WERKSTATT, fn)
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


def detect_write_request(prompt):
    """Fragt Gemini ob Dima eine Datei geschrieben haben will.
    Gibt dict mit filename+content zurueck, sonst None."""
    import json as _j
    import jack_gemini_bridge as _gb
    import datetime as _dt
    _stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M")
    q = (
        f"AKTUELLES DATUM/ZEIT: {_stamp}\n"
        "Analysiere diese Nachricht von Dima. Will er eine DATEI SCHREIBEN lassen?\n"
        "Wenn er einen Zeitstempel im Dateinamen will, setze das echte Datum von oben ein. "
        "NIEMALS Platzhalter wie TIMESTAMP oder geschweifte Klammern verwenden. "
        "Dateiname nur Buchstaben, Zahlen, Unterstrich, Punkt.\n"
        "Wenn JA: antworte NUR mit JSON: {\"write\": true, \"filename\": \"...\", \"content\": \"...\"}\n"
        "Wenn NEIN: antworte NUR mit JSON: {\"write\": false}\n"
        "Kein Markdown, keine Erklaerung, nur JSON.\n\n"
        f"NACHRICHT: {prompt}"
    )
    try:
        ans = _gb.ask_gemini(q).strip()
        if ans.startswith("```"):
            ans = "\n".join(ans.split("\n")[1:])
        if ans.endswith("```"):
            ans = "\n".join(ans.split("\n")[:-1])
        d = _j.loads(ans.strip())
        if d.get("write") and d.get("filename") and d.get("content") is not None:
            return {"filename": d["filename"], "content": d["content"]}
    except Exception:
        pass
    return None
