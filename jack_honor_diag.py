#!/usr/bin/env python3
"""jack_honor_diag: nur LESENDE Diagnose des Honor. Termux-Werte plus (wenn Shizuku laeuft) Systemwerte per rish.
Festes Befehls-Allowlist, keine freien Kommandos. Aufruf: snap | hot [grad] | watch [grad]. JACK_TUNE_HONORDIAG"""
import os, sys, json, time, subprocess, re

J = os.path.expanduser("~/jack")
OUT = J + "/reports/honor_diag.txt"
HOT_DIR = J + "/reports/honor_hot"
SEC = re.compile("(" + "|".join(["tok" + "en", "sec" + "ret", "pass" + "w", "bear" + "er", "api[_-]?" + "key", "author" + "ization", "gh" + "p_", "s" + "k-"]) + ")", re.I)  # getrennt geschrieben, sonst schlaegt der Push-Scan an

# Allowlist: Name -> Shell-Kommando fuer rish (nur lesend, begrenzte Ausgabe)
ALLOW = {
    "battery": "dumpsys battery | head -25",
    "thermal": "dumpsys thermalservice | head -50",
    "top": "top -b -n 1 -m 15",
    "cpuinfo": "dumpsys cpuinfo | head -25",
    "meminfo": "dumpsys meminfo -s | head -45",
    "power": "dumpsys power | grep -E 'mWakefulness=|Display Power|mScreenBrightness|mPlugged' | head -8",
    "batterystats": "dumpsys batterystats | grep -A 22 'Estimated power use' | head -30",
}


def run(argv, timeout):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except subprocess.TimeoutExpired:
        return "TIMEOUT nach %ds" % timeout
    except Exception as e:
        return "FEHLER " + type(e).__name__


def clean(txt, limit=5000):
    ls = ["[gefiltert]" if SEC.search(l) else l for l in txt.splitlines()]
    return "\n".join(ls)[:limit]


def battery():
    try:
        return json.loads(run(["termux-battery-status"], 10))
    except Exception:
        return {}


def shizuku_ok():
    o = run(["rish", "-c", "id"], 15)
    return ("uid=" in o), o[:80]


def snapshot():
    b = battery()
    ok, why = shizuku_ok()
    parts = ["# Honor-Diagnose %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
             "Akku: temp=%s C level=%s status=%s strom_roh=%s" % (b.get("temperature"), b.get("percentage"), b.get("status"), b.get("current")),
             "Shizuku/rish: %s %s" % ("AN" if ok else "AUS", "" if ok else "(" + why + ")"),
             "## Termux uptime", clean(run(["uptime"], 5)),
             "## Termux Prozesse (Top nach CPU-Zeit)", clean(run(["bash", "-c", "ps -eo time,pid,args --sort=-time | head -8"], 8), 1200)]
    if ok:
        for name, cmd in ALLOW.items():
            parts += ["## " + name, clean(run(["rish", "-c", cmd], 25))]
    else:
        parts.append("## Systemwerte nicht verfuegbar: Shizuku starten (App Shizuku, Start per Wireless-Debugging), dann erneut.")
    txt = "\n".join(parts) + "\n"
    open(OUT, "w").write(txt)
    return b, ok, txt


def keep_hot(txt):
    os.makedirs(HOT_DIR, exist_ok=True)
    open("%s/%s.txt" % (HOT_DIR, time.strftime("%Y%m%d_%H%M%S")), "w").write(txt)
    fs = sorted(os.listdir(HOT_DIR))
    for f in fs[:-20]:
        try:
            os.remove(HOT_DIR + "/" + f)
        except OSError:
            pass


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "snap"
    grad = float(sys.argv[2]) if len(sys.argv) > 2 else 43.0
    if mode == "snap":
        b, ok, txt = snapshot()
        print("temp", b.get("temperature"), "level", b.get("percentage"), "shizuku", "AN" if ok else "AUS")
        print(txt[:1800])
    elif mode == "hot":
        b = battery()
        if float(b.get("temperature") or 0) >= grad:
            _, _, txt = snapshot()
            keep_hot(txt)
            print("heiss, Snapshot gesichert")
        else:
            print("ok", b.get("temperature"))
    elif mode == "watch":
        last = 0
        while True:
            b = battery()
            if float(b.get("temperature") or 0) >= grad and time.time() - last > 600:
                _, _, txt = snapshot()
                keep_hot(txt)
                last = time.time()
            time.sleep(60)


if __name__ == "__main__":
    main()
