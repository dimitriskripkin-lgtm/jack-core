#!/usr/bin/env python3
"""jack_dep_map.py — Import-Graph für alle JACK-Module.

Erkennt welche Module von einem geänderten Modul abhängen,
propagiert Verify-Missions zu allen Importeuren,
meldet zirkuläre Imports.
"""
MODULE_VERSION = 1

import os, sys, ast, json, time, glob
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_dep_map")

PEND   = os.path.join(J, "missions", "pending")
GRAPH  = os.path.join(J, "dep_graph.json")
STATE  = os.path.join(J, "dep_map_state.json")

def build_graph():
    """Scannt alle jack_*.py und baut Import-Graph."""
    graph = {}  # {modul: [importiert_von_modul, ...]}
    files = glob.glob(os.path.join(J, "jack_*.py"))

    for fpath in files:
        fname = os.path.basename(fpath)
        mname = fname.replace(".py", "")
        try:
            src = open(fpath).read()
            tree = ast.parse(src)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("jack_"):
                            imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith("jack_"):
                        imports.append(node.module)
            graph[mname] = list(set(imports))
        except Exception:
            graph[mname] = []

    return graph

def find_circular(graph):
    """Findet zirkuläre Imports via DFS."""
    circular = []
    visited = set()

    def dfs(node, path):
        if node in path:
            cycle = path[path.index(node):] + [node]
            circular.append(cycle)
            return
        if node in visited: return
        visited.add(node)
        for dep in graph.get(node, []):
            dfs(dep, path + [node])

    for node in graph:
        dfs(node, [])
    return circular

def find_importers(graph, target_module):
    """Wer importiert target_module?"""
    mname = target_module.replace(".py","")
    return [m for m, deps in graph.items() if mname in deps]

def propagate_verify(changed_files, graph):
    """Für geänderte Module: Verify-Missions auch für Importeure."""
    written = 0
    for fname in changed_files:
        mname = fname.replace(".py","")
        importers = find_importers(graph, mname)
        for importer in importers:
            mid = f"dep_verify_{importer}_after_{mname}_{int(time.time())}"
            mpath = os.path.join(PEND, f"{mid}.json")
            if os.path.exists(mpath): continue
            m = {
                "id": mid,
                "typ": "check",
                "cat": "dep_verify",
                "act": "compile_ok",
                "file": f"~/jack/{importer}.py",
                "desc": f"Verify {importer} nach Änderung von {mname}",
                "_prio": 2,
                "_source": "dep_map"
            }
            json.dump(m, open(mpath,'w'))
            written += 1
    return written

def run():
    graph = build_graph()
    json.dump(graph, open(GRAPH,'w'), indent=2)

    # Zirkuläre Imports melden
    circular = find_circular(graph)
    if circular:
        for cycle in circular[:3]:
            log.warn(f"Zirkulär: {' → '.join(cycle)}")

    # Geänderte Dateien seit letztem Lauf
    state = {}
    try: state = json.load(open(STATE))
    except Exception: pass

    last_hashes = state.get("hashes", {})
    import hashlib
    current_hashes = {}
    changed = []

    for fpath in glob.glob(os.path.join(J, "jack_*.py")):
        fname = os.path.basename(fpath)
        try:
            h = hashlib.md5(open(fpath,'rb').read()).hexdigest()[:8]
            current_hashes[fname] = h
            if last_hashes.get(fname) != h:
                changed.append(fname)
        except Exception: pass

    # Verify-Missions propagieren
    written = 0
    if changed and last_hashes:  # Nicht beim ersten Lauf
        written = propagate_verify(changed, graph)
        if written:
            log.info(f"Propagiert: {written} Missions für {len(changed)} geänderte Module")

    state["hashes"] = current_hashes
    state["last_run"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    state["module_count"] = len(graph)
    state["circular_count"] = len(circular)
    json.dump(state, open(STATE,'w'))

    log.info(f"Dep-Map: {len(graph)} Module, {len(circular)} Zyklen, {written} neue Missions")
    return written

if __name__ == "__main__":
    n = run()
    g = json.load(open(os.path.join(J,"dep_graph.json")))
    print(f"Dep-Map: {len(g)} Module gescannt")
    # Zirkuläre anzeigen
    circ = find_circular(g)
    if circ:
        print(f"⚠️  {len(circ)} zirkuläre Imports:")
        for c in circ[:5]: print(f"  {' → '.join(c)}")
    else:
        print("✓ Keine zirkulären Imports")
    print(f"Neue Missions: {n}")
