#!/usr/bin/env python3
"""JACK_TUNE_OLLHYB — Ollama auf dem Honor, nur unter Hitzegrenze."""
MODULE_VERSION = 1
import subprocess, time
LIMIT_C = 42.0
PROZ = None
def temp():
    try:
        import jack_heat_protection as h
        return h.get_temp("honor")
    except Exception:
        return 999.0
while True:
    t = temp()
    if t < LIMIT_C and PROZ is None:
        PROZ = subprocess.Popen(["ollama", "serve"])
    elif t >= LIMIT_C and PROZ is not None:
        PROZ.terminate(); PROZ.wait(timeout=5); PROZ = None
    if PROZ is not None and PROZ.poll() is not None:
        PROZ = None
    time.sleep(15)
