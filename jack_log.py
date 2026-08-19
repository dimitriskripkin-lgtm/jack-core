#!/usr/bin/env python3
"""Legacy-Wrapper: Leitet alte jack_log Aufrufe an jack_logging weiter."""
import jack_logging

_logger = jack_logging.get('legacy_wrapper')

def log_decision(tag, text='', ergebnis=''):
    """Faengt alte log_decision Aufrufe ab."""
    msg = str(tag)
    if text: msg += f" | {text}"
    if ergebnis: msg += f" | {ergebnis}"
    _logger.info(msg)

def recent(n=15):
    """Faengt alte recent Aufrufe ab."""
    try:
        return jack_logging.letzte(n)
    except AttributeError:
        return "Legacy Wrapper: 'letzte' Funktion in jack_logging nicht gefunden."
