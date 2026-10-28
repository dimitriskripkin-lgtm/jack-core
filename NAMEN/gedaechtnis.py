#!/usr/bin/env python3
"""Gemeinsames Gedaechtnis fuer die Namensordner Grok, Tesla, Dimitri, Jack.

Kein jack-Modul. Nur Python-Standardbibliothek, kein Netzwerk, keine
Embeddings, kein Ollama.

Speicher: NAMEN/<Name>/erinnerungen.jsonl, nur anhaengend.
Jede Zeile ist entweder ein Eintrag (typ beobachtung/fakt) oder ein
Ereignis, das sich auf einen Eintrag bezieht (bestaetigung, status).
Zaehler und Status ergeben sich beim Lesen aus den Ereignissen, so muss
keine alte Zeile umgeschrieben werden.

Einzige Ausnahme: `aufraeumen`. Es verschiebt schwache Eintraege in
NAMEN/<Name>/attic/ (Attic statt rm). Vorher wird immer eine Sicherung
nach attic/sicherungen/ geschrieben; aeltere Sicherungen werden nicht
geloescht, sondern nach attic/sicherungen/archiv/ verschoben.

Konzepte (eigener Code, keine Kopie) aus: intertwine/grok-observational-memory,
PLRTCore/shadow-vault, Wolfe-Jam/grok-faf-voice, koreysmith123/recallsmith,
matthiasroder/grok-bot-learning. Siehe NAMEN/README.md.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import re
import shutil
import sys
import tempfile
import unicodedata

NAMEN = ("Grok", "Tesla", "Dimitri", "Jack")
EBENEN = ("konkret", "strukturell", "universell")
KURATOR = "Dimitri"
BASIS_STANDARD = os.path.dirname(os.path.abspath(__file__))
HALBWERTSZEIT_TAGE = 90.0
JACCARD_SCHWELLE = 0.8
SICHERUNGEN_BEHALTEN = 5
STOPPWOERTER = set("""der die das ein eine einer eines und oder aber nicht
kein keine ist sind war wird werden mit von zu zum zur im in am an auf fuer
fur aus bei als auch nur noch schon so wie was wer wo es er sie wir ich du
the a an and or of to in on for is are be""".split())


class GedaechtnisFehler(Exception):
    def __init__(self, meldung, code=1):
        super().__init__(meldung)
        self.meldung = meldung
        self.code = code


# ---------------------------------------------------------------- Hilfen

def jetzt_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def zeit_text(zeit=None):
    return (zeit or jetzt_utc()).strftime("%Y-%m-%dT%H:%M:%SZ")


def zeit_lesen(text):
    try:
        return datetime.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=datetime.timezone.utc)
    except (TypeError, ValueError):
        return None


def normalisieren(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = text.replace("ß", "ss")
    text = "".join(z for z in text if not unicodedata.combining(z))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(text.split())


def woerter(text):
    return {w for w in normalisieren(text).split()
            if len(w) > 1 and w not in STOPPWOERTER}


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / float(len(a | b))


def text_hash(text):
    return hashlib.sha256(normalisieren(text).encode("utf-8")).hexdigest()[:16]


def name_pruefen(name):
    for n in NAMEN:
        if n.lower() == (name or "").lower():
            return n
    raise GedaechtnisFehler("Unbekannter Name '%s'. Erlaubt: %s."
                            % (name, ", ".join(NAMEN)), 2)


# ---------------------------------------------------------------- Speicher

class Gedaechtnis:
    def __init__(self, name, basis=None, jetzt=None):
        self.name = name_pruefen(name)
        self.basis = os.path.abspath(basis or BASIS_STANDARD)
        self.ordner = os.path.join(self.basis, self.name)
        self.datei = os.path.join(self.ordner, "erinnerungen.jsonl")
        self.attic = os.path.join(self.ordner, "attic")
        self._jetzt = jetzt

    def jetzt(self):
        return self._jetzt or jetzt_utc()

    # -- Lesen

    def zeilen(self, datei=None):
        datei = datei or self.datei
        ergebnis = []
        if not os.path.exists(datei):
            return ergebnis
        with open(datei, "r", encoding="utf-8") as f:
            for nr, zeile in enumerate(f, 1):
                zeile = zeile.strip()
                if not zeile:
                    continue
                try:
                    ergebnis.append(json.loads(zeile))
                except ValueError:
                    sys.stderr.write("Hinweis: Zeile %d in %s unlesbar, "
                                     "uebersprungen.\n" % (nr, datei))
        return ergebnis

    def eintraege(self):
        """Faltet Eintraege und Ereignisse zum aktuellen Stand."""
        stand = {}
        reihenfolge = []
        for z in self.zeilen():
            typ = z.get("typ")
            if typ in ("beobachtung", "fakt"):
                e = dict(z)
                e.setdefault("zaehler", 1)
                e["zuletzt_utc"] = e.get("zeit_utc")
                if e["id"] not in stand:
                    reihenfolge.append(e["id"])
                stand[e["id"]] = e
            elif typ == "bestaetigung" and z.get("bezug") in stand:
                e = stand[z["bezug"]]
                e["zaehler"] = e.get("zaehler", 1) + 1
                e["zuletzt_utc"] = z.get("zeit_utc")
            elif typ == "status" and z.get("bezug") in stand:
                stand[z["bezug"]]["status"] = z.get("status")
        return [stand[i] for i in reihenfolge]

    def finden(self, eintrag_id):
        for e in self.eintraege():
            if e["id"] == eintrag_id:
                return e
        raise GedaechtnisFehler("Eintrag %s gibt es bei %s nicht."
                                % (eintrag_id, self.name), 3)

    # -- Schreiben (nur anhaengen)

    def _anhaengen(self, zeile):
        os.makedirs(self.ordner, exist_ok=True)
        with open(self.datei, "a", encoding="utf-8") as f:
            f.write(json.dumps(zeile, ensure_ascii=False, sort_keys=True)
                    + "\n")

    def _doppelt(self, text, typ):
        h = text_hash(text)
        w = woerter(text)
        for e in self.eintraege():
            if e.get("typ") != typ or e.get("status") == "widerrufen":
                continue
            if e.get("hash") == h or jaccard(w, woerter(e.get("text"))) \
                    >= JACCARD_SCHWELLE:
                return e
        return None

    def merken(self, text, beleg, typ="beobachtung", quelle="unbekannt",
               ebene="konkret", wichtigkeit=3, aus=None):
        text = (text or "").strip()
        if not text:
            raise GedaechtnisFehler("Leerer Text wird nicht gespeichert.", 2)
        if not (beleg or "").strip():
            raise GedaechtnisFehler("Jeder Eintrag braucht einen Beleg "
                                    "(--beleg).", 2)
        if ebene not in EBENEN:
            raise GedaechtnisFehler("Ebene muss %s sein." % "/".join(EBENEN),
                                    2)
        wichtigkeit = max(1, min(5, int(wichtigkeit)))
        alt = self._doppelt(text, typ)
        zeit = zeit_text(self.jetzt())
        if alt:
            self._anhaengen({"typ": "bestaetigung", "bezug": alt["id"],
                             "zeit_utc": zeit, "name": self.name,
                             "quelle": quelle, "beleg": beleg})
            return alt["id"], False
        vorhanden = {e["id"] for e in self.eintraege()}
        n = 0
        while True:
            eid = "e-" + hashlib.sha256(("%s|%s|%s|%s|%d" % (
                self.name, typ, zeit, text, n)).encode("utf-8")
            ).hexdigest()[:10]
            if eid not in vorhanden:
                break
            n += 1
        status = "vorgeschlagen" if ebene == "universell" else "aktiv"
        zeile = {"typ": typ, "id": eid, "zeit_utc": zeit, "name": self.name,
                 "quelle": quelle, "text": text, "ebene": ebene,
                 "wichtigkeit": wichtigkeit, "beleg": beleg, "status": status,
                 "hash": text_hash(text)}
        if aus:
            zeile["aus"] = list(aus)
        self._anhaengen(zeile)
        return eid, True

    def status_setzen(self, eintrag_id, status, wer, grund=""):
        self.finden(eintrag_id)
        self._anhaengen({"typ": "status", "bezug": eintrag_id,
                         "status": status, "wer": wer, "grund": grund,
                         "zeit_utc": zeit_text(self.jetzt()),
                         "name": self.name})

    def freigeben(self, eintrag_id, kurator):
        if kurator != KURATOR:
            raise GedaechtnisFehler("Nur der Kurator %s darf freigeben."
                                    % KURATOR, 4)
        self.status_setzen(eintrag_id, "freigegeben", kurator)

    def zurueckrollen(self, eintrag_id, wer, grund=""):
        self.status_setzen(eintrag_id, "widerrufen", wer, grund)

    # -- Bewertung

    def punkte(self, e):
        zeit = zeit_lesen(e.get("zuletzt_utc") or e.get("zeit_utc"))
        alter = 0.0
        if zeit:
            alter = max(0.0, (self.jetzt() - zeit).total_seconds() / 86400.0)
        frische = 0.5 ** (alter / HALBWERTSZEIT_TAGE)
        verstaerkung = 1.0 + math.log(max(1, e.get("zaehler", 1)))
        bonus = 1.2 if e.get("status") == "freigegeben" else 1.0
        return (e.get("wichtigkeit", 3) / 5.0) * frische * verstaerkung * bonus

    def suchen(self, anfrage, anzahl=10):
        frage = woerter(anfrage)
        if not frage:
            return []
        treffer = []
        for e in self.eintraege():
            if e.get("status") == "widerrufen":
                continue
            ueberlapp = len(frage & woerter(e.get("text"))) / float(len(frage))
            if ueberlapp <= 0:
                continue
            treffer.append((ueberlapp * self.punkte(e), e))
        treffer.sort(key=lambda t: (-t[0], t[1]["id"]))
        return treffer[:anzahl]

    # -- Reflektieren (Beobachtung -> Fakt, nichts wird geloescht)

    def reflektieren(self, quelle="reflektieren", min_zaehler=2,
                     min_wichtigkeit=4):
        schon = set()
        for e in self.eintraege():
            if e.get("typ") == "fakt":
                schon.update(e.get("aus") or [])
        neu = []
        for e in self.eintraege():
            if e.get("typ") != "beobachtung" or e["id"] in schon:
                continue
            if e.get("status") == "widerrufen":
                continue
            if e.get("zaehler", 1) >= min_zaehler or \
                    e.get("wichtigkeit", 3) >= min_wichtigkeit:
                eid, _ = self.merken(
                    e["text"], beleg="Beobachtung " + e["id"], typ="fakt",
                    quelle=quelle, ebene=e.get("ebene", "konkret"),
                    wichtigkeit=e.get("wichtigkeit", 3), aus=[e["id"]])
                neu.append(eid)
        return neu

    # -- Startkontext (kompakt, begrenzt)

    def start(self, max_zeichen=1500, anzahl=12):
        fakten = [e for e in self.eintraege() if e.get("typ") == "fakt"
                  and e.get("status") in ("aktiv", "freigegeben")]
        fakten.sort(key=lambda e: (-self.punkte(e), e["id"]))
        zeilen = ["Startkontext %s (%d Fakten):" % (self.name, len(fakten))]
        laenge = len(zeilen[0])
        for e in fakten[:anzahl]:
            z = "- [%s] %s" % (e.get("ebene", "?")[:4], e["text"])
            if laenge + len(z) + 1 > max_zeichen:
                zeilen.append("- ... (gekuerzt)")
                break
            zeilen.append(z)
            laenge += len(z) + 1
        return "\n".join(zeilen)[:max_zeichen]

    # -- Aufraeumen (Attic statt rm)

    def _sicherung(self):
        ziel = os.path.join(self.attic, "sicherungen")
        os.makedirs(ziel, exist_ok=True)
        stempel = self.jetzt().strftime("%Y%m%dT%H%M%S")
        archiv = os.path.join(ziel, "archiv")
        n = 1
        while True:
            datei = "erinnerungen_%s_%03d.jsonl" % (stempel, n)
            if not os.path.exists(os.path.join(ziel, datei)) and \
                    not os.path.exists(os.path.join(archiv, datei)):
                break
            n += 1
        pfad = os.path.join(ziel, datei)
        shutil.copy2(self.datei, pfad)
        alle = sorted(f for f in os.listdir(ziel) if f.endswith(".jsonl"))
        if len(alle) > SICHERUNGEN_BEHALTEN:
            os.makedirs(archiv, exist_ok=True)
            for f in alle[:-SICHERUNGEN_BEHALTEN]:
                if not os.path.exists(os.path.join(archiv, f)):
                    shutil.move(os.path.join(ziel, f),
                                os.path.join(archiv, f))
        return pfad

    def aufraeumen(self, schwelle=0.15, maximal=20, trocken=False):
        kandidaten = []
        for e in self.eintraege():
            if e.get("status") == "freigegeben":
                continue
            if e.get("typ") == "fakt" and e.get("status") == "aktiv" and \
                    e.get("wichtigkeit", 3) >= 4:
                continue
            p = self.punkte(e)
            if e.get("status") == "widerrufen" or p < schwelle:
                kandidaten.append((p, e))
        kandidaten.sort(key=lambda t: (t[0], t[1]["id"]))
        ids = {e["id"] for _, e in kandidaten[:maximal]}
        if trocken or not ids:
            return sorted(ids), None
        sicherung = self._sicherung()
        bleiben, weg = [], []
        for z in self.zeilen():
            if z.get("id") in ids or z.get("bezug") in ids:
                weg.append(z)
            else:
                bleiben.append(z)
        os.makedirs(self.attic, exist_ok=True)
        with open(os.path.join(self.attic, "erinnerungen_attic.jsonl"), "a",
                  encoding="utf-8") as f:
            for z in weg:
                f.write(json.dumps(z, ensure_ascii=False, sort_keys=True)
                        + "\n")
        fd, tmp = tempfile.mkstemp(dir=self.ordner, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for z in bleiben:
                f.write(json.dumps(z, ensure_ascii=False, sort_keys=True)
                        + "\n")
        os.replace(tmp, self.datei)
        return sorted(ids), sicherung


# ---------------------------------------------------------------- CLI

def eintrag_text(e, punkte=None):
    kopf = "%s  %s  %s/%s  w%s x%s" % (
        e["id"], e.get("zeit_utc", "?"), e.get("typ"), e.get("ebene"),
        e.get("wichtigkeit"), e.get("zaehler", 1))
    if punkte is not None:
        kopf += "  punkte %.3f" % punkte
    kopf += "  [%s]" % e.get("status")
    return kopf + "\n    " + e.get("text", "") + "\n    Beleg: " + \
        e.get("beleg", "") + "  Quelle: " + e.get("quelle", "")


def lauf(argv=None, basis=None, jetzt=None):
    p = argparse.ArgumentParser(
        description="Gedaechtnis fuer Grok, Tesla, Dimitri, Jack "
                    "(nur anhaengen, Attic statt rm).")
    p.add_argument("name", help="Grok, Tesla, Dimitri oder Jack")
    sub = p.add_subparsers(dest="befehl")
    b = sub.add_parser("beobachten", help="Rohe Beobachtung merken")
    b.add_argument("text")
    b.add_argument("--beleg", required=True)
    b.add_argument("--quelle", default="hand")
    b.add_argument("--ebene", default="konkret", choices=EBENEN)
    b.add_argument("--wichtigkeit", type=int, default=3)
    r = sub.add_parser("reflektieren", help="Beobachtungen zu Fakten")
    r.add_argument("--min-zaehler", type=int, default=2)
    r.add_argument("--min-wichtigkeit", type=int, default=4)
    s = sub.add_parser("start", help="Kompakter Startkontext")
    s.add_argument("--max-zeichen", type=int, default=1500)
    q = sub.add_parser("suchen", help="Bewertete Suche")
    q.add_argument("text")
    q.add_argument("--anzahl", type=int, default=10)
    f = sub.add_parser("freigeben", help="Vorschlag freigeben (nur Kurator)")
    f.add_argument("id")
    f.add_argument("--kurator", required=True)
    z = sub.add_parser("zurueckrollen", help="Eintrag widerrufen")
    z.add_argument("id")
    z.add_argument("--wer", default="hand")
    z.add_argument("--grund", default="")
    a = sub.add_parser("aufraeumen", help="Schwache Eintraege ins Attic")
    a.add_argument("--schwelle", type=float, default=0.15)
    a.add_argument("--maximal", type=int, default=20)
    a.add_argument("--trocken", action="store_true")
    sub.add_parser("zeigen", help="Alle Eintraege anzeigen")
    args = p.parse_args(argv)
    g = Gedaechtnis(args.name, basis=basis, jetzt=jetzt)

    if args.befehl == "beobachten":
        eid, neu = g.merken(args.text, args.beleg, quelle=args.quelle,
                            ebene=args.ebene, wichtigkeit=args.wichtigkeit)
        print(("Neu gemerkt: %s" if neu else
               "Schon bekannt, Zaehler erhoeht: %s") % eid)
    elif args.befehl == "reflektieren":
        neu = g.reflektieren(min_zaehler=args.min_zaehler,
                             min_wichtigkeit=args.min_wichtigkeit)
        print("%d neue(r) Fakt(en): %s" % (len(neu), ", ".join(neu) or "-"))
    elif args.befehl == "start":
        print(g.start(max_zeichen=args.max_zeichen))
    elif args.befehl == "suchen":
        treffer = g.suchen(args.text, args.anzahl)
        if not treffer:
            print("Nichts gefunden.")
        for punkte, e in treffer:
            print(eintrag_text(e, punkte))
    elif args.befehl == "freigeben":
        g.freigeben(args.id, args.kurator)
        print("Freigegeben: %s" % args.id)
    elif args.befehl == "zurueckrollen":
        g.zurueckrollen(args.id, args.wer, args.grund)
        print("Widerrufen (Zeile bleibt erhalten): %s" % args.id)
    elif args.befehl == "aufraeumen":
        ids, sicherung = g.aufraeumen(args.schwelle, args.maximal,
                                      args.trocken)
        if args.trocken:
            print("TROCKEN, wuerde ins Attic: %s" % (", ".join(ids) or "-"))
        else:
            print("Ins Attic verschoben: %s" % (", ".join(ids) or "-"))
            if sicherung:
                print("Sicherung: %s" % sicherung)
    else:
        for e in g.eintraege():
            print(eintrag_text(e))
    return 0


def main():
    try:
        return lauf()
    except GedaechtnisFehler as e:
        sys.stderr.write("FEHLER: " + e.meldung + "\n")
        return e.code


if __name__ == "__main__":
    sys.exit(main())
