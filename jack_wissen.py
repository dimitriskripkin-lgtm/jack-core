#!/usr/bin/env python3
"""jack_wissen.py - Wissens-Auskunft (Kap 281). Rein deterministisch, kein LLM.

Beantwortet Wissensfragen ueber JACK selbst ("Was weisst du ueber X?", "Wie funktioniert der X?", "Was ist X?") mit einem
woertlichen Auszug aus dem Betriebshandbuch plus Kapitelnummer. Kein brauchbarer Treffer -> "Dazu steht nichts im Handbuch."
(nur bei Fragen im JACK-Bereich), sonst None (Frage geht den alten Weg).

Festlegungen (vorregistriert 12.10.2026, talk_vorregistrierung.md):
- Ausloeser: starke ("was weisst du ueber", "wie funktioniert der/die/das ...", "was macht ...", "erklaer mir ...", "wozu dient ...")
  und schwache ("was ist/sind ..."). Fragen mit unbestimmtem Artikel (ein/eine ...) sind Allgemeinwissen, kein JACK-Bereich:
  Treffer ja, aber nie die Nichts-Antwort.
- Treffer: Kapitel mit Titel-/Dateinamen-Treffer eines Begriffs, oder mindestens zwei Begriffe im selben Absatz. Rang nach
  4*Titeltreffer + 2*bester Absatz + Begriffe im Kapitel. Auszug = bester Absatz, woertlich (gekuerzt), nie umformuliert.
- Starker Ausloeser ohne Treffer -> "Dazu steht nichts im Handbuch." Schwacher Ausloeser ohne Treffer -> None.
- Absaetze mit Geheimnismustern werden nie ausgegeben.
v2 (14.10.2026, Kap 281): JACK-Bezug-Gate vor der Suche (A: jack/dein*/bei dir; B: JACK-Eigenname oder Wortpaar aus
  Kapitel-/Modulname). Ohne Bezug -> None. Mehrdeutige Einzelwoerter oeffnen das Gate nie. Synonyme nur fuer die Suche.
"""
import math
import os
import re

MODULE_VERSION = 2
J = "/data/data/com.termux/files/home/jack"
HB = os.path.join(J, "BETRIEBSHANDBUCH")
AUS = os.path.join(os.path.expanduser("~"), "jack", ".wissen_off")  # Arena-Schalter: Datei da = alter Arm (Auskunft aus)
NICHTS = "Dazu steht nichts im Handbuch."
REST_SATZ = "Zum Rest der Frage habe ich keine belegten Angaben."
MAXLEN = 420

STARK_A = ("was weisst du ueber ", "weisst du etwas ueber ", "was weisst du von ", "was weisst du zu ")
STARK_B = ("wie funktioniert ", "wie arbeitet ", "was macht ", "was machen ", "erklaer mir ", "erklaere mir ", "erklaer ", "wozu dient ",
           "wofuer ist ", "wozu ist ", "was kann ", "was koennen ")
SCHWACH = ("was ist ", "was sind ", "was war ", "was waren ")
FRAGEWORT = ("wie", "wer", "warum", "wann", "wo", "was", "wieso", "weshalb", "wieviel", "welche", "welcher", "wodurch", "womit",
             "war", "waren", "hatte", "hat", "ist", "sind", "gab", "kann", "kommt", "kommen")
UNBESTIMMT = ("ein", "eine", "einen", "einem", "eines", "einer")
STOP = set("""was wie wer wo wann warum wieso weshalb welche welcher welches wieviel viel weisst du dir dich ueber von zu zur zum der die das
den dem des ein eine einen einem eines einer und oder auch noch schon jetzt eigentlich mal bitte bei im in am an auf aus mit fuer
macht machen kann koennen funktioniert funktionieren arbeitet erklaer erklaere mir mich ist sind war waren dient ueber etwas
jack handbuch teil sache thema ding kram so denn dann wohl gerade jacks dein deine deinem deinen deiner deines""".split())
# v2 (14.10.2026, JACK_TUNE_WISSEN2): JACK-Bezug-Gate vor der Suche. Ohne Bezug -> None (alter Weg).
DEIN = {"dein", "deine", "deinem", "deinen", "deiner", "deines"}
EIGENNAMEN = {"haliza", "kortex", "cortex", "overmind", "selbstmodell", "autolearn", "xibreaker"}
SYN = {"hitzeschutz": "heat", "ueberhitzung": "heat", "fokus": "focus", "totmannschalter": "deadman", "totmann": "deadman",
       "kortex": "cortex"}  # nur Suche, oeffnet nie das Gate
SECRET_RE = re.compile(r"(AIza[0-9A-Za-z_\-]{20,}|gh"  # getrennt, damit der Publish-Scanner das Muster nicht als Schluessel liest
                       r"p_[0-9A-Za-z]{20,}|sk-[0-9A-Za-z_\-]{20,}|xox[abp]-[0-9A-Za-z\-]{10,}"
                       r"|Bearer\s+[0-9A-Za-z_\-\.]{20,}|[0-9a-fA-F]{40,}|(?-i:(?=[A-Za-z0-9+/]*[A-Z])(?=[A-Za-z0-9+/]*[a-z])(?=[A-Za-z0-9+/]*\d)[A-Za-z0-9+/]{40,}={0,2})"
                       r"|(token|passwort|password|secret|api[_ ]?key)\s*[:=]\s*\S{8,}|-----BEGIN [A-Z ]*KEY)", re.I)

_cache = {"sig": None, "chapters": [], "paare": set()}


def norm(text):
    t = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        t = t.replace(a, b)
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return " ".join(t.split())


def plain(s):
    """Markdown-Zeichen weg, Leerraum vereinheitlichen (fuer Auszug und Woertlichkeitspruefung)."""
    s = re.sub(r"[*`_#>]+", " ", s or "")
    return " ".join(s.split())


def _sig():
    try:
        names = sorted(n for n in os.listdir(HB) if n.endswith(".md"))
        return (len(names), max((os.path.getmtime(os.path.join(HB, n)) for n in names), default=0))
    except OSError:
        return None


def stamm(w):
    for suf in ("ungen", "ung", "en", "er", "es", "e", "n", "s"):
        if len(w) > len(suf) + 4 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def toks(text):
    return {stamm(w) for w in text.split() if len(w) >= 3}


def lade():
    sig = _sig()
    if sig is not None and sig == _cache["sig"]:
        return _cache["chapters"]
    chs = []
    for n in sorted(os.listdir(HB)):
        if not n.endswith(".md"):
            continue
        try:
            with open(os.path.join(HB, n), encoding="utf-8", errors="ignore") as f:
                raw = f.read()
        except OSError:
            continue
        stem = n[:-3]
        m = re.match(r"(\d+)", stem)
        num = m.group(1) if m else stem
        title = norm((raw.splitlines() or [""])[0].replace("_", " ") + " " + stem.replace("_", " "))
        paras = []
        for p in re.split(r"\n\s*\n", raw):
            pp = plain(p)
            if len(pp) >= 40 and not SECRET_RE.search(p):
                paras.append((pp, toks(norm(pp))))
        if not paras and not SECRET_RE.search(raw):
            pp = plain(raw)
            if pp:
                paras.append((pp, toks(norm(pp))))
        allt = set()
        for _, ts in paras:
            allt |= ts
        chs.append({"stem": stem, "num": num, "title": toks(title), "paras": paras, "size": len(raw), "all": allt})
    df = {}
    for c in chs:
        for t in c["all"] | c["title"]:
            df[t] = df.get(t, 0) + 1
    paare = set()
    namen = [re.sub(r"^\d+_", "", c["stem"]) for c in chs]
    try:
        namen += [n[5:-3] for n in os.listdir(J) if n.startswith("jack_") and n.endswith(".py")]
    except OSError:
        pass
    for nm in namen:
        teile = norm(nm.replace("_", " ")).split()
        for a, b in zip(teile, teile[1:]):
            if len(a) >= 3 and len(b) >= 3:
                paare.add((a, b))
    _cache["sig"], _cache["chapters"], _cache["df"], _cache["n"], _cache["paare"] = sig, chs, df, len(chs), paare
    return chs


def _hat(ts, tokset):
    if ts in tokset:
        return True
    if len(ts) >= 6:
        return any(t.startswith(ts) or (len(t) >= 6 and ts.startswith(t)) for t in tokset)
    return False


def idf(ts):
    return math.log((_cache["n"] + 1.0) / (_cache["df"].get(ts, 0) + 1.0)) + 1.0


def erste_teilfrage(text):
    low = (text or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        low = low.replace(a, b)
    m = re.search(r"(?:,|\bund\b|\boder\b)\s*(?:" + "|".join(FRAGEWORT) + r")\b", low)
    if m:
        return norm(low[:m.start()]), True
    return norm(low), False


def begriffe(kopf):
    out = []
    for w in kopf.split():
        if len(w) >= 3 and w not in STOP and not w.isdigit() and w not in out:
            out.append(w)
    return out


def art(kopf):
    """('stark'|'schwach'|None, jack_bereich). jack_bereich False bei unbestimmtem Artikel direkt nach dem Ausloeser."""
    k = kopf + " "
    for a in STARK_A:
        if k.startswith(a):
            return "stark", True
    for a in STARK_B + SCHWACH:
        if k.startswith(a):
            rest = k[len(a):].split()[:3]
            allgemein = "eigentlich" in rest or (bool([w for w in rest if w != "eigentlich"]) and [w for w in rest if w != "eigentlich"][0] in UNBESTIMMT)
            if allgemein:  # Allgemeinwissen-Formulierung: wie schwacher Ausloeser (Titeltreffer Pflicht, nie die Nichts-Antwort)
                return "schwach", False
            return ("stark" if a in STARK_B else "schwach"), True
    return None, False


def bezug(kopf):
    """'A' expliziter Bezug, 'B' eindeutige JACK-Entitaet, None sonst (mehrdeutige Einzelwoerter reichen nie)."""
    w = kopf.split()
    if any(t in ("jack", "jacks") or t in DEIN for t in w) or " bei dir" in " " + kopf + " " or " von dir" in " " + kopf + " ":
        return "A"
    if any(t in EIGENNAMEN for t in w):
        return "B"
    lade()
    if any(p in _cache["paare"] for p in zip(w, w[1:])):
        return "B"
    return None


def suche(text, n=2, streng=False):
    """Rangliste [(punkte, kapitel, absatz)], leer wenn kein brauchbarer Treffer. streng: Titeltreffer Pflicht (schwache Ausloeser)."""
    kopf, _ = erste_teilfrage(text)
    roh = begriffe(kopf)
    terms = [stamm(w) for w in roh]
    if not terms:
        return []
    lade()
    alt = {stamm(w): stamm(SYN[w]) for w in roh if w in SYN}
    def hat(t, ts):
        return _hat(t, ts) or (t in alt and _hat(alt[t], ts))
    def gw(t):
        return idf(alt[t]) if t in alt else idf(t)
    mass = sum(gw(t) for t in terms)
    res = []
    for c in lade():
        tt = [t for t in terms if hat(t, c["title"])]
        inch = [t for t in terms if hat(t, c["all"]) or t in tt]
        best, bp, bn = 0.0, None, 0
        for pp, pt in c["paras"]:
            hit = [t for t in terms if hat(t, pt)]
            sc = sum(gw(t) for t in hit)
            if sc > best:
                best, bp, bn = sc, pp, len(hit)
        if best == 0:
            if not tt or not c["paras"]:
                continue
            bp = c["paras"][0][0]
        frac = sum(gw(t) for t in inch) / mass
        ok = (tt or bn >= 2) and frac >= 0.5
        if streng and not tt:
            ok = False
        if not ok:
            continue
        score = sum(gw(t) * (3 * (t in tt) + 1) for t in inch) + 2 * best
        res.append((score, c["size"], c, bp))
    res.sort(key=lambda x: (-x[0], -x[1]))
    return [(p, c, bp) for p, _, c, bp in res[:n]]


def kuerzen(p):
    if len(p) <= MAXLEN:
        return p
    cut = p[:MAXLEN]
    m = list(re.finditer(r"[.!?](?=\s)", cut))
    if m and m[-1].end() > MAXLEN * 0.5:
        return cut[:m[-1].end()]
    return cut.rsplit(" ", 1)[0] + " [...]"


def erkennt(text):
    if os.path.exists(AUS):
        return False
    kopf, _ = erste_teilfrage(text)
    typ, jack = art(kopf)
    if typ is None:
        return False
    bz = bezug(kopf)
    if bz is None:
        return False
    if bz == "A" and typ == "schwach" and jack:
        typ = "stark"
    if suche(text, 1, streng=(typ == "schwach")):
        return True
    return typ == "stark" and jack


def antwort(text):
    if os.path.exists(AUS):
        return None
    kopf, rest = erste_teilfrage(text)
    typ, jack = art(kopf)
    if typ is None:
        return None
    bz = bezug(kopf)
    if bz is None:
        return None
    if bz == "A" and typ == "schwach" and jack:
        typ = "stark"
    hits = suche(text, 2, streng=(typ == "schwach"))
    if hits:
        p, c, bp = hits[0]
        s = "%s\n(Handbuch Kap %s)" % (kuerzen(bp), c["num"])
        if len(hits) > 1 and hits[1][0] >= 0.8 * p and hits[1][1]["num"] != c["num"]:
            s += " Siehe auch Kap %s." % hits[1][1]["num"]
    elif typ == "stark" and jack:
        s = NICHTS
    else:
        return None
    if rest:
        s += "\n" + REST_SATZ
    return s


if __name__ == "__main__":
    import sys
    print(antwort(" ".join(sys.argv[1:])) or "(keine Wissensfrage)")
