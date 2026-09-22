#!/usr/bin/env python3
"""jack_stand.py — misst den Ist-Zustand, schreibt reports/flugschreiber_stand.json."""
MODULE_VERSION = 1
import os, sys, json, glob, re, subprocess, time
J = os.path.expanduser("~/jack")
def _sh(c, t=10):
    try: return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=t).stdout.strip()
    except Exception: return ""
def git():
    return {"commit": _sh("cd %s && git rev-parse --short HEAD" % J),
            "tag": _sh("cd %s && git describe --tags --abbrev=0" % J),
            "unversioniert": len(_sh("cd %s && git status --porcelain" % J).splitlines())}
def dienste():
    o = {}
    for l in _sh("sv status /data/data/com.termux/files/usr/var/service/*").splitlines():
        if ": /" in l: o[l.split("/")[-1].split(":")[0]] = l.split(":")[0]
    return o
def marken():
    m = {}
    for f in glob.glob(os.path.join(J, "jack_*.py")):
        try: s = open(f, encoding="utf-8", errors="ignore").read()
        except Exception: continue
        for t in set(re.findall(r"JACK_TUNE_[A-Z0-9]+", s)):
            m.setdefault(t, []).append(os.path.basename(f))
    return m
def staged():
    sh = os.path.join(J, "shadow"); r = {"anzahl": 0, "veraltet": []}
    try:
        for f in os.listdir(sh):
            if not f.endswith(".staged"): continue
            r["anzahl"] += 1; z = os.path.join(J, f[:-7])
            if os.path.exists(z) and os.path.getmtime(os.path.join(sh, f)) < os.path.getmtime(z):
                r["veraltet"].append(f[:-7])
    except Exception: pass
    return r
def approvals():
    n = 0
    for p in ("jack_fixes.json", "pending_approvals.json"):
        try: n += len(json.load(open(os.path.join(J, p))))
        except Exception: pass
    return n
def module():
    try:
        d = json.load(open(os.path.join(J, "reports", "module_status.json")))
        return {"aktiv": len(d.get("aktive_module", [])), "waisen": d.get("waisen_count"), "stand": d.get("stand")}
    except Exception: return {}
def bauen():
    return {"gemessen": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "git": git(), "dienste": dienste(),
            "staged": staged(), "offene_approvals": approvals(), "module": module(), "marken": marken()}
if __name__ == "__main__":
    d = bauen()
    json.dump(d, open(os.path.join(J, "reports", "flugschreiber_stand.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: v for k, v in d.items() if k != "marken"}, indent=1, ensure_ascii=False))
    print("Marken gefunden:", len(d["marken"]))
