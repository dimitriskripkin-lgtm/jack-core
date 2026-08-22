#!/usr/bin/env python3
"""jack_vision_selector.py - Phase 2: Text-basierte Element-Suche via uiautomator.
Update-immun. Kein Koordinaten-Chaos. Immer frischen Dump vor Klick.
"""
import subprocess, re, os, sys

XIAOMI = "xiaomi-jack"
DUMP_PATH = "/sdcard/screen.xml"

def _ssh(cmd, timeout=15):
    r = subprocess.run(["ssh", XIAOMI, cmd],
        capture_output=True, text=True, timeout=timeout)
    return r.stdout + r.stderr

def dump_screen():
    """Frischen uiautomator-Dump holen. IMMER vor Klick aufrufen."""
    _ssh(f"su -c 'uiautomator dump {DUMP_PATH}' 2>/dev/null")
    xml = _ssh(f"cat {DUMP_PATH} 2>/dev/null")
    if not xml or "<hierarchy" not in xml:
        return None
    return xml

def find_element(xml, query, attr="text"):
    """Findet Element nach text oder content-desc. Gibt (cx, cy) zurück."""
    if not xml:
        return None
    patterns = [
        rf'{attr}="{re.escape(query)}"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"',
        rf'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"[^>]*{attr}="{re.escape(query)}"',
    ]
    for pat in patterns:
        m = re.search(pat, xml)
        if m:
            g = m.groups()
            cx = (int(g[0]) + int(g[2])) // 2
            cy = (int(g[1]) + int(g[3])) // 2
            return cx, cy
    if attr == "text":
        return find_element(xml, query, attr="content-desc")
    return None

def find_partial(xml, query):
    """Sucht Teilstring im text oder content-desc."""
    if not xml:
        return None
    pat = r'(?:text|content-desc)="[^"]*' + re.escape(query) + r'[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"'
    m = re.search(pat, xml)
    if m:
        cx = (int(m.group(1)) + int(m.group(3))) // 2
        cy = (int(m.group(2)) + int(m.group(4))) // 2
        return cx, cy
    return None

def tap(cx, cy):
    """Tippt auf absolute Koordinaten via input tap."""
    result = _ssh(f"input tap {cx} {cy}")
    return True

def tap_text(query, partial=False):
    """Kompletter Flow: Dump holen → Element suchen → tippen."""
    xml = dump_screen()
    if not xml:
        return False, "Kein Screen-Dump"
    pos = find_partial(xml, query) if partial else find_element(xml, query)
    if not pos:
        return False, f"Element nicht gefunden: {query}"
    tap(pos[0], pos[1])
    return True, f"Getippt auf '{query}' bei {pos}"

def list_elements(xml=None, max_items=20):
    """Alle sichtbaren Text-Elemente ausgeben (Debug)."""
    if xml is None:
        xml = dump_screen()
    if not xml:
        return []
    found = re.findall(r'text="([^"]+)"', xml)
    found += re.findall(r'content-desc="([^"]+)"', xml)
    seen = []
    for f in found:
        if f and f not in seen:
            seen.append(f)
    return seen[:max_items]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python3 jack_vision_selector.py <text>")
        print("         python3 jack_vision_selector.py list")
        sys.exit(1)
    if sys.argv[1] == "list":
        xml = dump_screen()
        els = list_elements(xml)
        print(f"Sichtbare Elemente ({len(els)}):")
        for e in els:
            print(" -", e)
    else:
        query = " ".join(sys.argv[1:])
        ok, msg = tap_text(query)
        print("OK:" if ok else "FEHLER:", msg)
