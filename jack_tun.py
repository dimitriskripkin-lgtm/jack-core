#!/usr/bin/env python3
"""JACK_TUNE_TUN Intent und Datei vor Tippen."""
import jack_xiaomi

def intent(action, data=""):
    cmd = "am start -a " + action + " -f 0x10008000"  # JACK_TUNE_CLEARTASK NEW_TASK|CLEAR_TASK, sonst haengt die vorherige Settings-Seite
    if data:
        cmd += " -d " + data
    return jack_xiaomi.ssh(cmd, timeout=10)

def datei(path):
    return jack_xiaomi.ssh("test -f " + path + " && echo DA || echo WEG", timeout=8)

def tippen_erst_wenn_kein_kommando(action, data=""):
    r = intent(action, data)
    if r.get("ok"):
        return {"ok": True, "weg": "kommando", "out": r.get("out") or ""}
    return {"ok": False, "weg": "tippen_noetig", "out": r.get("out") or ""}
