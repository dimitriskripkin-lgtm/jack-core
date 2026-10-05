#!/usr/bin/env python3
"""JACK_TUNE_SEHEN Baum zuerst, Foto nur wenn der Baum leer ist."""
import jack_xiaomi

def baum():
    r = jack_xiaomi.ssh("uiautomator dump /sdcard/jack_ui.xml && head -c 4000 /sdcard/jack_ui.xml", timeout=12)
    text = (r.get("out") or "")
    if r.get("ok") and "<node" in text:
        return {"ok": True, "weg": "baum", "out": text[:4000]}
    return {"ok": False, "weg": "leer", "out": text[:300]}

def sehen():
    b = baum()
    if b.get("ok"):
        return b
    return {"ok": False, "weg": "foto_noetig", "out": b.get("out") or ""}
