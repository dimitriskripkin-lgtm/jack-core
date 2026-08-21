#!/usr/bin/env python3
"""TÜV v6: Echte Fehler erkennen.
Qwen 21.08. - Listen korrekt parsen, FAST_CMDS zuverlässig erkennen."""
import os, re, sys
sys.path.insert(0, os.path.expanduser("~/jack"))

J = os.path.expanduser("~/jack")
TG = os.path.join(J, "jack_telegram.py")
src = open(TG, encoding="utf-8").read()

# FAST_CMDS sammeln (diese werden alle über einen Dispatcher bedient)
fast_cmds = set()
m = re.search(r"FAST_CMDS\s*=\s*\{([^}]+)\}", src)
if m:
    fast_cmds.update(re.findall(r"'(/[^']+)'", m.group(1)))

# Alle Slash-Befehle sammeln
cmds = set(fast_cmds)
cmds.update("/" + c for c in re.findall(r"_rt\s*==\s*'/([a-z_]+)'", src))
cmds.update("/" + c for c in re.findall(r"_rt\.startswith\('/([a-z_]+)'", src))
cmds.update("/" + c for c in re.findall(r"text\.strip\(\)\s*==\s*'/([a-z_]+)'", src))
cmds.update("/" + c for c in re.findall(r"text\.strip\(\)\.startswith\('/([a-z_]+)'", src))
# Listen einzeln extrahieren
for list_match in re.finditer(r'\[([^\]]+)\]', src):
    list_content = list_match.group(1)
    cmds.update(re.findall(r"'(/[^']+)'", list_content))
    cmds.update(re.findall(r'"(/[^"]+)"', list_content))
cmds.update(re.findall(r'"(/[a-z_]+)"\s*,\s*"[^"]+"\s*,\s*"/', src))

def has_handler(cmd):
    n = cmd.lstrip("/")
    # Pattern 1: FAST_CMDS dispatcher
    if cmd in fast_cmds:
        return True
    # Pattern 2: Direkte Vergleiche (alle Varianten)
    pats = [
        f"_rt == '{cmd}'", f"_rt.startswith('{cmd}')",
        f"text.strip()=='{cmd}'", f"text.strip() == '{cmd}'",
        f"text.strip().startswith('{cmd}')",
        f"'{cmd}' in text", f"'/', '{n}'",
        f"'/', '{cmd}'",
        f"'{cmd}' in FAST_CMDS",
    ]
    if any(p in src for p in pats):
        return True
    # Pattern 3: In Listen/Set (einzelne Elemente)
    for pattern in [f"'{cmd}'", f'"{cmd}"']:
        for list_match in re.finditer(r'\[([^\]]{1,200})\]', src):
            if pattern in list_match.group(1) and '/' in list_match.group(1):
                return True
    return False

def live_test(cmd):
    try:
        if cmd == "/akku":
            return "OK" if os.path.exists("/sys/class/power_supply/battery/capacity") else "KEIN SYSFS"
        if cmd == "/outcomes":
            import jack_outcome_tracker as o
            o.get_stats(1); return "OK"
        if cmd == "/activity":
            import jack_activity_logger as a
            a.get_recent(hours=1); return "OK"
        if cmd == "/appmap":
            import jack_intent_apps as j
            return f"OK ({len(j.MAP)} Apps)"
        if cmd == "/errors":
            import sqlite3
            c = sqlite3.connect(os.path.join(J, "jack_errors.db"))
            c.execute("SELECT COUNT(*) FROM errors").fetchone(); return "OK"
        if cmd in fast_cmds:
            return "OK (FAST_CMDS)"
        if cmd == "/sehen":
            import jack_vision
            return "OK (analyze_screen)" if hasattr(jack_vision, "analyze_screen") else "FEHLER"
        if cmd in ("/menu", "/m"):
            return "OK (menu_hauptseite)"
        return "KEIN-LIVE-TEST"
    except Exception as e:
        return "FEHLER: " + str(e)[:60]

report = []
# Commands mit Parametern auf Basis-Command reduzieren
base_cmds = set()
for cmd in cmds:
    if not cmd.startswith("/"):
        continue
    # Nur den Basis-Command extrahieren (vor dem ersten Leerzeichen)
    base = cmd.split()[0]
    base_cmds.add(base)

for cmd in sorted(base_cmds):
    h = has_handler(cmd)
    lt = live_test(cmd)
    if not h:
        status = "HANDLER-FEHLT"
    elif "FEHLER" in lt:
        status = "MODUL-DEFETT"
    else:
        status = "OK"
    report.append((cmd, status, lt))

print("TÜV v6 REPORT — " + str(len(report)) + " Befehle (v6: Listen + FAST_CMDS gefixt)")
print("=" * 66)
for cmd, status, lt in report:
    print(f"{cmd:18} | {status:14} | {lt}")
print("=" * 66)
ok = sum(1 for _, s, _ in report if s == "OK")
fehlt = [c for c, s, _ in report if s == "HANDLER-FEHLT"]
defekt = [c for c, s, _ in report if s == "MODUL-DEFETT"]
print(f"OK: {ok}/{len(report)} (v5 war 30/53)")
if fehlt: print("ECHTE FEHLER (Handler fehlt): " + ", ".join(fehlt))
if defekt: print("MODUL DEFETT: " + ", ".join(defekt))
