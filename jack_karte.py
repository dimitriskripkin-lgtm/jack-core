#!/usr/bin/env python3
"""JACK Kartierung: Settings-Bildschirme des Xiaomi lesen und ablegen.
Rein lesend: am start oeffnet nur den Bildschirm, setzt keine Werte.
Chunkweise, idempotent, Fokus-Verifikation statt Screenshots raten."""
import os, sys, json, subprocess, time
sys.path.insert(0, os.path.expanduser("~/jack"))
import jack_config
W = os.path.expanduser("~/jack/xiaomi_wissen.json")
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
    try:
        return json.load(open(W))
    except Exception:
        return {}

def lade_karte():
    try:
        return json.load(open(KARTE))
    except Exception:
        return {}

def sichere_karte(d):
    json.dump(d, open(KARTE, "w"), indent=2, ensure_ascii=False)

def activities():
    w = lade_wissen()
    acts = w.get("settings_activities") or w.get("activities") or []
    return acts, w

def component(a):
    a = a.strip()
    if a.startswith("com.android.settings/"):
        return a
    if a.startswith("/"):
        return "com.android.settings" + a
    return "com.android.settings/" + a

def fokus():
    rc, out, _ = sh("dumpsys window windows | grep mCurrentFocus")
    return out

def dump_elemente():
    sh("su -c 'uiautomator dump /sdcard/jack_karte.xml' >/dev/null 2>&1; true")
    rc, out, _ = sh("cat /sdcard/jack_karte.xml")
    if not out.startswith("<"):
        return []
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(out)
    except Exception:
        return []
    els = []
    for n in root.iter("node"):
        t = (n.get("text") or "").strip()
        d = (n.get("content-desc") or "").strip()
        if t or d:
            els.append((t or d)[:60])
    return els[:40]

def chunk(n=10):
    acts, w = activities()
    if not acts:
        return "KEY settings_activities FEHLT. Vorhanden: " + ", ".join(sorted(w.keys()))
    karte = lade_karte()
    gemacht = 0
    for a in acts:
        if gemacht >= n:
            break
        if a in karte:
            continue
        sh("su -c 'am start -n " + component(a) + "'")
        time.sleep(2)
        fok = fokus()
        els = dump_elemente()
        karte[a] = {"fokus": fok[:120], "elemente": els,
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S")}
        gemacht += 1
    sichere_karte(karte)
    sh("su -c 'input keyevent 3'")
    return str(gemacht) + " neue Bildschirme kartiert. Gesamt " + str(len(karte)) + "/" + str(len(acts))

def status():
    acts, w = activities()
    if not acts:
        return "KEY settings_activities FEHLT. Vorhanden: " + ", ".join(sorted(w.keys()))
    karte = lade_karte()
    return "Karte: " + str(len(karte)) + "/" + str(len(acts)) + " Bildschirme"

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "status"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    if a == "chunk":
        print(chunk(n))
    else:
        print(status())
