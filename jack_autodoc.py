#!/usr/bin/env python3
"""jack_autodoc.py — Gemini schreibt fehlende Docstrings automatisch (staged).

Scannt Core-Module auf Funktionen ohne Docstring, lässt Gemini einen schreiben,
staged den Fix zur Genehmigung. Max 2 Dateien / 5 Funktionen pro Lauf.
"""
MODULE_VERSION = 1

import os, sys, json, time, ast, re
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_autodoc")

PEND    = os.path.join(J, "missions", "pending")
SHADOW  = os.path.join(J, "shadow")
APPROVALS = os.path.join(J, "pending_approvals.json")
STATE   = os.path.join(J, "autodoc_last_run.json")
MAX_FILES   = 2
MAX_FUNCS   = 5

CORE_TARGETS = [
    "jack_graph.py", "jack_heartbeat.py", "jack_cortex.py",
    "jack_oracle.py", "jack_ollama_gate.py", "jack_chat_router.py",
    "jack_mission_runner.py", "jack_gemini_bridge.py",
]

def load_state():
    try: return json.load(open(STATE))
    except Exception: return {"done": {}}

def save_state(s):
    json.dump(s, open(STATE,'w'))

def get_undocumented(fpath):
    """Findet Funktionen ohne Docstring via AST."""
    try:
        src = open(fpath).read()
        tree = ast.parse(src)
        lines = src.splitlines()
        missing = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"): continue  # Private skip
                docstring = ast.get_docstring(node)
                if not docstring:
                    # Code-Snippet für Gemini (erste 8 Zeilen der Funktion)
                    start = node.lineno - 1
                    snippet = "\n".join(lines[start:start+8])
                    missing.append({
                        "name": node.name,
                        "line": node.lineno,
                        "col": node.col_offset,
                        "snippet": snippet
                    })
        return missing
    except Exception as e:
        log.exception("AST-Parse fehlgeschlagen", e)
        return []

def gemini_docstring(fname, func_info):
    """Lässt Gemini einen Docstring schreiben."""
    try:
        import jack_gemini_bridge as _jgb
        prompt = f"""Schreibe einen kurzen Python-Docstring (1-2 Sätze, Deutsch) für diese Funktion.
Antworte NUR mit dem Docstring-Text ohne Anführungszeichen und ohne ```-Blöcke.
Beispiel: Prüft ob der SSH-Port auf Xiaomi erreichbar ist.

Datei: {fname}
Funktion: {func_info['name']}
Code:
{func_info['snippet']}"""
        result = _jgb.ask_gemini(prompt)
        if result:
            return result.strip().strip('"').strip("'")[:200]
    except Exception as e:
        log.exception("Gemini Docstring fehlgeschlagen", e)
    return None

def write_staged_fix(fname, func_info, docstring):
    """Schreibt staged Fix mit Docstring-Insertion."""
    try:
        fpath = os.path.join(J, fname)
        src = open(fpath).read()
        lines = src.splitlines(keepends=True)

        # Zeile nach def-Statement finden
        def_line = func_info["line"] - 1
        indent = " " * (func_info["col"] + 4)
        doc_line = f'{indent}"""{docstring}"""\n'

        # Prüfen ob schon ein Docstring da ist
        next_line = lines[def_line + 1] if def_line + 1 < len(lines) else ""
        if '"""' in next_line or "'''" in next_line:
            return False  # Schon vorhanden

        lines.insert(def_line + 1, doc_line)
        new_src = "".join(lines)

        # Staged schreiben
        os.makedirs(SHADOW, exist_ok=True)
        staged = os.path.join(SHADOW, fname + ".staged")
        open(staged, 'w').write(new_src)

        # Approval-Eintrag
        mid = f"autodoc_{fname.replace('.py','')}_{func_info['name']}"
        entry = {
            "id": mid,
            "file": f"~/jack/{fname}",
            "act": "autodoc",
            "desc": f"Docstring: {func_info['name']}() — {docstring[:50]}",
            "staged_path": staged,
        }
        try:
            data = json.load(open(APPROVALS)) if os.path.exists(APPROVALS) else []
            if not isinstance(data, list): data = []
            if not any(e.get("id")==mid for e in data):
                data.append(entry)
                json.dump(data, open(APPROVALS,'w'))
        except Exception: pass

        log.info(f"Staged: {func_info['name']}() in {fname}")
        return True
    except Exception as e:
        log.exception("Staged-Write fehlgeschlagen", e)
        return False

def run():
    state = load_state()
    done = state.get("done", {})
    files_done = 0
    funcs_done = 0

    for fname in CORE_TARGETS:
        if files_done >= MAX_FILES or funcs_done >= MAX_FUNCS:
            break
        fpath = os.path.join(J, fname)
        if not os.path.exists(fpath): continue

        missing = get_undocumented(fpath)
        if not missing: continue

        # Nur neue (noch nicht bearbeitete) Funktionen
        done_funcs = done.get(fname, [])
        missing = [f for f in missing if f["name"] not in done_funcs]
        if not missing: continue

        log.info(f"{fname}: {len(missing)} Funktionen ohne Docstring")
        files_done += 1

        for func_info in missing[:3]:
            if funcs_done >= MAX_FUNCS: break
            docstring = gemini_docstring(fname, func_info)
            if not docstring: continue
            if write_staged_fix(fname, func_info, docstring):
                done_funcs.append(func_info["name"])
                funcs_done += 1
            time.sleep(1)

        done[fname] = done_funcs

    state["done"] = done
    state["last_run"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_state(state)
    log.info(f"Autodoc: {funcs_done} Docstrings staged")
    return funcs_done

if __name__ == "__main__":
    n = run()
    print(f"Autodoc: {n} Docstrings staged")
