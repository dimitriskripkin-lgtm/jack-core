#!/usr/bin/env python3
"""jack_thermal_guard.py — Akku+Temp Check vor schweren Jobs."""
MODULE_VERSION = 1

import os, sys, json, subprocess, time
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_thermal_guard")

MIN_BATTERY = 20
MAX_TEMP    = 45.0

def get_battery():
    try:
        r = subprocess.run(["termux-battery-status"],
            capture_output=True, text=True, timeout=5)
        return json.loads(r.stdout).get("percentage", 100)
    except Exception: return 100

def get_temp():
    try:
        base = "/sys/class/thermal"
        if not os.path.exists(base): return 0.0
        temps = []
        for zone in os.listdir(base):
            t = os.path.join(base, zone, "temp")
            if os.path.exists(t):
                val = int(open(t).read().strip())
                if 20000 < val < 80000:
                    temps.append(val / 1000)
        return max(temps) if temps else 0.0
    except Exception: return 0.0

def check(job_name="job") -> bool:
    bat  = get_battery()
    temp = get_temp()
    if bat < MIN_BATTERY:
        log.warn(f"{job_name} pausiert: Akku {bat}%")
        return False
    if temp > MAX_TEMP:
        log.warn(f"{job_name} pausiert: Temp {temp:.1f}C")
        return False
    log.info(f"{job_name} OK: Akku={bat}% Temp={temp:.1f}C")
    return True

def run():
    return check("waechter")

if __name__ == "__main__":
    ok = check("test")
    print(f"Thermal-Guard: {'OK — Job darf laufen' if ok else 'PAUSE — zu heiss oder leer'}")
    print(f"  Akku: {get_battery()}%  Temp: {get_temp():.1f}C")
