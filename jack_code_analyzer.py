#!/usr/bin/env python3
"""jack_code_analyzer.py — Liest Code, erkennt selbst neue Probleme, schreibt CHECK-Missions."""
MODULE_VERSION = 1

import os, sys, re, json, time, ast

J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
PEND = os.path.join(J, "missions", "pending")
LOG = os.path.join(J, "analyzer.log")

def _log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(LOG, "a") as f: f.write(f"{ts} {msg}\n")

# Muster die der Analyzer selbst erkennt
PATTERNS = [
    {"name":"bare_except","regex":r"    except:\s*$","msg":"bare except gefunden","act":"grep_count","pattern":"    except:","expect_max":0},
    {"name":"hardcoded_path_DISABLED","regex":r'"/data/data/com\.termux/files/home/jack/[^"]+"',"msg":"hardcoded Pfad","act":"grep_count","pattern":"/data/data/com.termux/files/home/jack/","expect_max":0},
    # {"name":"tilde_in_string","regex":r'"~/',"msg":"Tilde in String","act":"grep_count","pattern":'"~/',"expect_max":0}, # deaktiviert FP
    # print_debug: nur Core-Dienste, nicht CLI/Diag/Test-Tools
    # {"name":"print_debug",...} — deaktiviert, zu viele FP auf Nicht-Core-Module
    # hardcoded_ip deaktiviert — IP kommt aus config.ini, kein echter Fehler
    {"name":"todo_fixme","regex":r"#\s*(TODO|FIXME|HACK|XXX)","msg":"TODO/FIXME im Code","act":"grep_count","pattern":"# TODO","expect_max":0},
    {"name":"no_module_version","regex":None,"msg":"MODULE_VERSION fehlt","act":"grep_count","pattern":"MODULE_VERSION","expect_min":1},
]

def analyze_file(fpath):
    """Analysiert eine Datei, gibt Liste von Findings zurück."""
    findings = []
    try:
        content = open(fpath, errors="ignore").read()
        fname = os.path.basename(fpath)
        for p in PATTERNS:
            if p["regex"] is None:
                # Spezialfall: Pattern fehlt
                if p["pattern"] not in content:
                    findings.append({"pattern": p, "file": fpath, "fname": fname})
            else:
                if re.search(p["regex"], content, re.MULTILINE):
                    findings.append({"pattern": p, "file": fpath, "fname": fname})
    except Exception as e:
        _log(f"ERROR {fpath}: {e}")
    return findings

def finding_to_mission(f):
    """Konvertiert ein Finding in eine CHECK-Mission."""
    p = f["pattern"]
    fname = f["fname"]
    mid = f"ana_{p['name']}_{fname.replace('.py','').replace('.','_')}_{int(time.time())}"
    m = {
        "id": mid,
        "typ": "check",
        "act": p["act"],
        "file": f"~/jack/{fname}",
        "pattern": p["pattern"],
        "cat": f"analyzer_{p['name']}"
    }
    if "expect_max" in p: m["expect_max"] = p["expect_max"]; m["expect"] = "PASS"
    if "expect_min" in p: m["expect_min"] = p["expect_min"]; m["expect"] = "PASS"
    return m

def run():
    _log("=== ANALYZER START ===")
    all_py = [os.path.join(J, f) for f in os.listdir(J)
              if f.endswith(".py") and not f.endswith(".bak")]

    all_findings = []
    for fpath in sorted(all_py):
        findings = analyze_file(fpath)
        all_findings.extend(findings)

    _log(f"{len(all_findings)} Findings in {len(all_py)} Dateien")

    # Neue Missions schreiben — nur wenn noch nicht in pending/done
    written = 0
    DONE = os.path.join(J, "missions", "done")
    for f in all_findings:
        m = finding_to_mission(f)
        # Prüfen ob ähnliche Mission schon existiert
        already = any(
            m["pattern"] in open(os.path.join(PEND, x), errors="ignore").read()
            and m["file"] in open(os.path.join(PEND, x), errors="ignore").read()
            for x in os.listdir(PEND) if x.endswith(".json")
        ) if os.path.exists(PEND) else False
        # Auch done/fail/archive prüfen — kein Re-Fire
        if not already:
            for sub in ["done","fail","archive"]:
                sp=os.path.join(J,"missions",sub)
                if os.path.exists(sp):
                    if any(x.startswith(m["id"]) for x in os.listdir(sp)):
                        already=True; break
        if not already:
            path = os.path.join(PEND, f"{m['id']}.json")
            open(path,"w").write(json.dumps(m))
            _log(f"NEU: {m['id']} — {f['pattern']['msg']} in {f['fname']}")
            written += 1

    _log(f"=== ANALYZER ENDE: {written} neue Missions ===")
    return written

if __name__ == "__main__":
    n = run()
    print(f"Analyzer: {n} neue Missions generiert")
    sys.exit(0)