#!/usr/bin/env python3
"""JACK Audit - Gesundheits- und Sicherheits-Check. Kern-Modul (nicht gegated)."""
import os, re, socket, subprocess, sqlite3, shutil
from datetime import datetime

H = os.path.expanduser("~/jack")
XIP, XPORT = "10.234.166.131", 8022

def dienste():
    r = subprocess.run("sv status jack_cortex jack_telegram jack_autolearn jack_publisher jack_waechter ollama", shell=True, capture_output=True, text=True)
    ls = [l for l in r.stdout.strip().split("\n") if l]
    run = sum(1 for l in ls if l.startswith("run:"))
    print("Dienste:        %d/6 laufen%s" % (run, "" if run==6 else "  <-- PRUEFEN!"))
    for l in ls:
        if not l.startswith("run:"): print("   PROBLEM:", l)

def speicher():
    try:
        t,u,f = shutil.disk_usage(H)
        print("Speicher:       %.1fG benutzt / %.1fG (%.1fG frei)" % (u/1e9, t/1e9, f/1e9))
    except Exception as e:
        print("Speicher:       ERR", e)

def fehler():
    try:
        con = sqlite3.connect(H + "/jack_errors.db")
        n = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
        con.close()
        print("Offene Fehler:  %d" % n)
    except Exception as e:
        print("Offene Fehler:  ERR", e)

def xiaomi():
    s = socket.socket(); s.settimeout(3)
    try:
        s.connect((XIP, XPORT)); s.close()
        print("Xiaomi:         erreichbar (SSH-Port offen)")
    except Exception:
        print("Xiaomi:         abwesend (kein Fehler - Slave nicht im Hotspot)")

def secrets():
    p = os.path.expanduser("~/.jack_secrets")
    if not os.path.exists(p):
        print("Secrets:        FEHLT (~/.jack_secrets nicht da)"); return
    mode = oct(os.stat(p).st_mode)[-3:]
    print("Secrets:        chmod %s %s" % (mode, "OK" if mode in ("600","400") else "ZU OFFEN - chmod 600!"))

def scrubber():
    BAD = re.compile(r"(AQ\.[A-Za-z0-9_-]{10}|sk_[a-zA-Z0-9]{10}|AIza[A-Za-z0-9_-]{10}|gh[ps]_[A-Za-z0-9]{10}|[0-9]{9,10}:AA[A-Za-z0-9_-]{10})")
    ctx = os.path.expanduser("~/jack-context/context.md")
    if not os.path.exists(ctx):
        print("Scrubber:       context.md nicht da"); return
    hits = sum(1 for l in open(ctx, encoding="utf-8", errors="ignore") if BAD.search(l))
    print("Scrubber:       %s" % ("SAUBER (keine Keys im Public-Repo)" if hits==0 else "ALARM! %d moegliche Keys durchgerutscht" % hits))

def gate():
    try:
        has = "def assess_skill_risk" in open(H + "/jack_skills.py").read()
        print("Skill-Gate:     %s" % ("AKTIV" if has else "FEHLT - SICHERHEITSWAND WEG!"))
    except Exception as e:
        print("Skill-Gate:     ERR", e)

if __name__ == "__main__":
    print("=" * 44)
    print(" JACK AUDIT  " + datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 44)
    print("-- Gesundheit --")
    dienste(); speicher(); fehler(); xiaomi()
    print("-- Sicherheit --")
    secrets(); scrubber(); gate()
    print("=" * 44)
