#!/usr/bin/env python3
# ScreenStateTracker + OutcomeEvaluator - kein Vision-API, XML-basiert
import subprocess, hashlib
import xml.etree.ElementTree as ET
UI_XML = "/sdcard/jack_ui.xml"
ADB = ["adb", "-s", "127.0.0.1:5555", "shell"]

def _adb(cmd, t=10):
    try:
        r = subprocess.run(ADB + [cmd], capture_output=True, text=True, timeout=t)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def get_foreground_package():
    _, out, _ = _adb("dumpsys activity | grep mResumedActivity | tail -1")
    for p in (out or "").split():
        if "/" in p and "." in p and not p.startswith("{"):
            return p.split("/")[0]
    return None

def get_screen_state():
    _, out, _ = _adb("uiautomator dump " + UI_XML + " > /dev/null 2>&1 && cat " + UI_XML)
    if not out or "<hierarchy" not in out:
        return {"xml_hash": None, "package": None, "elements": set(), "raw_xml": ""}
    elements, package = set(), None
    try:
        for node in ET.fromstring(out).iter("node"):
            text = node.get("text", "").strip()
            desc = node.get("content-desc", "").strip()
            rid  = node.get("resource-id", "").strip()
            pkg  = node.get("package", "")
            if pkg and not package: package = pkg
            if text or desc: elements.add((text, desc, rid))
    except ET.ParseError: pass
    if not package: package = get_foreground_package()
    return {"xml_hash": hashlib.md5(out.encode()).hexdigest()[:8],
            "package": package, "elements": elements, "raw_xml": out}

def diff_states(before, after):
    if not before or not after:
        return {"changed": False, "package_changed": False,
                "old_package": None, "new_package": None,
                "added_elements": [], "removed_elements": []}
    pkg_changed  = before.get("package") != after.get("package")
    hash_changed = before.get("xml_hash") != after.get("xml_hash")
    added   = list(after.get("elements", set()) - before.get("elements", set()))[:10]
    removed = list(before.get("elements", set()) - after.get("elements", set()))[:10]
    return {"changed": hash_changed, "package_changed": pkg_changed,
            "old_package": before.get("package"), "new_package": after.get("package"),
            "added_elements": added, "removed_elements": removed}

def evaluate_outcome(diff, expected_package=None, expected_text=None):
    if not diff.get("changed"):
        return ("fail", "Bildschirm unveraendert")
    if expected_package and diff.get("new_package") == expected_package:
        return ("success", "Ziel-Package aktiv: " + expected_package)
    if expected_text:
        needle = expected_text.lower()
        for (text, desc, rid) in diff.get("added_elements", []):
            if needle in text.lower() or needle in desc.lower():
                return ("success", "Ziel-Element erschienen: " + expected_text)
    if diff.get("package_changed"):
        return ("unclear", "Package-Wechsel -> " + str(diff.get("new_package")))
    return ("unclear", str(len(diff.get("added_elements", []))) + " neue Elemente, kein Ziel definiert")

if __name__ == "__main__":
    print("[Tracker] Hole Screen-Zustand...")
    s = get_screen_state()
    print("  Package : " + str(s["package"]))
    print("  Hash    : " + str(s["xml_hash"]))
    print("  Elemente: " + str(len(s["elements"])))
    for el in list(s["elements"])[:3]: print("  -> " + str(el))
    print("[Tracker] OK")
