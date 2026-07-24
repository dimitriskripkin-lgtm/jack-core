#!/usr/bin/env python3
"""JACK Audit - Gesundheits- und Sicherheits-Check. Kern-Modul (nicht gegated)."""
import os, re, socket, subprocess, sqlite3, shutil
from datetime import datetime

H = os.path.expanduser("~/jack")
XIP, XPORT = "10.58.220.131", 8022

def _dienste():
    r = subprocess.run("sv status jack_cortex jack_telegram jack_waechter ollama", shell=True, capture_output=True, text=True)
    ls = [l for l in r.stdout.strip().split("\n") if l]
    run = sum(1 for l in ls if l.startswith("run:"))
    out = ["Dienste:        %d/4 laufen%s" % (run, "" if run==7 else "  <-- PRUEFEN!")]
    for l in ls:
        if not l.startswith("run:"): out.append("   PROBLEM: " + l)
    return "\n".join(out)

def _speicher():
    try:
        t,u,f = shutil.disk_usage(H)
        return "Speicher:       %.1fG benutzt / %.1fG (%.1fG frei)" % (u/1e9, t/1e9, f/1e9)
    except Exception as e:
        return "Speicher:       ERR %s" % e

def _fehler():
    try:
        con = sqlite3.connect(H + "/jack_errors.db")
        n = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
        con.close()
        return "Offene Fehler:  %d" % n
    except Exception as e:
        return "Offene Fehler:  ERR %s" % e

def _xiaomi():
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect((XIP, XPORT)); s.close()
        return "Xiaomi:         erreichbar (SSH-Port offen)"
    except Exception:
        return "Xiaomi:         abwesend (kein Fehler - Slave nicht im Hotspot)"

def _secrets():
    p = os.path.expanduser("~/.jack_secrets")
    if not os.path.exists(p):
        return "Secrets:        FEHLT (~/.jack_secrets nicht da)"
    mode = oct(os.stat(p).st_mode)[-3:]
    return "Secrets:        chmod %s %s" % (mode, "OK" if mode in ("600","400") else "ZU OFFEN - chmod 600!")

def _scrubber():
    BAD = re.compile(r"(AQ\.[A-Za-z0-9_-]{10}|sk_[a-zA-Z0-9]{10}|AIza[A-Za-z0-9_-]{10}|gh[ps]_[A-Za-z0-9]{10}|[0-9]{9,10}:AA[A-Za-z0-9_-]{10})")
    ctx = os.path.expanduser("~/jack-context/context.md")
    if not os.path.exists(ctx):
        return "Scrubber:       context.md nicht da"
    hits = sum(1 for l in open(ctx, encoding="utf-8", errors="ignore") if BAD.search(l))
    return "Scrubber:       %s" % ("SAUBER (keine Keys im Public-Repo)" if hits==0 else "ALARM! %d moegliche Keys durchgerutscht" % hits)

def _gate():
    try:
        has = "def assess_skill_risk" in open(H + "/jack_skills.py").read()
        return "Skill-Gate:     %s" % ("AKTIV" if has else "FEHLT - SICHERHEITSWAND WEG!")
    except Exception as e:
        return "Skill-Gate:     ERR %s" % e

def report():
    L = ["JACK AUDIT  " + datetime.now().strftime("%Y-%m-%d %H:%M"), "-- Gesundheit --",
         _dienste(), _speicher(), _fehler(), _xiaomi(), "-- Sicherheit --",
         _secrets(), _scrubber(), _gate()]
    return "\n".join(L)

if __name__ == "__main__":
    print("=" * 44); print(report()); print("=" * 44)
