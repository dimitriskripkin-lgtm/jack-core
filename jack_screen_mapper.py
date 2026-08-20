#!/usr/bin/env python3
"""
Screen-State-Mapping Phase 1: UI-Dump Parser
Extrahiert UI-Elemente vom Xiaomi und speichert Screen-Signaturen.
"""
import sqlite3, subprocess, xml.etree.ElementTree as ET, hashlib, os, time

DB_FILE = os.path.expanduser("~/jack/jack_screen_states.db")
XIAOMI_HOST = "10.58.220.131"
XIAOMI_PORT = "8022"
XIAOMI_KEY = os.path.expanduser("~/.ssh/id_jack")

def ssh_cmd(args, timeout=10):
    cmd = [
        "ssh", "-i", XIAOMI_KEY, "-p", XIAOMI_PORT,
        "-o", "ConnectTimeout=3",
        "-o", "StrictHostKeyChecking=no",
        f"root@{XIAOMI_HOST}"
    ] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout, r.stderr
    except Exception as e:
        return -1, "", str(e)

def get_foreground():
    import re
    probes = [
        "dumpsys activity activities | grep -i resumed | head -5",
        "dumpsys window | grep -i mCurrentFocus | head -2",
        "dumpsys activity top | grep -i ACTIVITY | head -3",
    ]
    for p in probes:
        rc, out, err = ssh_cmd(["su -c '" + p + "'"], timeout=15)
        if rc == 0 and out.strip():
            m = re.search(r"([a-zA-Z0-9._]+)/([a-zA-Z0-9._$]+)", out)
            if m:
                return m.group(1), m.group(2)
    return None, None
def ensure_unlocked():
    import time
    rc, out, err = ssh_cmd(["su -c 'dumpsys window | grep -i mCurrentFocus | head -2'"], timeout=10)
    low = out.lower()
    if "aod" in low or "keyguard" in low or not out.strip():
        ssh_cmd(["su", "-c", "input keyevent 224"], timeout=8)
        time.sleep(1)
        ssh_cmd(["su", "-c", "input swipe 540 2000 540 900 300"], timeout=8)
        time.sleep(2)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS screens (
            screen_hash TEXT PRIMARY KEY,
            package TEXT,
            activity TEXT,
            timestamp TEXT,
            elements_json TEXT,
            actions_json TEXT
        )
    """)
    return conn

def dump_ui():
    """UI-Dump vom Xiaomi holen"""
    # uiautomator dump auf Xiaomi ausführen
    ensure_unlocked()
    ensure_unlocked()
    rc, _, err = ssh_cmd(["su", "-c", "uiautomator dump /sdcard/ui.xml"])
    if rc != 0:
        print(f"FEHLER: uiautomator dump fehlgeschlagen: {err}")
        return None
    
    # XML-Datei holen
    rc, xml_content, err = ssh_cmd(["su", "-c", "cat /sdcard/ui.xml"])
    if rc != 0:
        print(f"FEHLER: Konnte UI-XML nicht lesen: {err}")
        return None
    
    return xml_content

def parse_ui_xml(xml_content):
    """UI-XML parsen und Elemente extrahieren"""
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"FEHLER: XML-Parse-Error: {e}")
        return None, None, []
    
    # Package und Activity aus Root-Node extrahieren
    package = root.get("package", "unknown")
    activity = root.get("activity", "unknown")
    
    elements = []
    for node in root.iter("node"):
        elem = {
            "class": node.get("class", ""),
            "text": node.get("text", ""),
            "content_desc": node.get("content-desc", ""),
            "resource_id": node.get("resource-id", ""),
            "bounds": node.get("bounds", ""),
            "clickable": node.get("clickable") == "true",
            "enabled": node.get("enabled") == "true",
            "package": node.get("package", "")
        }
        # Nur interessante Elemente (Buttons, Inputs, Labels)
        if elem["clickable"] or elem["text"] or elem["content_desc"]:
            elements.append(elem)
    
    return package, activity, elements

def compute_screen_hash(package, activity, elements=None):
    # STABILE Identitaet: nur Package+Activity (Badges/Zaehler/Uhr variieren)
    data = package + "|" + activity
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def main():
    print("=== Screen-State-Mapping Phase 1 ===")
    print("Hole UI-Dump vom Xiaomi...")
    
    # UI-Dump holen
    xml_content = dump_ui()
    if not xml_content:
        print("Abbruch: Kein UI-Dump")
        return
    
    print(f"✓ UI-Dump geholt ({len(xml_content)} Bytes)")
    
    # XML parsen
    package, activity, elements = parse_ui_xml(xml_content)
    fg_pkg, fg_act = get_foreground()
    if fg_pkg:
        package, activity = fg_pkg, fg_act
    if not package or package == "unknown":
        print("Abbruch: Parse-Fehler")
        return
    
    print(f"✓ Screen erkannt: {package}/{activity}")
    print(f"✓ {len(elements)} interessante Elemente gefunden")
    
    # Hash berechnen
    screen_hash = compute_screen_hash(package, activity, elements)
    print(f"✓ Screen-Hash: {screen_hash}")
    
    # DB initialisieren
    conn = init_db()
    
    import json
    conn.execute("""
        INSERT OR REPLACE INTO screens (screen_hash, package, activity, timestamp, elements_json, actions_json)
        VALUES (?, ?, ?, datetime('now'), ?,
                COALESCE((SELECT actions_json FROM screens WHERE screen_hash=?), '[]'))
    """, (screen_hash, package, activity, json.dumps(elements), screen_hash))
    conn.commit()
    print("Screen gespeichert/aktualisiert: " + screen_hash)

    # Ausgabe
    print("\n=== ELEMENTE ===")
    for i, elem in enumerate(elements[:10], 1):
        text = elem["text"] or elem["content_desc"] or elem["resource_id"]
        print(f"{i}. {elem['class'].split('.')[-1]}: {text[:50]}")
    
    if len(elements) > 10:
        print(f"... und {len(elements) - 10} weitere")
    
    conn.close()

if __name__ == "__main__":
    main()
