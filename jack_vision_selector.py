#!/usr/bin/env python3
"""jack_vision_selector.py - Text-Tap via uiautomator. Update-immun. Immer frischer Dump."""
import subprocess, re, os, sys

XIAOMI = "xiaomi-jack"
DUMP = "/sdcard/screen.xml"
HOME = "/data/data/com.termux/files/home"

def _ssh(remote, timeout=18):
    env = os.environ.copy()
    env["HOME"] = HOME
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", XIAOMI, remote],
        capture_output=True, text=True, timeout=timeout, env=env,
    )
    return (r.stdout or "") + (r.stderr or ""), r.returncode

def _su(cmd, timeout=18):
    # cmd ohne aeussere Quotes; wir escapen einfach
    esc = cmd.replace("'", "'\"'\"'")
    return _ssh("su -c '%s'" % esc, timeout=timeout)

def dump_screen():
    _su("uiautomator dump %s" % DUMP)
    out, rc = _ssh("cat %s 2>/dev/null" % DUMP)
    if not out or "<hierarchy" not in out:
        return None
    return out

def _bounds_near(xml, idx, window=350):
    chunk = xml[max(0, idx - window): idx + window]
    m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', chunk)
    if not m:
        return None
    x1, y1, x2, y2 = map(int, m.groups())
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    if cx < 5 or cy < 5:
        return None
    return cx, cy

def find_element(xml, query, partial=False):
    if not xml or not query:
        return None
    q = re.escape(query)
    if partial:
        attrs = [
            r'(?:text|content-desc)="[^"]*%s[^"]*"' % q,
        ]
    else:
        attrs = [
            r'text="%s"' % q,
            r'content-desc="%s"' % q,
        ]
    for ap in attrs:
        for m in re.finditer(ap, xml, re.I):
            pos = _bounds_near(xml, m.start())
            if pos:
                return pos
    return None

def tap(cx, cy):
    _su("input tap %d %d" % (cx, cy))
    return True

def tap_text(query, partial=True):
    """Dump → suchen → tippen. partial=True default (robuster)."""
    xml = dump_screen()
    if not xml:
        return False, "Kein Screen-Dump"
    pos = find_element(xml, query, partial=partial)
    if not pos:
        # exact fallback
        if partial:
            pos = find_element(xml, query, partial=False)
        if not pos:
            return False, "Element nicht gefunden: %s" % query
    tap(pos[0], pos[1])
    return True, "Getippt auf '%s' bei %s" % (query, pos)

def list_elements(max_items=30):
    xml = dump_screen()
    if not xml:
        return []
    found = []
    seen = set()
    for m in re.finditer(r'<node [^>]+>', xml):
        tag = m.group(0)
        tm = re.search(r'text="([^"]+)"', tag)
        cm = re.search(r'content-desc="([^"]+)"', tag)
        label = (tm.group(1) if tm else "") or (cm.group(1) if cm else "")
        if not label or len(label) < 2 or label in seen:
            continue
        seen.add(label)
        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', tag)
        pos = None
        if bm:
            x1, y1, x2, y2 = map(int, bm.groups())
            pos = ((x1 + x2) // 2, (y1 + y2) // 2)
        found.append((label[:60], pos))
        if len(found) >= max_items:
            break
    return found

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python3 jack_vision_selector.py list")
        print("         python3 jack_vision_selector.py <text>")
        sys.exit(1)
    if sys.argv[1] == "list":
        for label, pos in list_elements():
            print(" -", label, pos or "")
    else:
        q = " ".join(sys.argv[1:])
        ok, msg = tap_text(q)
        print(("OK: " if ok else "FEHLER: ") + msg)
