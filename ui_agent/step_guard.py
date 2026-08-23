#!/usr/bin/env python3
"""Zwischen jedem UI-Schritt: Sperre, Overlay, Beweis, Rollback."""
import re, time, subprocess, os

XIAOMI = "xiaomi-jack"
HOME = "/data/data/com.termux/files/home"
DUMP = "/sdcard/screen.xml"

OVERLAY_HINTS = (
    "cookie", "zustimmen", "accept all", "alle akzeptieren",
    "werbung", "advertisement", "installieren", "schließen",
    "nicht jetzt", "later", "superuser", "magisk",
    "passwort", "muster", "pin eingeben", "entsperren",
)

def log(msg):
    print(f"[guard] {msg}", flush=True)

def ssh(cmd, timeout=15):
    env = os.environ.copy()
    env["HOME"] = HOME
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", XIAOMI, cmd],
        capture_output=True, text=True, timeout=timeout, env=env,
    )
    return ((r.stdout or "") + (r.stderr or "")).strip(), r.returncode

def su(cmd):
    esc = cmd.replace("'", "'\"'\"'")
    return ssh(f"su -c '{esc}'")

def focus_line():
    out, _ = su("dumpsys window 2>/dev/null | grep mCurrentFocus | head -1")
    if not out or "mCurrentFocus" not in out:
        out, _ = ssh("dumpsys window 2>/dev/null | grep mCurrentFocus | head -1")
    return out

def is_locked():
    out, _ = ssh(
        "dumpsys window 2>/dev/null | grep -E "
        "'mDreamingLockscreen|mShowingLockscreen|isStatusBarKeyguard' | head -5"
    )
    low = out.lower()
    if "mshowinglockscreen=true" in low.replace(" ", ""):
        return True
    if "mdreaminglockscreen=true" in low.replace(" ", ""):
        return True
    if "keyguard" in low and "true" in low:
        return True
    # fallback: focus
    foc = focus_line().lower()
    if "keyguard" in foc or "lockscreen" in foc:
        return True
    return False

def unlock_short():
    log("Sperre erkannt → unlock")
    su("input keyevent 224")
    time.sleep(0.2)
    su("input keyevent 82")
    time.sleep(0.15)
    su("input swipe 540 1500 540 1000 160")
    time.sleep(0.6)

def dump_xml():
    su(f"uiautomator dump {DUMP}")
    out, _ = ssh(f"cat {DUMP} 2>/dev/null")
    return out if out and "<hierarchy" in out else ""

def screen_hash(xml):
    texts = re.findall(r'text="([^"]{2,40})"', xml or "")
    foc = focus_line()
    blob = foc + "|" + "|".join(texts[:20])
    return str(abs(hash(blob)) % (10**10)), texts[:15]

def package_of_focus():
    foc = focus_line()
    # Window{... u0 package/activity}
    m = re.search(r"\bu0\s+([a-zA-Z0-9_.]+)/", foc)
    if m:
        return m.group(1)
    m = re.search(r"([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)/", foc)
    if m:
        return m.group(1)
    return foc[:80] if foc else "?"

def find_overlay(xml):
    low = (xml or "").lower()
    hits = [h for h in OVERLAY_HINTS if h in low]
    return hits

def dismiss_overlays(xml, max_try=2):
    """Einfache Stoerer: BACK oder sichtbares Schließen/OK."""
    for i in range(max_try):
        hits = find_overlay(xml)
        if not hits:
            return False
        log(f"Overlay-Hinweise: {hits[:5]} → versuche dismiss")
        # oft hilft BACK
        su("input keyevent 4")
        time.sleep(0.7)
        xml = dump_xml()
        if not find_overlay(xml):
            log("Overlay weg")
            return True
    return bool(find_overlay(xml))

def ensure_ready(reason="preflight"):
    """Vor jedem Schritt. Gibt dict state zurück."""
    log(f"ensure_ready ({reason})")
    if is_locked():
        unlock_short()
    xml = dump_xml()
    if not xml:
        log("WARN: kein UI-Dump")
        return {"ok": False, "locked": is_locked(), "package": package_of_focus(),
                "hash": "", "texts": [], "overlay": []}
    h, texts = screen_hash(xml)
    overlay = find_overlay(xml)
    if overlay:
        dismiss_overlays(xml)
        xml = dump_xml()
        h, texts = screen_hash(xml)
        overlay = find_overlay(xml)
    pkg = package_of_focus()
    st = {
        "ok": True,
        "locked": False,
        "package": pkg,
        "hash": h,
        "texts": texts,
        "overlay": overlay,
    }
    log(f"ready pkg={pkg} hash={h[:10]} overlay={overlay[:3]} texts={texts[:5]}")
    return st

def run_step(name, action_fn, why, expect_change=True):
    """
    action_fn: callable ohne args, soll etwas auf dem Geraet tun.
    why: kurzer Grund (wird geloggt).
    """
    before = ensure_ready(reason=f"before:{name}")
    log(f"SCHRITT {name} | WARUM: {why}")
    try:
        action_fn()
    except Exception as e:
        log(f"Aktion-Fehler: {e}")
        return False, before, before
    time.sleep(1.0)
    after = ensure_ready(reason=f"after:{name}")
    changed = after.get("hash") != before.get("hash") or after.get("package") != before.get("package")
    if expect_change and not changed:
        log("Kein Fortschritt → ROLLBACK BACK")
        su("input keyevent 4")
        time.sleep(0.5)
        after = ensure_ready(reason="after_rollback")
        return False, before, after
    log(f"OK {before.get('hash','')[:8]} → {after.get('hash','')[:8]} pkg={after.get('package')}")
    return True, before, after

if __name__ == "__main__":
    st = ensure_ready("manual")
    print("STATE", st)
