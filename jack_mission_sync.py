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
ALLOWED_ACTS = {
    "grep_count", "line_count", "file_exists",
    "line_check", "mtime_fresh", "no_secret", "notiz"
}
BLOCKED_LOG = os.path.expanduser("~/jack/missions/blocked_sync.log")

def _sanitize(path):
    """Prüft Mission-JSON vor Übernahme. False = blockiert."""
    try:
        d = json.load(open(path))
        act = d.get("act", "")
        if act not in ALLOWED_ACTS:
            return False, f"act nicht erlaubt: {act}"
        f_val = d.get("file", "")
        for danger in ["../", ".ssh", "jack_secrets", "/proc", "authorized_keys"]:
            if danger in str(f_val):
                return False, f"Pfad-Tabu: {danger}"
        return True, "ok"
    except Exception as e:
        return False, f"Parse-Fehler: {e}"

    for f in os.listdir(src):
        if not f.endswith(".json") or f.startswith("."): continue
        src_path = os.path.join(src, f)
        dst = os.path.join(TARGET, f)
        if not os.path.exists(dst):
            ok, grund = _sanitize(src_path)
            if not ok:
                with open(BLOCKED_LOG, "a") as bl:
                    bl.write(f"{f}: {grund}\n")
                print(f"BLOCKIERT: {f} -> {grund}")
                continue
            shutil.copy2(src_path, dst)
            copied += 1
    print(f"sync: {copied} neue Missions nach pending/")

if __name__ == "__main__":
    sync()
