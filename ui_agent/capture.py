#!/usr/bin/env python3
"""ui_agent/capture.py - SINGLE SOURCE OF TRUTH für UI-Wahrnehmung.
Jede andere Dump-Logik ist verboten. - Einheitlicher UI-Dump + Parse + stabiler Screen-Hash."""
import subprocess, re, os, hashlib, time
from typing import List, Dict, Optional, Tuple

XIAOMI = "xiaomi-jack"
DUMP_PATH = "/sdcard/screen.xml"
HOME = "/data/data/com.termux/files/home"

def _ssh(cmd: str, timeout: int = 15) -> Tuple[str, int]:
    env = os.environ.copy()
    env["HOME"] = HOME
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", XIAOMI, cmd],
        capture_output=True, text=True, timeout=timeout, env=env,
    )
    return ((r.stdout or "") + (r.stderr or "")), r.returncode

def _su(cmd: str, timeout: int = 15) -> Tuple[str, int]:
    esc = cmd.replace("'", "'\"'\"'")
    return _ssh(f"su -c '{esc}'", timeout=timeout)

def dump_xml(retries: int = 4) -> Optional[str]:
    for _ in range(retries):
        _su(f"rm -f {DUMP_PATH}; uiautomator dump {DUMP_PATH}")
        time.sleep(0.35)
        out, rc = _ssh(f"cat {DUMP_PATH} 2>/dev/null")
        if out and "<hierarchy" in out:
            return out
        time.sleep(0.4)
    return None

def get_foreground() -> Tuple[str, str]:
    # über su, weil plain-SSH auf diesem MIUI leer zurückkommt
    out, _ = _su("dumpsys window 2>/dev/null | grep -E 'mCurrentFocus|mFocusedApp' | head -6")
    pkg = act = "unknown"
    # Format: com.miui.home/.launcher.Launcher  oder  com.miui.home/com.miui.home.launcher.Launcher
    m = re.search(r"([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.$]+)", out or "")
    if m:
        pkg, act = m.group(1), m.group(2)
    return pkg, act

def parse_elements(xml: str, max_items: int = 40) -> List[Dict]:
    els = []
    seen = set()
    for m in re.finditer(r"<node [^>]+>", xml or ""):
        tag = m.group(0)
        text = ""
        tm = re.search(r'text="([^"]*)"', tag)
        if tm: text = tm.group(1).strip()
        cm = re.search(r'content-desc="([^"]*)"', tag)
        desc = cm.group(1).strip() if cm else ""
        label = (text or desc).replace("&#10;", " ")[:60]
        if len(label) < 1: continue
        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', tag)
        if not bm: continue
        x1, y1, x2, y2 = map(int, bm.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if cx < 10 or cy < 30: continue
        clickable = 'clickable="true"' in tag
        key = (label[:28], cx // 40, cy // 40)
        if key in seen: continue
        seen.add(key)
        els.append({"label": label, "x": cx, "y": cy, "clickable": clickable,
                    "bounds": f"[{x1},{y1}][{x2},{y2}]", "text": text, "content_desc": desc})
        if len(els) >= max_items: break
    return els

def screen_hash(package: str, activity: str) -> str:
    data = f"{package}|{activity}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def take_screenshot(path="/sdcard/jack_screen.png"):
    _su(f"screencap -p {path}")
    return path

def capture() -> Dict:
    xml = dump_xml()
    if not xml:
        return {"ok": False, "error": "kein dump", "hash": "unknown", "elements": []}
    pkg, act = get_foreground()
    elements = parse_elements(xml)
    h = screen_hash(pkg, act)
    state = "normal"
    if pkg in ("com.miui.aod", "com.android.systemui") or "aod" in (pkg or "").lower():
        state = "aod"
    elif pkg == "unknown" or h == "unknown":
        state = "unknown"
    elif not elements:
        state = "empty"
    return {"ok": True, "hash": h, "package": pkg, "activity": act,
            "elements": elements, "xml_len": len(xml),
            "state": state,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
