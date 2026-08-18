#!/usr/bin/env python3
"""JACK Navi: 3-Schichten-Navigationsloop fuer Xiaomi-UI.
Schicht 1 (Fahrer): harte Logik - Fokus, XML, TABU-Keywords pro Element.
Schicht 2 (Beifahrer): Vision NUR bei Elementen ohne Text, fail-closed, nur mit --vision.
Schicht 3 (Verifikation): Fokus+Diff nach jedem Tap, unerwartet -> BACK (nur live).
Dry-Modus (Standard): entscheidet und loggt, tippt NICHT.
Live-Modus: erst nach Dimas Go nach Dry-Review."""
import os, sys, json, subprocess, time, re
sys.path.insert(0, os.path.expanduser("~/jack"))
import jack_config

KEY = os.path.expanduser("~/.ssh/id_jack")
TRACE = os.path.expanduser("~/jack/navi_trace.jsonl")

TABU_UI = [
    'reset', 'wipe', 'factory', 'loeschen', 'löschen', 'delete', 'erase',
    'formatieren', 'passwort', 'password', 'pin eingeben', 'puk',
    'notruf', 'notfall', 'sos', 'emergency', 'werkseinstellung',
    'zahlung', 'payment', 'kaufen', 'buy', 'kreditkarte', 'paypal',
    'sperrmuster', 'fingerabdruck', 'fingerprint', 'biometrie', 'biometric',
    'gesichtsentsperrung', 'face unlock', 'sim-karten', 'sim card',
    'entwickleroptionen', 'developer', 'oem', 'bootloader',
    'konten', 'account', 'abmelden', 'sign out', 'vpn',
]

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

def fokus():
    rc, out, _ = sh("su -c 'dumpsys activity top' 2>/dev/null | grep ACTIVITY | tail -1")
    if not out:
        rc, out, _ = sh("dumpsys window 2>/dev/null | grep mCurrentFocus")
    return out

def dump_elemente():
    sh("su -c 'uiautomator dump /sdcard/jack_navi.xml' >/dev/null 2>&1; true")
    rc, out, _ = sh("cat /sdcard/jack_navi.xml")
    if not out.startswith("<"):
        return []
    import xml.etree.ElementTree as ET
    try:
        root = ET.fromstring(out)
    except Exception:
        return []
    els = []
    for n in root.iter("node"):
        els.append({
            "text": (n.get("text") or "").strip(),
            "desc": (n.get("content-desc") or "").strip(),
            "rid": (n.get("resource-id") or "").strip(),
            "clickable": n.get("clickable") == "true",
            "bounds": n.get("bounds", ""),
        })
    return els

def mitte(bounds):
    m = re.findall(r"-?[0-9]+", bounds or "")
    if len(m) != 4:
        return None
    x1, y1, x2, y2 = map(int, m)
    return (x1 + x2) // 2, (y1 + y2) // 2

def tabu_grund(el):
    hay = (el["text"] + " " + el["desc"] + " " + el["rid"]).lower()
    for t in TABU_UI:
        if t in hay:
            return t
    return None

def vision_check(el):
    try:
        import jack_vision
        frage = ("Auf dem Xiaomi ist ein Element ohne Text sichtbar. "
                 "Resource-ID: " + (el["rid"] or "keine") + ". "
                 "Ist das eine zerstoerende oder sicherheitsrelevante Aktion "
                 "(loeschen, zuruecksetzen, Passwort, Zahlung, Berechtigung)? "
                 "Antworte NUR: ja / nein / unklar")
        ant = (jack_vision.vision_ask(frage) or "").lower()
        if "unklar" in ant:
            return "blockiert_vision_unklar"
        if "ja" in ant:
            return "blockiert_vision_ja"
        if "nein" in ant:
            return None
        return "blockiert_vision_unklar"
    except Exception:
        return "blockiert_vision_fehler"

def log_trace(entry):
    entry["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(TRACE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + chr(10))

def entscheide(max_els=12, use_vision=False):
    fok = fokus()
    els = dump_elemente()
    if not els:
        return "Kein UI-Dump moeglich. Fokus: " + fok[:80]
    kand = [e for e in els if (e["text"] or e["desc"]) and len(e["text"] or e["desc"]) >= 2]
    z = ["Fokus: " + fok[:80],
         "Elemente gesamt: " + str(len(els)) + " | klickbar mit Inhalt: " + str(len(kand))]
    for el in kand[:max_els]:
        label = el["text"] or el["desc"] or el["rid"]
        grund = tabu_grund(el)
        if grund:
            log_trace({"fokus": fok[:60], "element": label[:40], "entscheidung": "BLOCK", "grund": "tabu_" + grund})
            z.append("  BLOCK  " + label[:35] + "  (TABU: " + grund + ")")
            continue
        if not el["text"] and not el["desc"]:
            if use_vision:
                v = vision_check(el)
                if v:
                    log_trace({"fokus": fok[:60], "element": el["rid"][:40], "entscheidung": "BLOCK", "grund": v})
                    z.append("  BLOCK  " + el["rid"][:35] + "  (Vision: " + v + ")")
                else:
                    log_trace({"fokus": fok[:60], "element": el["rid"][:40], "entscheidung": "WUERDE_TAPPEN", "grund": "vision_nein"})
                    z.append("  TAP?   " + el["rid"][:35] + "  (Vision sagt nein)")
            else:
                log_trace({"fokus": fok[:60], "element": el["rid"][:40], "entscheidung": "BLOCK", "grund": "unklares_icon_vision_aus"})
                z.append("  BLOCK  " + el["rid"][:35] + "  (Icon ohne Text, Vision aus)")
            continue
        log_trace({"fokus": fok[:60], "element": label[:40], "entscheidung": "WUERDE_TAPPEN", "grund": "text_ok"})
        z.append("  TAP?   " + label[:35])
    return chr(10).join(z)


def zustand():
    """Fokus plus XML-Signatur (Texte, Desc, checked) - merkt auch Dialoge und Toggles."""
    import hashlib, xml.etree.ElementTree as ET
    rc, out, _ = sh("su -c 'uiautomator dump /sdcard/jack_navi_z.xml' >/dev/null 2>&1; cat /sdcard/jack_navi_z.xml")
    sig = "leer"
    if out.startswith("<"):
        try:
            root = ET.fromstring(out)
            parts = []
            for n in root.iter("node"):
                t = (n.get("text") or "").strip()
                d = (n.get("content-desc") or "").strip()
                c = n.get("checked", "false")
                if t or d:
                    parts.append(t + "|" + d + "|" + c)
            sig = hashlib.md5(chr(10).join(sorted(parts)).encode()).hexdigest()[:12]
        except Exception:
            sig = "fehler"
    return fokus() + "#" + sig

LIVE_SKIP = ['qr', 'scan', 'teilen', 'share', 'zurueck', 'zurück', 'back',
             'loeschen', 'löschen', 'delete', 'reset', 'passwort', 'password',
             'senden', 'kamera', 'camera', 'factory', 'wipe']

def _tap(x, y):
    sh("su -c 'input tap " + str(x) + " " + str(y) + "'")

FOKUS_TABU = ['password', 'passwort', 'reset', 'delete', 'loeschen', 'factory',
              'wipe', 'security', 'perm', 'privacy', 'lock', 'keyguard',
              'biometric', 'finger', 'face_unlock', 'account', 'konto', 'sim']

NON_ACTION = ['keine ergebnisse', 'nicht gefunden', 'keine daten',
              'nicht verfuegbar', 'loading', 'laedt']

def live(max_taps=2):
    """Live-Modus: max_taps Taps mit Verifikation. NOTFALL-BACK bei TABU-Screen."""
    import time as _t
    bericht = []
    before_z = zustand()
    els = dump_elemente()
    getappt = 0
    for el in els:
        if getappt >= max_taps:
            break
        label = el["text"] or el["desc"]
        if not label or len(label) < 3:
            continue
        if not el["clickable"]:
            continue
        low = label.lower()
        if tabu_grund(el):
            continue
        if any(s in low for s in LIVE_SKIP):
            continue
        if any(s in low for s in NON_ACTION):
            continue
        pos = mitte(el["bounds"])
        if not pos:
            continue
        _tap(pos[0], pos[1])
        getappt += 1
        _t.sleep(1.5)
        after_z = zustand()
        after_fok = after_z.split('#')[0]
        tabu_im_fokus = any(t in after_fok.lower() for t in FOKUS_TABU)
        if tabu_im_fokus:
            sh("su -c 'input keyevent 4'")
            _t.sleep(0.8)
            sh("su -c 'input keyevent 3'")
            log_trace({"fokus": after_fok[:60], "element": label[:40], "entscheidung": "NOTFALL-BACK", "grund": "tabu_screen_nach_tap"})
            bericht.append("NOTFALL-BACK nach Tap auf " + label[:30])
            break
        veraendert = (after_z != before_z)
        log_trace({"fokus": after_fok[:60], "element": label[:40], "entscheidung": "LIVE-TAP", "grund": "veraendert" if veraendert else "unveraendert", "live": True})
        bericht.append("TAP " + label[:30] + " -> " + ("neuer Screen: " + after_fok[:50] if veraendert else "keine Reaktion"))
        before_fok = after_fok
    sh("su -c 'input keyevent 3'")
    return chr(10).join(bericht) if bericht else "Keine sicheren Tap-Kandidaten gefunden."


if __name__ == "__main__":
    uv = "--vision" in sys.argv
    print(entscheide(use_vision=uv))
