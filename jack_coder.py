#!/usr/bin/env python3
"""JACK schreibt und testet Code - NUR in der Werkstatt, mit Risiko-Gate."""
import os, re, subprocess, time

WERKSTATT = os.path.expanduser("~/jack_werkstatt")

HIGH_RISK = [
    "rm -rf", "rmtree", "os.remove", "os.unlink", "os.rmdir", "shutil.rmtree",
    "shutil.move", "drop table", "delete from", ":(){", "mkfs", "dd if=",
    "> /dev", "chmod -r", "chown -r", "os.system", "subprocess", "eval(",
    "exec(", "__import__", "socket", "urllib", "requests.", "open('/data",
    'open("/data', ".ssh", "jack_secrets", "telegram", "api_key", "os.environ",
]

def _safe_name(name):
    name = os.path.basename(name.strip())
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", name) or "script.py"
    if not name.endswith(".py"):
        name += ".py"
    return name

def _in_werkstatt(path):
    return os.path.realpath(path).startswith(os.path.realpath(WERKSTATT) + os.sep)

def assess_risk(code):
    low = code.lower()
    for p in HIGH_RISK:
        if p in low:
            return p
    return None

def write_code(task, filename=None):
    import jack_gemini_bridge as gb
    prompt = (
        "Du bist JACKs Programmierer. Schreibe vollstaendigen, lauffaehigen Python-Code "
        "fuer die Aufgabe. NUR Code, keine Erklaerung, keine Markdown-Zaeune. "
        "Keine Netzwerkzugriffe, keine Datei-Loeschungen, kein Zugriff ausserhalb des Ordners.\n\n"
        f"AUFGABE: {task}"
    )
    code = gb.ask_gemini(prompt).strip()
    if code.startswith("Gemini") and any(m in code for m in ("Rate-Limit","ueberlastet","Verbindungsfehler")):
        return None, None, code
    if code.startswith("```"):
        code = "\n".join(code.split("\n")[1:])
    if code.endswith("```"):
        code = "\n".join(code.split("\n")[:-1])
    code = code.strip()
    fn = _safe_name(filename or ("script_" + time.strftime("%Y%m%d_%H%M")))
    path = os.path.join(WERKSTATT, fn)
    if not _in_werkstatt(path):
        return None, None, "BLOCKIERT: ausserhalb Werkstatt"
    os.makedirs(WERKSTATT, exist_ok=True)
    with open(path, "w") as f:
        f.write(code)
    return fn, code, "OK"

def run_code(filename, timeout=10):
    fn = _safe_name(filename)
    path = os.path.join(WERKSTATT, fn)
    if not _in_werkstatt(path):
        return False, "BLOCKIERT: ausserhalb Werkstatt"
    if not os.path.exists(path):
        return False, f"Datei fehlt: {fn}"
    code = open(path).read()
    risk = assess_risk(code)
    if risk:
        return False, f"AUSFUEHRUNG BLOCKIERT - gefaehrliches Muster: {risk!r}"
    r = subprocess.run(["python3", "-m", "py_compile", path], capture_output=True, text=True)
    if r.returncode != 0:
        return False, f"SyntaxError: {r.stderr.strip()[:300]}"
    try:
        p = subprocess.run(["python3", path], capture_output=True, text=True,
                           timeout=timeout, cwd=WERKSTATT)
        out = (p.stdout + p.stderr).strip()
        return True, out[:1500] if out else f"(kein Output, Exit {p.returncode})"
    except subprocess.TimeoutExpired:
        return False, f"Abgebrochen: laenger als {timeout}s (Endlosschleife?)"
    except Exception as e:
        return False, str(e)
