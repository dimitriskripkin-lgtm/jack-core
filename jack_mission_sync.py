#!/usr/bin/env python3
"""Pulled GitHub jack-missions -> ~/jack/missions/pending/"""
import os, subprocess, shutil, json

REPO   = "https://github.com/dimitriskripkin-lgtm/jack-missions.git"
LOCAL  = os.path.expanduser("~/jack-missions")
TARGET = os.path.expanduser("~/jack/missions/pending")

def sync():
    os.makedirs(TARGET, exist_ok=True)
    subprocess.run(["git","-C",LOCAL,"pull","--ff-only"],
        capture_output=True, timeout=30)
    src = os.path.join(LOCAL,"pending")
    copied = 0
    for f in os.listdir(src):
        if not f.endswith(".json") or f.startswith("."): continue
        dst = os.path.join(TARGET, f)
        if not os.path.exists(dst):
            shutil.copy2(os.path.join(src,f), dst)
            copied += 1
    print(f"sync: {copied} neue Missions nach pending/")

if __name__ == "__main__":
    sync()
