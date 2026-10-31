#!/data/data/com.termux/files/usr/bin/python3
"""JACK_TUNE_SVNEUSTART (31.10.2026, Kap 312): runit-Dienst sicher neu starten.

Problem 31.10.: cloudflared und jack_mcp beendeten sich nach TERM nicht innerhalb von sv's 7 s
(cloudflared Grace-Period 30 s), "sv restart" meldete timeout, der alte Prozess lief weiter.
Ablauf: alte PID merken -> sv -w WARTE restart -> laeuft noch die alte PID: sv kill + kill -9 genau
dieser PID -> sv up -> warten bis "run" mit NEUER PID. Erfolg nur mit neuer PID (Beleg), sonst ok=False.
Fasst nur den genannten Dienst an. jack_missions/jack_mcp nur mit erlaubt_kern=True (Regel: Dima startet die).
CLI: python3 jack_svneustart.py <dienst> [--kern]
"""
import os
import re
import signal
import subprocess
import sys
import time

KERN = {"jack_missions", "jack_mcp"}
_NAME = re.compile(r"[A-Za-z0-9_.-]{1,64}\Z")


def _status(dienst):
    try:
        r = subprocess.run(["sv", "status", dienst], capture_output=True, text=True, timeout=10)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return "fehler " + type(e).__name__


def _pid(text):
    m = re.match(r"\s*run:\s*\S+:\s*\(pid (\d+)\)", text or "")
    return int(m.group(1)) if m else None


def neustart(dienst, warte_s=45, erlaubt_kern=False, kill_fn=os.kill, sleep_fn=time.sleep,
             status_fn=_status, run_fn=subprocess.run):
    """-> dict(ok, dienst, alt, neu, weg, info). ok nur bei neuer laufender PID."""
    if not _NAME.fullmatch(str(dienst or "")):
        return {"ok": False, "dienst": dienst, "info": "ungueltiger Dienstname"}
    if dienst in KERN and not erlaubt_kern:
        return {"ok": False, "dienst": dienst, "info": "Kerndienst: Neustart nur durch Dima"}
    alt = _pid(status_fn(dienst))
    weg = "sv"
    try:
        run_fn(["sv", "-w", str(int(warte_s)), "restart", dienst], capture_output=True, text=True,
               timeout=int(warte_s) + 15)
    except Exception:
        pass
    neu = _pid(status_fn(dienst))
    if alt and neu == alt:
        weg = "kill"
        try:
            run_fn(["sv", "kill", dienst], capture_output=True, text=True, timeout=10)
        except Exception:
            pass
        sleep_fn(2)
        try:
            kill_fn(alt, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass
        sleep_fn(2)
        try:
            run_fn(["sv", "up", dienst], capture_output=True, text=True, timeout=10)
        except Exception:
            pass
    for _ in range(10):
        sleep_fn(1)
        neu = _pid(status_fn(dienst))
        if neu and neu != alt:
            return {"ok": True, "dienst": dienst, "alt": alt, "neu": neu, "weg": weg,
                    "info": "laeuft mit neuer PID"}
    return {"ok": False, "dienst": dienst, "alt": alt, "neu": neu, "weg": weg,
            "info": "keine neue laufende PID nachgewiesen"}


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--kern"]
    if len(args) != 1:
        raise SystemExit("Aufruf: jack_svneustart.py <dienst> [--kern]")
    r = neustart(args[0], erlaubt_kern="--kern" in sys.argv)
    print(r)
    sys.exit(0 if r["ok"] else 1)
