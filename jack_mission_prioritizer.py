#!/usr/bin/env python3
"""jack_mission_prioritizer.py — Sortiert pending/ nach Priorität."""
MODULE_VERSION = 1

import os, sys, json, time
J = os.path.expanduser("~/jack")
PEND = os.path.join(J, "missions", "pending")
LOG = os.path.join(J, "prioritizer.log")

PRIO = {
    "security": 0,
    "deadman": 1,
    "health": 2,
    "trainer": 3,
    "quality_autofix": 4,
    "quality": 5,
    "arch": 6,
    "version": 7,
    "size": 8,
    "analyzer_bare_except": 4,
    "analyzer_hardcoded_path": 6,
    "analyzer_no_module_version": 7,
    "analyzer_print_debug": 5,
    "analyzer_hardcoded_ip": 0,
    "analyzer_todo_fixme": 8,
    "version_autofix": 7,
    "quality_nacht": 5,
    "arch_nacht": 6,
}

def run():
    if not os.path.exists(PEND): return 0
    missions = []
    for f in os.listdir(PEND):
        if not f.endswith(".json"): continue
        try:
            m = json.load(open(os.path.join(PEND, f)))
            cat = m.get("cat","zzz")
            prio = PRIO.get(cat, 50)
            missions.append((prio, f, m))
        except Exception: pass

    missions.sort(key=lambda x: x[0])
    # Umbenennen mit Prio-Prefix damit runner sortiert aufnimmt
    # Da runner FIFO macht — wir schreiben Prio ins JSON
    for prio, fname, m in missions:
        m["_prio"] = prio
        open(os.path.join(PEND, fname),"w").write(json.dumps(m))

    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG,"a") as f:
        f.write(f"{ts} Priorisiert: {len(missions)} Missions\n")
    return len(missions)

if __name__ == "__main__":
    n = run()
    print(f"Prioritizer: {n} Missions sortiert")
