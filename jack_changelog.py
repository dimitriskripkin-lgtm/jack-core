#!/usr/bin/env python3
"""jack_changelog.py — Git-Delta → Verify-Missions für veränderte Module."""
MODULE_VERSION = 1

import os, sys, subprocess, json, time
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
PEND = os.path.join(J, "missions", "pending")
LOG = os.path.join(J, "changelog.log")
STATE = os.path.join(J, "changelog_last_commit.txt")

def _log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG,"a") as f: f.write(f"{ts} {msg}\n")

def get_last_commit():
    try:
        r = subprocess.run(["git","-C",J,"rev-parse","HEAD"],
            capture_output=True,text=True,timeout=10)
        return r.stdout.strip()
    except Exception: return None

def get_changed_files(since_commit):
    try:
        r = subprocess.run(["git","-C",J,"diff","--name-only",since_commit,"HEAD"],
            capture_output=True,text=True,timeout=10)
        return [f.strip() for f in r.stdout.splitlines() if f.endswith(".py")]
    except Exception: return []

def run():
    current = get_last_commit()
    if not current: return 0

    last = open(STATE).read().strip() if os.path.exists(STATE) else None
    if last == current:
        return 0  # nichts verändert

    changed = get_changed_files(last) if last else []
    _log(f"Commit {current[:8]}: {len(changed)} Dateien verändert")

    written = 0
    for fname in changed:
        fpath = os.path.join(J, fname)
        if not os.path.exists(fpath): continue
        base = fname.replace(".py","")
        missions = [
            {"id":f"chg_compile_{base}","typ":"check","act":"compile_ok",
             "file":f"~/jack/{fname}","cat":"changelog"},
            {"id":f"chg_mv_{base}","typ":"check","act":"grep_count",
             "file":f"~/jack/{fname}","pattern":"MODULE_VERSION","expect_min":1,"expect":"PASS","cat":"changelog"},
            {"id":f"chg_exc_{base}","typ":"check","act":"grep_count",
             "file":f"~/jack/{fname}","pattern":"    except:","expect_max":0,"expect":"PASS","cat":"changelog"},
        ]
        for m in missions:
            path = os.path.join(PEND, f"{m['id']}.json")
            if not os.path.exists(path):
                open(path,"w").write(json.dumps(m))
                written += 1

    open(STATE,"w").write(current)
    _log(f"changelog: {written} Verify-Missions für {len(changed)} veränderte Module")
    return written

if __name__ == "__main__":
    n = run()
    print(f"Changelog: {n} neue Verify-Missions")
