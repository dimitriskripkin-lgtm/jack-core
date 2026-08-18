#!/usr/bin/env python3
"""JACK Kartierung v2: Settings-Bildschirme mit Fokus-Verifikation.
Rein lesend. am start oeffnet nur, setzt keine Werte.
v2: HOME vor/nach jedem Screen, Fokus-Check ob Ziel wirklich offen,
sonst Eintrag als nicht geoeffnet markiert statt falsche Elemente speichern."""
import os, sys, json, subprocess, time
sys.path.insert(0, os.path.expanduser("~/jack"))
import jack_config
W = os.path.expanduser("~/jack/xiaomi_wissen.json")
DANGER_PATTERNS = ['reset', 'clear', 'wipe', 'format', 'factory',
                     'erase', 'masterclear', 'factoryreset', 'masterreset',
                     'frp', 'oem', 'bootloader', 'developer_option',
                     'backup_reset', 'delete_all', 'erase_all']

def ist_gefaehrlich(activity):
    low = activity.lower()
    for p in DANGER_PATTERNS:
        if p in low:
            return True
    return False

KARTE = os.path.expanduser("~/jack/xiaomi_karte.json")
KEY = os.path.expanduser("~/.ssh/id_jack")

def _ip():
    return jack_config.get_param("NETWORK", "xiaomi_ip")

def sh(cmd, t=15):
    try:
        r = subprocess.run(["ssh", "-i", KEY, "-o", "BatchMode=yes",
            "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
            "-o", "LogLevel=ERROR", "-o", "ConnectTimeout=4", "-p", "8022",
            "root@" + _ip(), cmd], capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 1, "", "SSH-FEHLER: " + str(e)[:100]

def lade_wissen():
    try: return json.load(open(W))
    except Exception: return {}

def lade_karte():
    try: return json.load(open(KARTE))
    except Exception: return {}

def sichere_karte(d):
    json.dump(d, open(KARTE, "w"), indent=2, ensure_ascii=False)

def activities():
    w = lade_wissen()
    acts = w.get("settings_activities") or w.get("activities") or []
    return acts, w

def component(a):
    a = a.strip()
    if a.startswith("com.android.settings/"): return a
    if a.startswith("/"): return "com.android.settings" + a
    return "com.android.settings/" + a

def klasse(a):
    return a.strip().split("/")[-1].split(".")[-1]

def home():
    sh("su -c 'input keyevent 3'")

def fokus():
    rc, out, _ = sh("su -c 'dumpsys window windows' 2>/dev/null | grep mCurrentFocus")
    if not out:
        rc, out, _ = sh("su -c 'dumpsys activity top' 2>/dev/null | grep ACTIVITY | tail -1")
    return out

def dump_elemente():
    sh("su -c 'uiautomator dump /sdcard/jack_karte.xml' >/dev/null 2>&1; true")
    rc, out, _ = sh("cat /sdcard/jack_karte.xml")
    if not out.startswith("<"): return []
    import xml.etree.ElementTree as ET
    try: root = ET.fromstring(out)
    except Exception: return []
    els = []
    for n in root.iter("node"):
        t = (n.get("text") or "").strip()
        d = (n.get("content-desc") or "").strip()
        if t or d: els.append((t or d)[:60])
    return els[:40]

def chunk(n=10):
    acts, w = activities()
    if not acts:
        return "KEY settings_activities FEHLT. Vorhanden: " + ", ".join(sorted(w.keys()))
    karte = lade_karte()
    gemacht = 0
    echt = 0
    for a in acts:
        if gemacht >= n: break
        if a in karte: continue
        if ist_gefaehrlich(a):
            karte[a] = {'fokus': 'GEFAEHRLICH-BLOCKIERT', 'elemente': [],
                        'geoeffnet': False, 'gefaehrlich': True,
                        'ts': time.strftime('%Y-%m-%d %H:%M:%S')}
            gemacht += 1
            continue
        home()
        time.sleep(0.7)
        sh("su -c 'am start -n " + component(a) + "'")
        time.sleep(2)
        fok = fokus()
        geoeffnet = klasse(a) in fok
        els = dump_elemente() if geoeffnet else []
        karte[a] = {"fokus": fok[:120], "elemente": els,
                    "geoeffnet": geoeffnet,
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        gemacht += 1
        if geoeffnet: echt += 1
        home()
    sichere_karte(karte)
    return (str(gemacht) + " kartiert, davon " + str(echt) + " echt geoeffnet. Gesamt "
            + str(len(karte)) + "/" + str(len(acts)))

def status():
    acts, w = activities()
    if not acts:
        return "KEY settings_activities FEHLT. Vorhanden: " + ", ".join(sorted(w.keys()))
    karte = lade_karte()
    echt = sum(1 for v in karte.values() if v.get("geoeffnet"))
    return ("Karte: " + str(len(karte)) + "/" + str(len(acts))
            + " | echt geoeffnet: " + str(echt)
            + " | nicht oeffenbar: " + str(len(karte) - echt) + " | gefaehrlich: " + str(sum(1 for v in karte.values() if v.get("gefaehrlich"))))

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "status"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    if a == "chunk":
        print(chunk(n))
    elif a == "reset":
        if os.path.exists(KARTE):
            os.rename(KARTE, KARTE + ".bak_v1")
            print("Karte zurueckgesetzt (Alt: xiaomi_karte.json.bak_v1)")
        else:
            print("Keine Karte da")
    else:
        print(status())
