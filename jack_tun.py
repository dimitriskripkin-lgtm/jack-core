#!/usr/bin/env python3
"""JACK_TUNE_TUN Intent und Datei vor Tippen."""
import jack_xiaomi

def intent(action, data=""):
    # JACK_TUNE_INTSU: ssh() laeuft ohne su. System-Intents brauchen su -c, sonst InvocationTargetException.
    bad = " ;|&`$'\"\""
    if not action or any(c in action for c in bad):
        return {"ok": False, "out": "action ungueltig"}
    cmd = "am start -a " + action + " -f 0x10008000"  # JACK_TUNE_CLEARTASK
    if data:
        if any(c in data for c in bad):
            return {"ok": False, "out": "data ungueltig"}
        cmd += " -d " + data
    r = jack_xiaomi.run_shell(cmd, as_root=True, timeout=10)
    return {"ok": bool(r.get("success")), "out": ((r.get("stdout") or "") + " " + (r.get("stderr") or ""))[:400]}

def datei(path):
    return jack_xiaomi.ssh("test -f " + path + " && echo DA || echo WEG", timeout=8)

def tippen_erst_wenn_kein_kommando(action, data=""):
    r = intent(action, data)
    if r.get("ok"):
        return {"ok": True, "weg": "kommando", "out": r.get("out") or ""}
    return {"ok": False, "weg": "tippen_noetig", "out": r.get("out") or ""}
