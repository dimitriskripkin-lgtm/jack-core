#!/usr/bin/env python3
"""jack_secret_scanner.py — Scannt Code vor Git-Push auf Secrets."""
MODULE_VERSION = 1

import os, sys, re, glob
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_secret_scanner")

PATTERNS = [
    (r'AIza[A-Za-z0-9_-]{35}', "Google API Key"),
    (r'sk-[A-Za-z0-9]{48}', "OpenAI Key"),
    (r'ghp_[A-Za-z0-9]{36}', "GitHub Token"),
    (r'ghs_[A-Za-z0-9]{36}', "GitHub Token"),
    (r'[0-9]{9,10}:AA[A-Za-z0-9_-]{33}', "Telegram Bot Token"),
    (r'(?i)password\s*=\s*["\'][^"\']{6,}["\']', "Hardcoded Password"),
    (r'(?i)secret\s*=\s*["\'][^"\']{6,}["\']', "Hardcoded Secret"),
]

SKIP_FILES = ["jack_secret_scanner.py", "jack_audit.py", ".git"]

def scan_file(fpath):
    findings = []
    try:
        content = open(fpath).read()
        for pattern, name in PATTERNS:
            for m in re.finditer(pattern, content):
                line = content[:m.start()].count('\n') + 1
                findings.append({"file": os.path.basename(fpath),
                    "line": line, "type": name, "snippet": m.group()[:20]+"..."})
    except Exception: pass
    return findings

def run():
    all_findings = []
    for fpath in glob.glob(os.path.join(J,"*.py")) + \
                 glob.glob(os.path.join(J,"*.ini")) + \
                 glob.glob(os.path.join(J,"*.json")):
        if any(s in fpath for s in SKIP_FILES): continue
        all_findings.extend(scan_file(fpath))
    if all_findings:
        log.warn(f"Secret Scanner: {len(all_findings)} Findings!")
        for f in all_findings:
            log.warn(f"  {f['type']} in {f['file']} L{f['line']}")
        try:
            import jack_telegram as _jt
            _jt.send(f"🔴 Secret Scanner: {len(all_findings)} mögliche Secrets gefunden!\n" +
                "\n".join(f"  {x['type']} — {x['file']} L{x['line']}" for x in all_findings[:5]))
        except Exception: pass
    else:
        log.info("Secret Scanner: keine Secrets gefunden")
    return len(all_findings)

if __name__ == "__main__":
    n = run()
    print(f"Secret Scanner: {n} Findings")
