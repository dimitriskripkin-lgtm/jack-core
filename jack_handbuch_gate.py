#!/usr/bin/env python3
"""JACK_TUNE_HBGATE: Handbuch-Pflicht fuer jede KI, die ueber MCP schreibt.
Stateless: Quittung = sha256(Schluessel+Tag)[:8]. Sie steht nur in der Ablehnung
(START-Regeln + Kapitelauszug), wer sie hat, hat die Texte im Kontext gehabt.
Fail-open: jeder interne Fehler laesst den Aufruf durch (nie den MCP-Kanal blockieren)."""
import os, re, json, time, hashlib

J = os.environ.get("JACK_HB_HOME", "/data/data/com.termux/files/home/jack")
HB = J + "/BETRIEBSHANDBUCH"
START = J + "/00_START_HIER.md"

INSTRUCTIONS = ("JACK: ERST start_hier(wer=\"claude|grok|gemini\") aufrufen und lesen (dein Arbeitsplatz-Buero ist dabei) (Wahrheitsrangfolge, Pflichtablauf, eiserne Regeln). "
                "Vor jeder Aenderung an einem Modul das Betriebshandbuch-Kapitel lesen (handbuch_index / handbuch_kapitel). "
                "Schreibende create_mission-Aufrufe verlangen extra.quittung, die steht in der Ablehnungsmeldung. "
                "Honor-Live-Datei ist Wahrheit, GitHub kann stale sein. Nichts neu bauen, was es schon gibt.")

def _rd(p, n=None):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            t = f.read()
        return t if n is None else t[:n]
    except Exception:
        return ""

def quittung(key):
    return hashlib.sha256(("JACKGATE|%s|%s" % (key, time.strftime("%Y-%m-%d"))).encode()).hexdigest()[:8]

_cache = {"mt": None, "map": {}, "idx": []}

def _nr(f):
    m = re.match(r"(\d+)", f)
    return int(m.group(1)) if m else 9999

def _scan():
    try:
        mt = os.path.getmtime(HB)
    except Exception:
        return
    if _cache["mt"] == mt and _cache["idx"]:
        return
    mp, idx = {}, []
    files = [f for f in os.listdir(HB) if f.endswith(".md") and f[0].isdigit()]
    for f in sorted(files, key=lambda x: (_nr(x), x)):
        txt = _rd(os.path.join(HB, f), 6000)
        lines = [l for l in txt.splitlines() if l.strip()]
        heads = [l for l in lines[:12] if l.lstrip().startswith("#")]
        title = heads[-1] if heads else (lines[0] if lines else f)
        for h in heads:
            for m in re.findall(r"[A-Za-z0-9_]+\.py", h):
                mp.setdefault(m, []).append(f)
        zweck = ""
        for l in lines[:25]:
            if l.lstrip().startswith("**Zweck"):
                zweck = re.sub(r"\*+", "", l.split("Zweck", 1)[1]).strip(" :")[:90]
                break
        if not zweck and len(lines) > 1:
            zweck = lines[1][:90]
        idx.append((f, title.lstrip("# ").strip()[:60], zweck))
    _cache.update({"mt": mt, "map": mp, "idx": idx})

def kapitel_alle(fname):
    _scan()
    return _cache["map"].get(os.path.basename(str(fname)), [])

def kapitel_fuer(fname):
    l = kapitel_alle(fname)
    return l[0] if l else None

def start_text():
    t = _rd(START)
    if not t:
        t = "00_START_HIER.md fehlt im JACK-Ordner. Melde das Dima."
    return json.dumps({"start_hier": t, "quittung_start": quittung("START"),
        "naechster_schritt": "Vor einer Moduländerung: handbuch_kapitel('<modul>.py') lesen. Schreibende Missions brauchen extra.quittung."},
        ensure_ascii=False)

def index(suche=""):
    _scan()
    s = (suche or "").lower()
    rows = ["%s | %s | %s" % r for r in _cache["idx"] if not s or s in (r[0] + r[1] + r[2]).lower()]
    return json.dumps({"n": len(rows), "von": len(_cache["idx"]), "zeilen": rows[:400]}, ensure_ascii=False)

def kapitel(name):
    _scan()
    name = str(name or "").strip()
    f = kapitel_fuer(name)
    if not f:
        for r in _cache["idx"]:
            if name and (name == r[0] or name in r[0] or name in r[1]):
                f = r[0]
                break
    if not f:
        return json.dumps({"error": "kein Kapitel gefunden fuer: " + name, "tipp": "handbuch_index(suche)"}, ensure_ascii=False)
    return json.dumps({"kapitel": f, "weitere_kapitel": [x for x in kapitel_alle(name) if x != f], "text": _rd(os.path.join(HB, f), 12000), "quittung": quittung(f)}, ensure_ascii=False)

PATCH_ACTS = ("py_replace", "sed_replace")

def gate(act, extra_d):
    """None = durchlassen, dict = Ablehnung."""
    try:
        import jack_acts
        a = jack_acts.ACTS.get(act, {})
        if not a.get("freigabe"):
            return None
        key, kap = "START", None
        if act in PATCH_ACTS:
            kap = kapitel_fuer(extra_d.get("file", ""))
            if kap:
                key = kap
        want = quittung(key)
        if str(extra_d.get("quittung", "")).strip().lower() == want:
            return None
        return {
            "error": "GATE: Betriebshandbuch zuerst (JACK_TUNE_HBGATE). Nichts wurde ausgefuehrt.",
            "warum": "Sessions vergessen den Stand. Beispiel 07.10.2026: Git-Takt gedrosselt, ohne Kapitel 01 zu lesen (.mission_boost/Poll-Logik uebersehen).",
            "so_gehts": "Lies Auszug unten (voll: start_hier(), handbuch_kapitel). Dann denselben Aufruf wiederholen mit extra-Feld \"quittung\": \"%s\"." % want,
            "quittung": want,
            "kapitel": kap,
            "weitere_kapitel": [x for x in kapitel_alle(extra_d.get("file", "")) if x != kap] if kap else [],
            "start_auszug": _rd(START, 2600),
            "kapitel_auszug": _rd(os.path.join(HB, kap), 3500) if kap else "(kein Kapitel fuer dieses Ziel gefunden - START gilt)",
        }
    except Exception:
        return None
