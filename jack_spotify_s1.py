"""JACK_TUNE_SPOTIFY_S1 (27.10.2026, Kap 306; Entwurf ChatGPT, Abnahme Claude): Spotify-Kommandos, NUR Integration durch Claude.
Keine IO bei Import. Telegram sendet nur die erzeugten Antwort-/Button-Daten.
"""
import hashlib
import json
import re
import secrets
import threading
import time

_pending = {}
_lock = threading.RLock()
_TTL = 600  # 10 Minuten; kein Persistieren: Neustart verwirft Freigaben
_KEYS = {"titel", "kuenstler", "album", "hinzugefuegt", "dauer", "zufall"}


def _authorized(chat_id, from_id, trusted_chat_id):
    """JACK wird hier nur in Dimas 1:1-Chat benutzt (chat.id == from.id)."""
    return (chat_id is not None and from_id is not None and trusted_chat_id is not None
            and str(chat_id) == str(from_id) == str(trusted_chat_id))


def _result(text, buttons=None):
    return {"text": str(text), "buttons": buttons}


def _parse(text):
    s = str(text or "").strip()
    if re.search(r"(?i)\b(?:auf|am)\s+(?:dem\s+)?xiaomi\b", s):  # JACK_TUNE_S1PARSE2: Xiaomi-Wunsch -> alter Xiaomi-Weg
        return None
    m = re.fullmatch(r"(?i)(?:(?:/spiel|spiel|jack\s*[,!:]?\s*spiel)[\s,:!.]+)(.+)", s)
    if m:
        q = re.sub(r"(?i)[\s,.!?]*\b(?:auf|am|im)\s+(?:dem\s+|der\s+)?(?:honor|handy|telefon)\b[\s.!?]*$", "", m.group(1)).strip(" ,.!?")
        if q:
            return ("play", q)
    if re.fullmatch(r"(?i)/pause", s):
        return ("pause",)
    if re.fullmatch(r"(?i)/weiter", s):
        return ("weiter",)
    if re.fullmatch(r"(?i)/lieblinge", s):
        return ("lieblinge",)
    m = re.fullmatch(r"(?i)/sortiere\s+(.+?)\s+(titel|kuenstler|künstler|album|hinzugefuegt|hinzugefügt|dauer|zufall)(?:\s+(ab|absteigend))?", s)
    if m:
        key = m.group(2).casefold().replace("ü", "ue")
        return ("sort", m.group(1).strip(), key, bool(m.group(3)))
    m = re.fullmatch(r"(?i)/(?:zurueck|zurück|spotify_zurueck)\s+(.+)", s)
    if m:
        return ("restore", m.group(1).strip())
    return None


def _find_playlist(sp, name):
    candidates = [p for p in sp.playlists() if str(p.get("name", "")).casefold() == name.casefold()]
    if not candidates:
        raise ValueError("Playlist nicht gefunden")
    if len(candidates) != 1:
        raise ValueError("Mehrere Playlists mit diesem Namen: bitte eindeutig benennen")
    return candidates[0]["id"]


def _fingerprint(sp, pid):
    rows = sp.items(pid)
    uris = sp._uris(rows)
    digest = hashlib.sha256(json.dumps(uris, ensure_ascii=False).encode()).hexdigest()
    meta = sp._http("GET", "/playlists/" + pid)
    snap = meta.get("snapshot_id")
    if not snap:
        raise RuntimeError("Spotify-Snapshot fehlt")
    return snap, digest, rows


def _create(kind, info, chat_id, from_id, trusted_chat_id, preview):
    if not _authorized(chat_id, from_id, trusted_chat_id):
        return _result("Nicht freigegeben")
    token = secrets.token_hex(16)
    info = dict(info, kind=kind, chat_id=str(chat_id), user_id=str(from_id),
                expires=time.monotonic() + _TTL)
    with _lock:
        for k in list(_pending):
            if _pending[k]["expires"] <= time.monotonic():
                _pending.pop(k, None)
        _pending[token] = info
    return _result(preview + "\n10 Minuten gültig. Sicher?", [[
        ("Ja, ausführen", "s1:ok:" + token),
        ("Abbrechen", "s1:no:" + token)]])


def handle_text(text, chat_id, from_id, trusted_chat_id):
    """None = kein S1-Befehl; sonst dict(text,buttons). Nur autorisierter Privatchat."""
    cmd = _parse(text)
    if cmd is None:
        return None
    if not _authorized(chat_id, from_id, trusted_chat_id):
        return _result("Spotify-Befehl nicht autorisiert")
    try:
        if cmd[0] in ("play", "pause", "weiter"):
            import jack_spotify_s1_play as player
            if cmd[0] == "play":
                return _result(player.spiele(cmd[1]))
            return _result(player.taste(cmd[0]))
        if cmd[0] == "lieblinge":
            import jack_spotify_top as top
            ranked, _ = top.rangliste()  # Nur Leseaufrufe
            first = ", ".join(str(x.get("name", "?")) for x in ranked[:5])
            return _create("favorites", {}, chat_id, from_id, trusted_chat_id,
                           "Lieblinge-Playlist neu aufbauen. Top 5: " + first)
        import jack_spotify as sp
        pid = _find_playlist(sp, cmd[1])
        snapshot, fingerprint, rows = _fingerprint(sp, pid)
        if cmd[0] == "sort":
            _, name, key, descending = cmd
            if key not in _KEYS:
                return _result("Sortierschlüssel unbekannt")
            positions = list(range(len(rows)))
            if key == "zufall":
                description = "zufällig"
            else:
                positions.sort(key=lambda i: sp._key(rows[i], key), reverse=descending)
                description = ("absteigend " if descending else "aufsteigend ") + key
            sample = ", ".join(str((rows[i].get("item") or rows[i].get("track") or {}).get("name", "?"))
                               for i in positions[:5])
            return _create("sort", {"pid": pid, "key": key, "descending": descending,
                                    "snapshot": snapshot, "fingerprint": fingerprint},
                           chat_id, from_id, trusted_chat_id,
                           "Playlist '" + name + "' (" + str(len(rows)) + " Titel) " + description +
                           ". Vorschau: " + sample)
        if cmd[0] == "restore":
            return _create("restore", {"pid": pid, "snapshot": snapshot,
                                       "fingerprint": fingerprint},
                           chat_id, from_id, trusted_chat_id,
                           "Letzte JACK-Sicherung für '" + cmd[1] + "' wiederherstellen?")
    except Exception as exc:
        return _result("Spotify konnte die Anfrage nicht vorbereiten: " + type(exc).__name__)
    return _result("Spotify-Befehl nicht unterstützt")


def confirm(data, chat_id, from_id, trusted_chat_id):
    """Einmalig konsumieren VOR API-Schreibzugriff; fremde/alte Knöpfe bleiben wirkungslos."""
    m = re.fullmatch(r"s1:(ok|no):([0-9a-f]{32})", str(data or ""))
    if not m:
        return None
    if not _authorized(chat_id, from_id, trusted_chat_id):
        return "Spotify: fremder Absender, abgelehnt"
    kind, token = m.groups()
    with _lock:
        item = _pending.get(token)
        if not item or item["chat_id"] != str(chat_id) or item["user_id"] != str(from_id):
            return "Spotify: Bestätigung nicht mehr gültig"
        _pending.pop(token, None)
    if item["expires"] <= time.monotonic():
        return "Spotify: Bestätigung abgelaufen"
    if kind == "no":
        return "Spotify: abgebrochen, nichts geändert"
    try:
        if item["kind"] == "favorites":
            import jack_spotify_top as top
            result = top.lieblinge_playlist()
            return "Lieblinge aktualisiert. Top 5: " + ", ".join(result.get("top5", [])[:5])
        import jack_spotify as sp
        now_snapshot, now_fingerprint, _ = _fingerprint(sp, item["pid"])
        if (now_snapshot, now_fingerprint) != (item["snapshot"], item["fingerprint"]):
            return "Spotify-Playlist hat sich seit der Vorschau geändert. Bitte neu bestätigen."
        if item["kind"] == "sort":
            res = sp.sortiere(item["pid"], item["key"], item["descending"], bestaetigt=True)
            return "Spotify sortiert: " + str(res.get("verschoben", "?")) + " Verschiebungen"
        if item["kind"] == "restore":
            moved = sp.zurueck(item["pid"], bestaetigt=True)
            return "Spotify-Sicherung wiederhergestellt: " + str(moved) + " Verschiebungen"
    except Exception as exc:
        return ("Spotify-Auftrag fehlgeschlagen oder teilweise ausgeführt (" + type(exc).__name__ +
                "). Nicht blind wiederholen; Backup/Snapshot prüfen.")
    return "Spotify: ungültige Aktion"
