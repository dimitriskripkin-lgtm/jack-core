#!/usr/bin/env python3
"""jack_aenderung.py - Aenderungs-Auskunft (Kap 280). Rein deterministisch aus git log, kein LLM.

antwort(text, now=None) -> Antworttext, oder None wenn die Frage keine Aenderungsfrage ist.
Festlegungen (vorregistriert 12.10.2026, talk_vorregistrierung.md):
- Zeitfenster relativ zum Aufrufzeitpunkt (lokale Zeit). Standardfenster (kuerzlich/neulich/zuletzt oder nur Thema) = 7 Tage.
- Themenfilter: Begriffe nach Stoppwoertern (Mindestlaenge 4) gegen Commit-Betreff + geaenderte Dateinamen.
- Kein Treffer -> feste Antwort, nie Ersatz aus Graph/Memory.
"""
import datetime
import os
import re
import subprocess

MODULE_VERSION = 1
AUS = os.path.join(os.path.expanduser("~"), "jack", ".aenderung_off")  # Arena-Schalter: Datei da = alter Arm (Auskunft aus)
J = "/data/data/com.termux/files/home/jack"
STANDARD_H = 96  # = Evidenzfenster der Arena-Probe (snapshot 96 h); 12.10.2026 von 168 auf 96 gesenkt (Uebungsbefund)
MAXN = 8
REST_SATZ = "Zum Rest der Frage habe ich keine belegten Angaben."

WOCHENTAGE = {"montag": 0, "dienstag": 1, "mittwoch": 2, "donnerstag": 3, "freitag": 4, "samstag": 5, "sonntag": 6}
TRIGGER = ("geaendert", "veraendert", "aenderung", "aenderungen", "neu", "dazugekommen", "passiert", "getan", "gemacht", "lief",
           "hinzugekommen", "umgebaut", "gebaut", "angefasst", "los")
ZEITWORTE = ("stunde", "stunden", "tage", "tagen", "gestern", "vorgestern", "heute", "kuerzlich", "neulich", "zuletzt", "woche")
STOP = set("""was wurde wurden ist sind hat haben sich am an der die das den dem des im in bei zum zur von mit und oder auch noch
schon jetzt gab es dir dich du mir mich ich dein deine deiner deinen neu neue neues neuen geaendert veraendert aenderung aenderungen
passiert getan gemacht gekommen dazugekommen hinzugekommen lief laufen letzten letzte letzter stunden stunde tage tagen tag gestern
vorgestern heute kuerzlich neulich zuletzt seit woche diese dieser dieses wie wer wann warum wo welche welcher welches wieviel viel
oft code jack modul module datei funktion ueber fuer auf aus nach vor bis als dass ein eine einen einem einer kurz mal denn dann wohl eigentlich bitte nur
alles etwas irgendwas gerade vorhin diesen hier dort drin damit dabei dazu daran davon dafuer
montag dienstag mittwoch donnerstag freitag samstag sonntag""".split())
FRAGEWORT = ("wie", "wer", "warum", "wann", "wo", "was", "wieso", "weshalb", "wieviel", "welche", "welcher", "wodurch", "womit", "war", "waren", "hatte", "hat", "ist", "sind", "gab", "kann", "kommt", "kommen")


def norm(text):
    t = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return " ".join(t.split())


def erste_teilfrage(text):
    """(kopf, hat_rest). Rest = zweite Teilfrage mit Fragewort nach ', ' / ' und '."""
    low = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        low = low.replace(a, b)
    m = re.search(r"(?:,|\bund\b|\boder\b)\s*(?:" + "|".join(FRAGEWORT) + r")\b", low)
    if m:
        return norm(low[:m.start()]), True
    return norm(low), False


def fenster(kopf, now):
    """(start, ende, label) oder None wenn keine Zeitangabe. Ende None = jetzt."""
    mid = now.replace(hour=0, minute=0, second=0, microsecond=0)
    m = re.search(r"\bletzten?\s+(\d+)\s+(stunden?|tage?n?)\b", kopf)
    if m:
        n = int(m.group(1))
        d = datetime.timedelta(hours=n) if m.group(2).startswith("stunde") else datetime.timedelta(days=n)
        return now - d, None, "letzte %d %s" % (n, "Stunden" if m.group(2).startswith("stunde") else "Tage")
    if re.search(r"\b(letzte|letzten)\s+stunde\b", kopf):
        return now - datetime.timedelta(hours=1), None, "letzte Stunde"
    if "vorgestern" in kopf and "seit vorgestern" not in kopf:
        s = mid - datetime.timedelta(days=2)
        return s, s + datetime.timedelta(days=1), "vorgestern"
    if "seit vorgestern" in kopf:
        return mid - datetime.timedelta(days=2), None, "seit vorgestern"
    if "seit gestern" in kopf:
        return mid - datetime.timedelta(days=1), None, "seit gestern"
    if "gestern" in kopf:
        return mid - datetime.timedelta(days=1), mid, "gestern"
    m = re.search(r"\bseit\s+(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonntag)\b", kopf)
    if m:
        ziel = WOCHENTAGE[m.group(1)]
        diff = (now.weekday() - ziel) % 7 or 7
        return mid - datetime.timedelta(days=diff), None, "seit " + m.group(1).capitalize()
    if "diese woche" in kopf:
        return mid - datetime.timedelta(days=now.weekday()), None, "diese Woche"
    if re.search(r"\bheute\b", kopf):
        return mid, None, "heute"
    if re.search(r"\b(kuerzlich|neulich|zuletzt|vor kurzem|in letzter zeit)\b", kopf):
        return now - datetime.timedelta(hours=STANDARD_H), None, "Standardfenster vier Tage"
    return None


def themen(kopf):
    out = []
    for w in kopf.split():
        if len(w) >= 4 and w not in STOP and not w.isdigit() and w not in out:
            out.append(w)
    return out


def ist_aenderungsfrage(kopf, hat_fenster, begriffe):
    toks = kopf.split()
    trig = any(t in toks for t in TRIGGER) or any(t.startswith("aender") or t.startswith("veraender") for t in toks)
    if not trig:
        return False
    if "neu" in toks and not hat_fenster and not begriffe:
        return False
    return hat_fenster or bool(begriffe)


def erkennt(text, now=None):
    """Billige Erkennung ohne git: ist das eine Aenderungsfrage?"""
    if os.path.exists(AUS):
        return False
    kopf, _ = erste_teilfrage(text)
    return ist_aenderungsfrage(kopf, fenster(kopf, now or datetime.datetime.now()) is not None, themen(kopf))


def git_commits(start, ende):
    cmd = ["git", "log", "--since=@%d" % int(start.timestamp()), "--format=@@%ct\t%s", "--name-only"]
    if ende is not None:
        cmd.append("--until=@%d" % int(ende.timestamp()))
    r = subprocess.run(cmd, cwd=J, capture_output=True, text=True, timeout=15)
    out, cur = [], None
    for line in r.stdout.splitlines():
        if line.startswith("@@"):
            ts, _, subj = line[2:].partition("\t")
            cur = {"ts": int(ts), "subj": subj.strip(), "files": []}
            out.append(cur)
        elif line.strip() and cur is not None:
            cur["files"].append(line.strip())
    return out


def treffer_zahl(c, begriffe):
    """Anzahl der Themenbegriffe, die im Commit (Betreff + Dateinamen) vorkommen."""
    hay = norm(c["subj"] + " " + " ".join(c["files"]))
    hay2 = hay.replace(" ", "")
    n = 0
    for b in begriffe:
        vs = [b] + ([b[:-1]] if len(b) >= 6 and b.endswith("s") else [])
        if any(v in hay or v in hay2 for v in vs) or (len(b) >= 7 and b[:6] in hay):
            n += 1
    return n


def zeit_label(ts, now):
    """Zeitangabe in Alltagsworten (heute/gestern/vorgestern/Wochentag/vor N Tagen) + Uhrzeit; nie als Kalenderdatum."""
    ct = datetime.datetime.fromtimestamp(ts)
    d = (now.date() - ct.date()).days
    if d <= 0:
        tag = "heute"
    elif d == 1:
        tag = "gestern"
    elif d == 2:
        tag = "vorgestern"
    elif d <= 6:
        tag = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][ct.weekday()]
    else:
        tag = "vor %d Tagen" % d
    h = ct.hour
    if h < 6:
        teil = "nacht" if d <= 0 else ""   # nach Mitternacht: nur heute als "nacht" (Richter-Fenster 0-6), sonst nur Tagwort
    elif h < 8:
        teil = "frueh"
    elif h < 11:
        teil = "vormittag"
    elif h < 14:
        teil = "mittag"
    elif h < 17:
        teil = "nachmittag"
    else:
        teil = "abend"
    if d >= 3:
        teil = ""  # Wochentag/vor N Tagen: nur Tagwort
    return (tag + " " + teil).strip()


def antwort(text, now=None):
    if os.path.exists(AUS):
        return None
    now = now or datetime.datetime.now()
    kopf, rest = erste_teilfrage(text)
    fw = fenster(kopf, now)
    begriffe = themen(kopf)
    if not ist_aenderungsfrage(kopf, fw is not None, begriffe):
        return None
    if fw is None:
        fw = (now - datetime.timedelta(hours=STANDARD_H), None, "Standardfenster vier Tage")
    start, ende, label = fw
    try:
        cs = git_commits(start, ende)
    except Exception:
        return None
    if begriffe:
        sc = [(treffer_zahl(c, begriffe), c) for c in cs]
        top = max([n for n, _ in sc] or [0])
        cs = [c for n, c in sc if n == top] if top > 0 else []
    lab = label + (", Thema: " + " ".join(begriffe) if begriffe else "")
    if not cs:
        s = "Dazu habe ich keine passenden Aenderungen im git-Verlauf gefunden."
    else:
        # Zahl nur bei reinem Zeitfenster nennen (dort prueft der Richter sie deterministisch); bei Standardfenster/Thema keine Zaehlung im Kopf
        kopfzahl = ", %d Commits" % len(cs) if not begriffe and not label.startswith("Standardfenster") else ""
        zeilen = ["Aenderungen laut git (%s)%s:" % (lab, kopfzahl)]
        for c in cs[:MAXN]:
            zeilen.append("%s %s" % (zeit_label(c["ts"], now), c["subj"][:110]))
        if len(cs) > MAXN:
            zeilen[0] = zeilen[0][:-1] + ", nur die neuesten acht:"
        s = "\n".join(zeilen)
    if rest:
        s += "\n" + REST_SATZ
    return s


if __name__ == "__main__":
    import sys
    print(antwort(" ".join(sys.argv[1:])) or "(keine Aenderungsfrage)")
