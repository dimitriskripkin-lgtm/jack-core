#!/usr/bin/env python3
"""JACK_TUNE_SANDBOX Uebungsplatz. Schreibt und laeuft nur unter jack_sandbox. Kern bleibt zu."""
import os, re, json, time, subprocess
HOME = "/data/data/com.termux/files/home"
BOX = HOME + "/jack_sandbox"
JACK = HOME + "/jack"
VERBOTEN = (JACK, "ssh ", "sv ", "config.ini", ".jack_mcp_token", "git push", "pending_approvals")

def _name(name):
    if not re.match(r"^[a-z0-9_]{3,40}$", str(name or "")):
        return ""
    return str(name)

def schreiben(name, code):
    n = _name(name)
    text = str(code or "")
    if not n:
        return False, "name ungueltig"
    if len(text) > 4000:
        return False, "zu lang"
    low = text.lower()
    for v in VERBOTEN:
        if v.lower() in low:
            return False, "verboten: kern"
    os.makedirs(BOX, exist_ok=True)
    path = BOX + "/" + n + ".py"
    open(path, "w").write(text)
    return True, path

def laufen(name, timeout=8):
    n = _name(name)
    path = BOX + "/" + n + ".py"
    if not n or not os.path.isfile(path):
        return False, "script fehlt"
    try:
        r = subprocess.run(
            ["python3", "-I", path],
            cwd=BOX,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={"PATH": "/data/data/com.termux/files/usr/bin", "HOME": BOX, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        out = ((r.stdout or "") + (r.stderr or ""))[:400]
        ok = r.returncode == 0
        open(BOX + "/" + n + ".result.json", "w").write(json.dumps({"ok": ok, "out": out, "ts": time.time()}))
        return ok, out
    except subprocess.TimeoutExpired:
        return False, "timeout"

def probe():
    ok, pfad = schreiben("probe_hallo", "print('SANDBOX_OK')\n")
    if not ok:
        return False, pfad
    ok2, out = laufen("probe_hallo")
    schlecht, warum = schreiben("probe_kern", "open('" + JACK + "/jack_telegram.py','w').write('x')\n")
    return ok2 and (not schlecht), "lauf " + out.strip() + " | kern " + warum
