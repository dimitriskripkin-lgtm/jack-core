#!/usr/bin/env python3
"""JACK Install Wrapper - sicheres Installieren mit Live-Monitoring.
Zeigt Fortschritt, Temperatur, RAM. Stoppt automatisch bei Ueberhitzung."""
import subprocess, sys, time, os, threading

PREFIX = os.environ.get("PREFIX", "/data/data/com.termux/files/usr")
TEMP_MAX = 43
CHECK_INTERVAL = 10

# ANSI Farben
GRN = "\033[92m"
YLW = "\033[93m"
RED = "\033[91m"
CYN = "\033[96m"
MAG = "\033[95m"
BLD = "\033[1m"
RST = "\033[0m"
CLR = "\033[2J\033[H"

MATRIX_CHARS = "01アイウエオカキクケコJACK▓░▒"

def banner():
    print(CYN + BLD + """
     ██╗ █████╗  ██████╗██╗  ██╗
     ██║██╔══██╗██╔════╝██║ ██╔╝
     ██║███████║██║     █████╔╝
██   ██║██╔══██║██║     ██╔═██╗
╚█████╔╝██║  ██║╚██████╗██║  ██╗
 ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
    """ + RST)
    print(MAG + "  ⚡ JACK Secure Installer v1.0 ⚡" + RST)
    print(CYN + "  " + "─"*36 + RST)

def get_temp():
    try:
        import json
        r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        d = json.loads(r.stdout)
        return float(d.get("temperature", 0)), int(d.get("percentage", 0))
    except Exception:
        return 0.0, 0

def get_ram():
    try:
        m = {}
        for l in open("/proc/meminfo"):
            t = l.split(":")
            if len(t)==2: m[t[0].strip()] = int(t[1].strip().split()[0])//1024
        return m.get("MemAvailable", 0)
    except Exception:
        return 0

def temp_farbe(t):
    if t < 38: return GRN
    if t < 43: return YLW
    return RED

def fortschritt_bar(n, total, breite=30):
    filled = int(breite * n / max(total,1))
    bar = "█" * filled + "░" * (breite - filled)
    pct = int(100 * n / max(total,1))
    return f"[{GRN}{bar}{RST}] {BLD}{pct}%{RST}"

stop_monitor = threading.Event()

def live_monitor(proc):
    start = time.time()
    tick = 0
    spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    while not stop_monitor.is_set():
        if proc.poll() is not None:
            break
        temp, akku = get_temp()
        ram = get_ram()
        elapsed = int(time.time() - start)
        spin = spinner[tick % len(spinner)]
        tc = temp_farbe(temp)
        ram_c = GRN if ram > 1500 else YLW if ram > 800 else RED
        print(f"\r  {CYN}{spin}{RST} {elapsed:3d}s | "
              f"Temp: {tc}{temp:.0f}°C{RST} | "
              f"RAM: {ram_c}{ram}MB{RST} | "
              f"Akku: {akku}%   ", end="", flush=True)
        if temp >= TEMP_MAX:
            print(f"\n\n  {RED}{BLD}⚠️  ÜBERHITZUNG: {temp}°C ≥ {TEMP_MAX}°C — ABBRUCH!{RST}")
            proc.terminate()
            stop_monitor.set()
            return
        tick += 1
        time.sleep(CHECK_INTERVAL)

def installiere(pakete, extra_args=None):
    banner()
    print(f"\n  {BLD}Pakete:{RST} {YLW}{' '.join(pakete)}{RST}")
    temp, akku = get_temp()
    ram = get_ram()
    tc = temp_farbe(temp)
    print(f"  {BLD}Start:{RST}  Temp {tc}{temp}°C{RST} | RAM {ram}MB | Akku {akku}%")
    if temp >= TEMP_MAX:
        print(f"\n  {RED}Zu heiß zum Starten ({temp}°C). Warte auf Abkühlung.{RST}")
        return False
    print(f"\n  {CYN}{'─'*40}{RST}")

    cmd = [sys.executable, "-m", "pip", "install", "--break-system-packages", "-q"] + (extra_args or []) + pakete
    print(f"  {MAG}Befehl:{RST} {' '.join(cmd[3:])}")
    print(f"  {CYN}{'─'*40}{RST}\n")

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    t = threading.Thread(target=live_monitor, args=(proc,), daemon=True)
    t.start()
    ausgabe = []
    for zeile in proc.stdout:
        ausgabe.append(zeile.strip())
    proc.wait()
    stop_monitor.set()
    t.join(timeout=2)
    print()

    temp_end, _ = get_temp()
    tc = temp_farbe(temp_end)
    print(f"\n  {CYN}{'─'*40}{RST}")
    if proc.returncode == 0:
        print(f"  {GRN}{BLD}✅ Installation erfolgreich!{RST}")
    else:
        print(f"  {RED}{BLD}❌ Fehler (Code {proc.returncode}){RST}")
        for z in ausgabe[-5:]:
            if z: print(f"     {RED}{z}{RST}")
    print(f"  Endtemp: {tc}{temp_end}°C{RST}")
    print(f"  {CYN}{'─'*40}{RST}\n")
    return proc.returncode == 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"{YLW}Nutzung: python3 jack_install.py <paket> [paket2...]{RST}")
        print(f"Beispiel: python3 jack_install.py litert-lm")
        sys.exit(1)
    pakete = sys.argv[1:]
    ok = installiere(pakete)
    sys.exit(0 if ok else 1)
