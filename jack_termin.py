"""JACK_TUNE_TERMIN (27.10.2026, Claude, Kap 307): Kalendertermin per Telegram-Knopf ueber n8n eintragen.
vorschlag(titel, start, ende) schickt Dima einen Knopf. Erst sein "Ja" (confirm) ruft jack_n8n.webhook auf.
Einmal-Code 128 Bit, 10 Minuten gueltig, nur Dimas Privatchat (chat.id == from.id == CHAT_ID).
Offene Freigaben liegen in logs/termin_pending.json (0600), damit der Telegram-Dienst sie sieht.
"""
import json, os, re, secrets, time, uuid
from pathlib import Path

_P = Path("/data/data/com.termux/files/home/jack/logs/termin_pending.json")
_TTL = 600
_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$")


def _laden():
    try:
        return json.loads(_P.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _speichern(d):
    tmp = str(_P) + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, _P)


def _authed(chat, user, trusted):
    return None not in (chat, user, trusted) and str(chat) == str(user) == str(trusted)


def vorschlag(titel, start, ende, beschreibung="", send_kb=None):  # send_kb: im Telegram-Prozess dessen send_keyboard
    titel = str(titel).strip()
    if not (3 <= len(titel) <= 160) or not _TS.match(start) or not _TS.match(ende):
        return "Termin ungueltig (Titel 3-160 Zeichen, Zeiten wie 2026-10-28T11:00:00+01:00)."
    nonce = secrets.token_hex(16)
    d = {k: v for k, v in _laden().items() if v.get("expires", 0) > time.time()}
    d[nonce] = {"expires": time.time() + _TTL,
                "payload": {"title": titel, "start": start, "end": ende, "timezone": "Europe/Berlin",
                            "request_id": uuid.uuid4().hex, "description": str(beschreibung)[:300]}}
    _speichern(d)
    if send_kb is None:
        import jack_telegram as tg
        send_kb = tg.send_keyboard
    send_kb("Kalender: \"%s\"\n%s bis %s\nEintragen? (10 Minuten gueltig)" % (titel, start.replace("T", " ")[:16], ende[11:16]),
                     [[("Ja, eintragen", "tm:ok:" + nonce), ("Abbrechen", "tm:no:" + nonce)]])
    return "Knopf an Dima geschickt."


def confirm(data, chat, user, trusted):
    m = re.fullmatch(r"tm:(ok|no):([0-9a-f]{32})", str(data or ""))
    if not m:
        return None
    if not _authed(chat, user, trusted):
        return "Termin: fremder Absender, abgelehnt"
    art, nonce = m.groups()
    d = _laden()
    item = d.pop(nonce, None)
    _speichern(d)
    if not item:
        return "Termin: Knopf nicht mehr gueltig"
    if item.get("expires", 0) <= time.time():
        return "Termin: Knopf abgelaufen, nichts eingetragen"
    if art == "no":
        return "Termin abgebrochen, nichts eingetragen"
    try:
        import jack_n8n
        r = jack_n8n.webhook("kalender", item["payload"], confirmed=True)
    except Exception as e:
        return "Termin: Fehler (%s), NICHT blind wiederholen" % type(e).__name__
    if r.get("ok"):
        return "Steht im Google-Kalender: \"%s\" (event_id %s...)" % (item["payload"]["title"], r["event_id"][:8])
    return "Termin NICHT bestaetigt (%s). Bitte im Kalender nachsehen, nicht blind wiederholen." % r.get("reason")
