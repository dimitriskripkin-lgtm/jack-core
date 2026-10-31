#!/usr/bin/env python3
"""jack_befehle.py - JACK_TUNE_BEFEHLE (Kap 303, 24.10.2026): "Kannst du X?" und "Welche Befehle hast du?"
deterministisch aus einer festen Liste beantworten, statt das Sprachmodell raten zu lassen.
Nur Befehle, die jack_telegram.py (bzw. jack_linkinbox) am 24.10. wirklich behandelt. Schalter ~/jack/.befehle_off.
"""
import os
import re

AUS = "/data/data/com.termux/files/home/jack/.befehle_off"
# (Befehl, Bedeutung, Stichwoerter als ganze Woerter/Stamm-Anfaenge)
BEFEHLE = [
    ("/standort", "holt den GPS-Standort", ("standort", "gps", "ort", "wo bin ich")),
    ("/akku", "zeigt Akku und Temperatur", ("akku", "batterie")),
    ("/status", "zeigt den Systemstatus", ("status", "zustand")),
    ("/lage", "zeigt das Lagebild (Fahrmodus, Bluetooth)", ("lage", "lagebild", "fahrmodus", "bluetooth")),
    ("/timer", "stellt einen Timer, z. B. /timer 10 Nudeln", ("timer", "wecker")),
    ("/musik", "steuert die Musik: pause, play, weiter", ("musik", "spotify", "lied", "song", "pause")),
    ("/agent", "bedient das Xiaomi per KI (Einstellungen, Chrome, Termux)", ("agent", "bedienen", "chrome")),
    ("/scan", "macht einen Vollscan", ("scan", "scannen")),
    ("/selftest", "macht den Selbsttest", ("selbsttest", "selftest")),
    ("/sensor", "liest die Sensoren", ("sensor", "sensoren", "temperatur")),
    ("/budget", "zeigt das Gemini-Budget", ("budget", "kosten", "geld", "guthaben")),
    ("/vorschlaege", "zeigt offene Verbesserungsvorschlaege", ("vorschlag", "vorschlaege", "verbesserung")),
    ("/links", "zeigt die letzten geteilten Video-Links", ("link", "links", "video", "videos", "tiktok", "youtube", "instagram")),
    ("/befehle", "zeigt alle Befehle", ()),
]


def _norm(text):
    t = str(text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return " ".join(re.findall(r"[a-z0-9]+", t))


def _treffer(t):
    w = t.split()
    out = []
    for cmd, was, keys in BEFEHLE:
        for k in keys:
            if (" " in k and k in t) or any(x == k or (len(k) >= 5 and x.startswith(k)) for x in w):
                out.append((cmd, was))
                break
    return out


def _liste_frage(t):
    return bool(re.search(r"\b(welche|alle|deine|liste)\b.*\bbefehle\b|\bbefehlsliste\b|\bwelche kommandos\b", t))


# JACK_TUNE_Z2B_KURZLISTE: ein read-only Weg fuer Telegram und Chat-Router.
VORSCHLAG_DIR = "/data/data/com.termux/files/home/jack/missions/proposals/pending"

def vorschlaege_kurzliste(pdir=None):
    """Die vorhandenen Telegram-Proposals, maximal fuenf, niemals freigeben."""
    import json
    from pathlib import Path
    root = Path(pdir if pdir is not None else VORSCHLAG_DIR)
    if not root.is_dir() or root.is_symlink():
        return "VORSCHLAEGE: keine offen"
    items = []
    for path in sorted(root.iterdir()):
        if path.suffix != ".json" or not path.is_file() or path.is_symlink():
            continue
        try:
            if path.stat().st_size > 65536:
                continue
            with path.open(encoding="utf-8") as inp:
                value = json.load(inp)
            if isinstance(value, dict):
                items.append(value)
        except (OSError, ValueError, TypeError):
            continue
    if not items:
        return "VORSCHLAEGE: keine offen"
    lines = ["VORSCHLAEGE (%d offen):" % len(items)]
    for it in items[:5]:
        ident = str(it.get("id", "?")).replace("\n", " ")[:60]
        problem = str(it.get("problem", "")).replace("\n", " ")[:100]
        lines.append("- %s: %s" % (ident, problem))
    if len(items) > 5:
        lines.append("Weitere: %d" % (len(items) - 5))
    lines.append("Details: /vorschau <id>. Freigabe nur mit /freigeben <id>.")
    return "\n".join(lines)


def _vorschlag_hilfe(t):
    return bool(re.fullmatch(
        r"(?:(?:zeig(?:e)? mir|gib mir|nenne|hast du|gibt es|wo sind|"
        r"wo finde ich|wie sehe ich|welche sind die|welche sind|ich will|ich moechte)\s+)?"
        r"(?:(?:deine|die|meine|offenen|offene|neuen|neue|aktuellen|aktuelle)\s+)?"
        r"(?:verbesserungsvorschlaege|verbesserungsvorschlag|vorschlaege|vorschlag)"
        r"(?:\s+(?:fuer|zu|von)\s+(?:jack|deinen code|meinen code|dein system))?", t))


def erkennt(text):
    if os.path.exists(AUS):
        return False
    t = _norm(text)
    if _liste_frage(t) or _vorschlag_hilfe(t):
        return True
    # "kannst du ..." / "hast du zugriff auf ..." mit erkennbarem Befehl
    if re.match(r"^(kannst|koenntest|hast) du\b", t) and _treffer(t):
        return True
    return False


def antwort(text):
    if not erkennt(text):
        return None
    t = _norm(text)
    if _vorschlag_hilfe(t):
        return vorschlaege_kurzliste()
    if _liste_frage(t):
        return "Meine Befehle: " + "; ".join("%s %s" % (c, w) for c, w, _ in BEFEHLE)
    tr = _treffer(t)
    if len(tr) == 1 and tr[0][0] == "/vorschlaege":
        return vorschlaege_kurzliste()
    if len(tr) == 1:
        c, w = tr[0]
        return "Ja, dafür gibt es %s: %s." % (c, w)
    return "Ja, dafür passen: " + "; ".join("%s %s" % (c, w) for c, w in tr[:3]) + "."


if __name__ == "__main__":
    import sys
    print(antwort(" ".join(sys.argv[1:])) or "(keine Befehlsfrage)")
