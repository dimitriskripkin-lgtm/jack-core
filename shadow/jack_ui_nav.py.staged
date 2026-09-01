#!/data/data/com.termux/files/usr/bin/python3
"""Xiaomi System-Nav: Back / Home / Recents via keyevent."""
import subprocess

KEYS = {
    "back": 4, "zurueck": 4, "zurück": 4,
    "home": 3, "start": 3, "homescreen": 3,
    "recents": 187, "recent": 187, "tasks": 187,
    "taskmanager": 187, "letzte": 187, "apps": 187,
}

def _ssh(cmd, t=15):
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack", cmd],
        capture_output=True, text=True, timeout=t)
    return r.returncode, (r.stdout or "") + (r.stderr or "")

def nav(action):
    try:  # JACK_TUNE_NAV_UNLOCK
        import jack_xiaomi_unlock as _xu
        _xu.ensure_unlocked()
    except Exception:
        pass
    a = (action or "").strip().lower()
    code = KEYS.get(a)
    if code is None:
        return False, "unbekannte nav action: " + a
    rc, out = _ssh("su -c 'input keyevent %d'" % code)
    return rc == 0, "keyevent %d rc=%s %s" % (code, rc, out[:120])

def try_nav_intent(text):
    """True wenn Text eine Nav-Aktion ist und ausgefuehrt wurde."""
    t = (text or "").strip().lower()
    mapping = [
        (("zurück", "zurueck", "back", "geh zurück", "gehe zurück"), "back"),
        (("home", "homescreen", "zum start", "auf start", "startbildschirm"), "home"),
        (("recents", "taskmanager", "letzte apps", "offene apps", "app umschalter", "apps wechseln"), "recents"),
    ]
    for words, act in mapping:
        if any(w in t for w in words) and len(t) < 40:
            ok, msg = nav(act)
            return True, act, ok, msg
    return False, None, False, ""

if __name__ == "__main__":
    import sys
    act = sys.argv[1] if len(sys.argv) > 1 else "home"
    ok, msg = nav(act)
    print("ok", ok, msg)
