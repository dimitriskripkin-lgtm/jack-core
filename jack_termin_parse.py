"""JACK_TUNE_TERMINTEXT (27.10.2026, Claude, Kap 307): erkennt Termine in Dimas Text/Sprache.
erkenne(text, jetzt) -> dict(titel, start, ende) oder None. Nur bei eindeutigem Tag UND Uhrzeit.
Ausgeloest wird nur, wenn der Satz mit einem Tag beginnt (heute/morgen/uebermorgen/Wochentag/am TT.MM.)
oder ein Termin-Wort enthaelt (Termin, Kalender, eintragen). Fragen werden ignoriert.
Ergebnis ist nur ein VORSCHLAG: eingetragen wird erst nach Dimas Knopf (jack_termin).
"""
import re
from datetime import datetime, timedelta

_ZAHL = {"eins": 1, "ein": 1, "eine": 1, "zwei": 2, "drei": 3, "vier": 4, "fünf": 5, "fuenf": 5, "sechs": 6,
         "sieben": 7, "acht": 8, "neun": 9, "zehn": 10, "elf": 11, "zwölf": 12, "zwoelf": 12,
         "dreizehn": 13, "vierzehn": 14, "fünfzehn": 15, "fuenfzehn": 15, "sechzehn": 16, "siebzehn": 17,
         "achtzehn": 18, "neunzehn": 19, "zwanzig": 20, "einundzwanzig": 21, "zweiundzwanzig": 22,
         "dreiundzwanzig": 23}
_WT = {"montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3, "freitag": 4, "samstag": 5, "sonntag": 6}
_ZW = r"(\d{1,2}|" + "|".join(sorted(_ZAHL, key=len, reverse=True)) + r")"
_TRIGGER = re.compile(r"\b(termin|kalender|eintragen|trag\w*)\b", re.I)


def _z(w):
    w = w.lower()
    return int(w) if w.isdigit() else _ZAHL.get(w)


def _tag(t, jetzt):
    s = t.lower()
    if re.search(r"\bübermorgen\b|\buebermorgen\b", s):
        return jetzt.date() + timedelta(days=2), r"\b(übermorgen|uebermorgen)\b"
    if re.search(r"\bmorgen\b", s) and not re.search(r"\bmorgens\b", s.split("morgen", 1)[0] + "x"):
        return jetzt.date() + timedelta(days=1), r"\bmorgen\b"
    if re.search(r"\bheute\b", s):
        return jetzt.date(), r"\bheute\b"
    m = re.search(r"\bam\s+(\d{1,2})\.\s*(\d{1,2})\.?(?:\s*(\d{4}))?", s)
    if m:
        j = int(m.group(3) or jetzt.year)
        try:
            d = datetime(j, int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            return None, None
        if not m.group(3) and d < jetzt.date():
            d = d.replace(year=j + 1)
        return d, re.escape(m.group(0))
    m = re.search(r"\b(?:am\s+|nächsten\s+|naechsten\s+)?(" + "|".join(_WT) + r")\b", s)
    if m:
        delta = (_WT[m.group(1)] - jetzt.weekday()) % 7 or 7
        return jetzt.date() + timedelta(days=delta), re.escape(m.group(0))
    return None, None


def _zeit(t):
    s = t.lower()
    m = re.search(r"\bum\s+halb\s+" + _ZW + r"\b", s)
    if m and _z(m.group(1)):
        return (_z(m.group(1)) - 1) % 24, 30, m.group(0)
    m = re.search(r"\bum\s+viertel\s+nach\s+" + _ZW + r"\b", s)
    if m and _z(m.group(1)) is not None:
        return _z(m.group(1)), 15, m.group(0)
    m = re.search(r"\bum\s+viertel\s+vor\s+" + _ZW + r"\b", s)
    if m and _z(m.group(1)):
        return (_z(m.group(1)) - 1) % 24, 45, m.group(0)
    m = re.search(r"\bum\s+(\d{1,2})[:.](\d{2})\s*(?:uhr)?\b", s)
    if m:
        return int(m.group(1)), int(m.group(2)), m.group(0)
    m = re.search(r"\bum\s+" + _ZW + r"(?:\s+uhr)?(?:\s+" + _ZW + r")?\b", s)
    if m and _z(m.group(1)) is not None:
        mi = _z(m.group(2)) if m.group(2) and "uhr" in m.group(0) else 0
        return _z(m.group(1)), mi or 0, m.group(0)
    return None


def erkenne(text, jetzt=None):
    t = str(text or "").strip()
    if not t or t.endswith("?") or len(t) > 200:
        return None
    jetzt = jetzt or datetime.now()
    tag, tag_rx = _tag(t, jetzt)
    z = _zeit(t)
    if not tag or not z:
        return None
    beginnt_mit_tag = re.match(r"^\s*(jack[,!:]?\s*)?(heute|morgen|übermorgen|uebermorgen|am\s|nächsten|naechsten|" + "|".join(_WT) + r")", t, re.I)
    if not (beginnt_mit_tag or _TRIGGER.search(t)):
        return None
    h, mi, zeit_txt = z
    s = t.lower()
    if re.search(r"\b(abends|nachmittags|am abend|am nachmittag)\b", s) and h < 12:
        h += 12
    elif 1 <= h <= 6 and not re.search(r"\b(morgens|früh|frueh|nachts|in der nacht)\b", s):
        h += 12  # "um vier" fuer einen Termin meint fast immer 16 Uhr; der Knopf zeigt die Zeit zur Kontrolle
    if not (0 <= h <= 23 and 0 <= mi <= 59):
        return None
    titel = t
    for rx in (tag_rx, re.escape(zeit_txt), r"\b(jack|termin|kalender|bitte|eintragen|trag\w*|ein|eine|einen|einer|im|in den|abends|nachmittags|morgens|früh|frueh|uhr|stell\w*|mach\w*|leg\w*|setz\w*|erstell\w*|mir|mich|uns|für|fuer|an|neue|neuen)\b"):
        titel = re.sub(rx, " ", titel, flags=re.I)
    titel = re.sub(r"[\s,.:!]+", " ", titel).strip(" ,.:!")
    if len(titel) < 3:
        titel = "Termin"
    titel = titel[0].upper() + titel[1:]
    start = datetime(tag.year, tag.month, tag.day, h, mi)
    ende = start + timedelta(hours=1)
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Berlin")
        a, b = start.replace(tzinfo=tz), ende.replace(tzinfo=tz)
    except Exception:
        return None  # ohne Zeitzonendaten lieber kein Vorschlag als eine falsche Uhrzeit
    return {"titel": titel[:160], "start": a.isoformat(timespec="seconds"), "ende": b.isoformat(timespec="seconds")}
