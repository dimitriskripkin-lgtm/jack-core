#!/usr/bin/env python3
import os, subprocess, sys
CFG="/data/data/com.termux/files/home/.ssh/config"
INI="/data/data/com.termux/files/home/jack/config.ini"
KEY="/data/data/com.termux/files/home/.ssh/id_jack"
def sh(cmd,t=10):
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=t)
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 99, "", "TIMEOUT"
def hostname():
    hit=False
    if not os.path.isfile(CFG):
        return None
    for l in open(CFG,encoding="utf-8",errors="ignore"):
        s=l.strip()
        if s.lower().startswith("host ") and "xiaomi" in s.lower():
            hit=True
            continue
        if hit and s.lower().startswith("host "):
            break
        if hit and s.lower().startswith("hostname "):
            return s.split()[1]
    return None
def model_via_alias():
    rc,out,err=sh(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=5","xiaomi-jack","su -c getprop ro.product.model"],t=12)
    m=(out or "").strip().split("\n")[-1].strip()
    ok=("2107113" in m) or ("11T" in m)
    return ok,m,rc,err[:80]
def main():
    cur=hostname()
    print("current",cur)
    ok,m,rc,err=model_via_alias()
    print("alias",ok,m,rc,err)
    if ok:
        print("FOUND",cur)
        return 0
    print("NOT_FOUND")
    return 1
if __name__=="__main__":
    sys.exit(main())
