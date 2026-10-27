"""JACK_TUNE_SPOTIFY_S1 (27.10.2026, Kap 306; Entwurf ChatGPT S1, Abnahme Claude): kontrollierte Spotify-Play/Pause/Resume-Adapter. Offline testbar.
Keine IO bei Import. Erfolg heisst erst PLAYING nach unabhaengigem dumpsys-Beleg.
"""
import os
import pathlib
import re
import subprocess
import time

APP = "com.spotify.music"


def _run(args, timeout=8):
    try:
        return subprocess.run(args, text=True, capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def _vorpruefung():
    try:  # Claude: zentrale Sperrliste (K1c), fail-closed
        import jack_app_sperre as _guard
        if _guard.gesperrt(APP):
            return "Spotify ist durch die App-Sperrliste gesperrt (oder Liste unlesbar)."
    except Exception:
        return "App-Sperrpruefung nicht verfuegbar. Kein Start."
    res = _run(["rish", "-c", "pm path " + APP], timeout=6)
    if res is None or res.returncode != 0:
        return "Shizuku/rish ist nicht bereit. Spotify nicht gestartet."
    if "package:" not in (res.stdout or ""):
        return "Spotify-App ist nicht installiert oder nicht erreichbar."
    return None


def _medienstatus():
    res = _run(["rish", "-c", "dumpsys media_session"], timeout=8)
    return (res.stdout or "") if res is not None and res.returncode == 0 else ""


def _bestaetigt(status, titel=None, pause=False):
    """Absichtlich streng: Status und Spotify-Paket im selben Session-Ausschnitt.
    Unbekanntes Android-dumpsys-Format -> kein nachgewiesener Erfolg.
    """
    if not status:
        return False
    chunks = re.split(r"(?=\n\s*(?:Session\s*#|Session\s*\{|package=))", status)
    if len(chunks) < 2:
        chunks = [status]
    for part in chunks:
        if APP not in part:
            continue
        # Claude: Honor-Format live gemessen: "state=PlaybackState {state=PLAYING(3), ..."
        expected = (r"\bstate\s*=\s*(?:PAUSED\(2\)|STOPPED\(1\)|[12])(?![0-9])" if pause
                    else r"\bstate\s*=\s*(?:PLAYING\(3\)|3)(?![0-9])")
        if not re.search(expected, part, re.I):
            continue
        if titel and titel.casefold() not in part.casefold():
            continue
        return True
    return False


def _warte_bestaetigt(titel=None, pause=False, versuche=4, pause_s=1.5):
    for i in range(versuche):
        if _bestaetigt(_medienstatus(), titel, pause=pause):
            return True
        if i < versuche - 1:
            time.sleep(pause_s)
    return False


def spiele(suche):
    reason = _vorpruefung()
    if reason:
        return reason
    if not str(suche).strip():
        return "Kein Titel angegeben."
    try:
        import jack_spotify_play as live
        result = live.spiele(suche)
    except Exception as exc:
        return "Spotify-Suche/Start fehlgeschlagen (" + type(exc).__name__ + ")."
    if not isinstance(result, dict) or not result.get("ok"):
        return "Spotify: " + str((result or {}).get("fehler", "nichts gefunden"))
    title = str(result.get("titel") or "")
    artist = str(result.get("kuenstler") or "")
    if title and _warte_bestaetigt(title):
        return "Spotify läuft: " + title + " | " + artist
    return "Spotify-Start gesendet: " + title + " | " + artist + ". Wiedergabe NICHT unabhängig bestätigt."


def taste(aktion):
    if aktion not in ("pause", "weiter"):
        return "Ungültiger Spotify-Befehl."
    reason = _vorpruefung()
    if reason:
        return reason
    code = "127" if aktion == "pause" else "126"
    res = _run(["rish", "-c", "input keyevent " + code], timeout=8)
    if res is None or res.returncode != 0:
        return "Shizuku/rish fehlgeschlagen: Befehl nicht ausgeführt."
    if _warte_bestaetigt(pause=(aktion == "pause")):
        return "Spotify: " + ("pausiert" if aktion == "pause" else "Wiedergabe läuft")
    return "Spotify: " + aktion + " gesendet, PlaybackState nicht eindeutig bestätigt."
