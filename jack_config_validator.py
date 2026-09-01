#!/usr/bin/env python3
"""jack_config_validator.py — Prüft config.ini auf Vollständigkeit beim Start."""
MODULE_VERSION = 1

import os, sys
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_config_validator")

REQUIRED = [
    "GEMINI_API_KEY", "GROQ_API_KEY", "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID", "JACK_HOME",
]
OPTIONAL = ["XIAOMI_IP", "OLLAMA_HOST", "GROQ_MODEL", "GEMINI_MODEL"]

def run() -> tuple:
    try:
        import jack_config as _jc
        missing, warnings = [], []
        for key in REQUIRED:
            val = _jc.get_param(key, fallback=None)
            if not val: missing.append(key)
        for key in OPTIONAL:
            val = _jc.get_param(key, fallback=None)
            if not val: warnings.append(key)
        if missing:
            log.warn(f"Config: Pflichtfelder fehlen: {missing}")
        if warnings:
            log.info(f"Config: Optionale Felder fehlen: {warnings}")
        if not missing:
            log.info("Config: alle Pflichtfelder vorhanden")
        return len(missing)==0, missing, warnings
    except Exception as e:
        log.exception("Config-Validator Fehler", e)
        return False, ["config.ini nicht ladbar"], []

if __name__ == "__main__":
    ok, missing, warn = run()
    print(f"Config: {'OK' if ok else 'FEHLER'}")
    if missing: print(f"  Fehlt: {missing}")
    if warn: print(f"  Optional fehlt: {warn}")
