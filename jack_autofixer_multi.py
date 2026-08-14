#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import py_compile

SHADOW_DIR = os.path.expanduser("~/.prefix/tmp/shadow_workspace")

def prepare_multi_file_sandbox(files_to_patch):
    os.makedirs(SHADOW_DIR, exist_ok=True)
    copied_files = []
    for fpath in files_to_patch:
        if os.path.exists(fpath):
            dest = os.path.join(SHADOW_DIR, os.path.basename(fpath))
            shutil.copy2(fpath, dest)
            copied_files.append(dest)
    return copied_files

def verify_shadow_workspace():
    if not os.path.exists(SHADOW_DIR):
        return False
    for root, dirs, files in os.walk(SHADOW_DIR):
        for f in files:
            if f.endswith(".py"):
                full_p = os.path.join(root, f)
                try:
                    py_compile.compile(full_p, doraise=True)
                except Exception as e:
                    print(f"[ERR] Multi-file shadow compile failed on {f}: {e}")
                    return False
    print("[OK] Multi-file shadow workspace verifiziert.")
    return True

if __name__ == "__main__":
    print("[OK] jack_autofixer_multi Modul bereit.")
