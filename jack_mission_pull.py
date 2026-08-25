#!/usr/bin/env python3
"""Pull pending missions from jack-missions repo into local queue."""
import os, subprocess, shutil, glob, sys

REPO = os.path.expanduser("~/jack-missions")
LOCAL_PENDING = os.path.expanduser("~/jack/missions/pending")
MAX_PULL = 10

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout + r.stderr

def pull():
    if not os.path.isdir(REPO):
        print("FEHLER: Repo fehlt:", REPO)
        sys.exit(1)
    rc, out = run(["git", "-C", REPO, "pull", "--ff-only", "origin", "main"])
    print("git pull:", out.strip()[:200])
    if rc != 0:
        print("PULL FEHLER")
        sys.exit(1)
    files = sorted(glob.glob(os.path.join(REPO, "pending", "*.json")))
    if not files:
        print("Keine neuen Missionen")
        return
    copied = 0
    for f in files:
        name = os.path.basename(f)
        dest = os.path.join(LOCAL_PENDING, name)
        log_path = os.path.join(os.path.expanduser("~/jack/missions/logs"), name)
        if os.path.exists(dest):
            print("Bereits lokal:", name)
            continue
        if os.path.exists(log_path):
            print("Bereits abgearbeitet:", name)
            continue
        shutil.copy2(f, dest)
        print("Kopiert:", name)
        copied += 1
    print(f"Pull fertig: {copied} neue Mission(en)")

if __name__ == "__main__":
    pull()
