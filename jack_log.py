#!/usr/bin/env python3
"""jack_log.py — Zentraler Logger für alle JACK-Module.

Usage:
    from jack_log import get_logger
    log = get_logger("jack_cortex")
    log.info("Gestartet")
    log.warn("Verbindung langsam")
    log.error("Kritischer Fehler")
    log.debug("Detail-Info")
"""
MODULE_VERSION = 1

import os, sys, time, threading
from enum import IntEnum

J = os.path.expanduser("~/jack")
MAIN_LOG = os.path.join(J, "jack_main.log")
MAX_LOG_BYTES = 5 * 1024 * 1024  # 5MB dann rotieren

_lock = threading.Lock()

class Level(IntEnum):
    DEBUG = 0
    INFO  = 1
    WARN  = 2
    ERROR = 3

LEVEL_LABELS = {
    Level.DEBUG: "DEBUG",
    Level.INFO:  "INFO ",
    Level.WARN:  "WARN ",
    Level.ERROR: "ERROR",
}

def _rotate_if_needed():
    try:
        if os.path.exists(MAIN_LOG) and os.path.getsize(MAIN_LOG) > MAX_LOG_BYTES:
            old = MAIN_LOG + ".1"
            if os.path.exists(old): os.remove(old)
            os.rename(MAIN_LOG, old)
    except Exception: pass

def _write(module, level, msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    label = LEVEL_LABELS.get(level, "?????")
    line = f"{ts} [{label}] [{module:<22}] {msg}\n"
    with _lock:
        _rotate_if_needed()
        try:
            with open(MAIN_LOG, "a") as f:
                f.write(line)
        except Exception: pass
    # ERROR immer auch auf stderr
    if level >= Level.ERROR:
        sys.stderr.write(line)

class JackLogger:
    """Logger-Instanz pro Modul."""
    def __init__(self, module: str, min_level: Level = Level.INFO):
        self.module = module[:22]
        self.min_level = min_level

    def debug(self, msg): self._log(Level.DEBUG, msg)
    def info(self,  msg): self._log(Level.INFO,  msg)
    def warn(self,  msg): self._log(Level.WARN,  msg)
    def error(self, msg): self._log(Level.ERROR, msg)

    def _log(self, level, msg):
        if level >= self.min_level:
            _write(self.module, level, str(msg))

    def exception(self, msg, exc):
        """Fehler mit Exception-Info loggen."""
        self._log(Level.ERROR, f"{msg} | {type(exc).__name__}: {exc}")

_loggers: dict = {}

def get_logger(module: str, min_level: Level = Level.INFO) -> JackLogger:
    """Gibt Logger-Instanz zurück. Pro Modul nur eine Instanz."""
    if module not in _loggers:
        _loggers[module] = JackLogger(module, min_level)
    return _loggers[module]

def tail(n=50) -> list:
    """Letzte n Zeilen aus jack_main.log."""
    try:
        lines = open(MAIN_LOG).readlines()
        return lines[-n:]
    except Exception: return []

if __name__ == "__main__":
    log = get_logger("jack_log_test")
    log.debug("Debug-Nachricht")
    log.info("System gestartet")
    log.warn("Warnung Test")
    log.error("Fehler Test")
    print("Letzten 4 Zeilen:")
    for l in tail(4): print(" ", l.rstrip())

def log_decision(key: str, value: str = "", extra: str = ""):
    """Kompatibilitäts-Shim — ersetzt alte jack_log.log_decision() Aufrufe."""
    msg = f"{key}: {value}"
    if extra: msg += f" | {extra}"
    _write("jack_autonomous", Level.INFO, msg)
