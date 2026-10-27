# JACK_TUNE_APPSPERRE (27.10.2026, Kap 296): zentrale App-Sperrliste, fail-closed. Entwurf ChatGPT K1c, Abnahme Claude.
import os
import re

SPERRLISTE = "/data/data/com.termux/files/home/jack/.sperrliste_apps"
_PAKET = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+")

def gesperrt(paket):
    if not isinstance(paket, str) or not _PAKET.fullmatch(paket):
        return True
    try:
        with open(SPERRLISTE, encoding="utf-8") as datei:
            zeilen = [zeile.strip() for zeile in datei]
    except (OSError, UnicodeError):
        return True
    eintraege = [zeile for zeile in zeilen if zeile and not zeile.startswith("#")]
    if not eintraege or any(not _PAKET.fullmatch(zeile) for zeile in eintraege):
        return True
    return paket in eintraege
