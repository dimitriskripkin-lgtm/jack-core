#!/usr/bin/env python3
"""jack_semantic_analyzer.py — Gemini reviewt Core-Module qualitativ.

Schickt Code-Chunks an Gemini, kriegt strukturiertes JSON mit Findings,
schreibt daraus staged Fix-Missions. Max 3 Dateien pro Lauf (Budget-Schutz).
"""
MODULE_VERSION = 1

import os, sys, json, time, glob
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_semantic_analyzer")

PEND    = os.path.join(J, "missions", "pending")
STATE   = os.path.join(J, "semantic_last_run.json")
MAX_FILES_PER_RUN = 3
MAX_LINES_PER_FILE = 120  # Nur erste N Zeilen — Budget schonen

# Core-Module in Priorität
CORE_TARGETS = [
    "jack_cortex.py",
    "jack_autonomous.py",
    "jack_graph.py",
    "jack_heartbeat.py",
    "jack_gemini_bridge.py",
    "jack_chat_router.py",
    "jack_mission_runner.py",
    "jack_missions.py",
    "jack_oracle.py",
    "jack_ollama_gate.py",
]

GEMINI_PROMPT = """Du bist Code-Reviewer für ein autonomes KI-System auf Android/Termux.
Analysiere diesen Python-Code und antworte NUR mit einem JSON-Array.
Format:
[
  {{"severity": "P0|P1|P2", "type": "bug|security|perf|style", "line": 42, "msg": "kurze Beschreibung", "fix": "konkreter Fix-Vorschlag"}}
]
Regeln:
- P0 = Crash/Security-Risiko, P1 = echter Bug, P2 = Verbesserung
- Maximal 5 Findings
- Nur echte Probleme, keine stilistischen Kleinigkeiten
- fix-Feld: konkreter Python-Code-Snippet oder Beschreibung
- Antworte NUR mit dem JSON-Array, kein Text davor/danach

Code:
```python
{code}
```"""

def load_state():
    try: return json.load(open(STATE))
    except Exception: return {"analyzed": {}}

def save_state(s):
    json.dump(s, open(STATE,'w'))

def get_file_hash(fpath):
    try:
        import hashlib
        return hashlib.md5(open(fpath,'rb').read()).hexdigest()[:8]
    except Exception: return "?"

def call_gemini(code):
    try:
        import jack_gemini_bridge as _jgb
        prompt = GEMINI_PROMPT.format(code=code)
        result = _jgb.ask_gemini(prompt)
        if not result: return []
        # JSON extrahieren
        import re
        m = re.search(r'\[.*\]', result, re.DOTALL)
        if m:
            return json.loads(m.group())
    except Exception as e:
        log.exception("Gemini-Call fehlgeschlagen", e)
    return []

def write_mission(fname, finding, idx):
    mname = fname.replace(".py","")
    sev = finding.get("severity","P2")
    ftype = finding.get("type","style")
    line = finding.get("line", 0)
    msg = finding.get("msg","?")[:60]
    fix = finding.get("fix","")[:200]

    mid = f"sem_{mname}_{sev}_{idx}_{int(time.time())}"
    mpath = os.path.join(PEND, f"{mid}.json")
    if os.path.exists(mpath): return False

    m = {
        "id": mid,
        "typ": "check",
        "cat": f"semantic_{ftype}",
        "file": f"~/jack/{fname}",
        "act": "compile_ok",
        "desc": f"[{sev}] L{line}: {msg}",
        "fix_hint": fix,
        "_prio": 0 if sev=="P0" else (1 if sev=="P1" else 3),
        "_source": "semantic_analyzer"
    }
    json.dump(m, open(mpath,'w'))
    log.info(f"{fname} [{sev}] L{line}: {msg}")
    return True

def run():
    state = load_state()
    analyzed = state.get("analyzed", {})

    files_done = 0
    missions_written = 0

    for fname in CORE_TARGETS:
        if files_done >= MAX_FILES_PER_RUN:
            break

        fpath = os.path.join(J, fname)
        if not os.path.exists(fpath): continue

        fhash = get_file_hash(fpath)
        if analyzed.get(fname) == fhash:
            continue  # Nicht verändert seit letztem Scan

        # Code laden (Budget schonen)
        lines = open(fpath).readlines()
        code = "".join(lines[:MAX_LINES_PER_FILE])
        if len(lines) > MAX_LINES_PER_FILE:
            code += f"\n# ... ({len(lines)-MAX_LINES_PER_FILE} weitere Zeilen)\n"

        log.info(f"Analysiere {fname} ({len(lines)} Zeilen)")
        findings = call_gemini(code)

        for i, f_ in enumerate(findings[:5]):
            if write_mission(fname, f_, i):
                missions_written += 1

        analyzed[fname] = fhash
        files_done += 1
        time.sleep(1)  # Rate-limit

    state["analyzed"] = analyzed
    state["last_run"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_state(state)

    log.info(f"Semantic: {files_done} Dateien, {missions_written} Missions")
    return missions_written

if __name__ == "__main__":
    n = run()
    print(f"Semantic Analyzer: {n} neue Missions")
