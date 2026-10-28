#!/usr/bin/env python3
"""Schreibrechte-Gedaechtnis fuer ein GitHub-Repository.

Liest die Mitarbeiter (Collaborators) und offene Einladungen ueber die
GitHub-API und haengt Aenderungen an die Verlaufsdatei verlauf.jsonl an.

- Nur Lesen bei GitHub, nur Anhaengen lokal (append-only).
- Kein jack-Modul, kein Befehlsweg: GitHub ist Archiv, kein Befehlsbus.
- Nur Python-Standardbibliothek.

Token kommt aus der Umgebung: GITHUB_TOKEN oder GH_TOKEN.
Der Token wird nie ausgegeben und nie gespeichert.
"""

import argparse
import datetime
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

STANDARD_REPO = "dimitriskripkin-lgtm/jack-core"
API = "https://api.github.com"
SKRIPT_ORDNER = os.path.dirname(os.path.abspath(__file__))
VERLAUF_DATEI = os.path.join(SKRIPT_ORDNER, "verlauf.jsonl")


class SchreibrechteFehler(Exception):
    """Fehler mit deutscher Meldung und Exit-Code."""

    def __init__(self, meldung, code=1):
        super().__init__(meldung)
        self.meldung = meldung
        self.code = code


def token_holen():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SchreibrechteFehler(
            "Kein Token gefunden. Bitte GITHUB_TOKEN oder GH_TOKEN setzen "
            "(GitHub zeigt die Mitarbeiterliste nur mit Push-Rechten am "
            "Repo; das Skript selbst liest nur).", 2)
    return token


def _naechste_seite(link_kopf):
    if not link_kopf:
        return None
    for teil in link_kopf.split(","):
        stuecke = teil.split(";")
        if len(stuecke) < 2:
            continue
        if 'rel="next"' in stuecke[1]:
            return stuecke[0].strip().strip("<>")
    return None


def api_holen(url, token):
    """Holt alle Seiten einer Listen-URL. Gibt Liste zurueck."""
    ergebnis = []
    while url:
        anfrage = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "NAMEN-schreibrechte",
        })
        try:
            with urllib.request.urlopen(anfrage, timeout=30) as antwort:
                daten = json.loads(antwort.read().decode("utf-8"))
                link = antwort.headers.get("Link")
        except urllib.error.HTTPError as e:
            if e.code == 401:
                text = "Token ungueltig oder abgelaufen (HTTP 401)."
            elif e.code == 403:
                text = ("Kein Zugriff oder Rate-Limit erreicht (HTTP 403). "
                        "Fuer Collaborators braucht der Token Push-Rechte "
                        "auf das Repo.")
            elif e.code == 404:
                text = "Repo nicht gefunden oder kein Zugriff (HTTP 404)."
            else:
                text = "GitHub-API-Fehler (HTTP %s)." % e.code
            raise SchreibrechteFehler(text, 3)
        except urllib.error.URLError as e:
            raise SchreibrechteFehler(
                "Netzwerkfehler beim Abruf: %s" % e.reason, 4)
        if not isinstance(daten, list):
            raise SchreibrechteFehler("Unerwartete Antwort der GitHub-API.", 3)
        ergebnis.extend(daten)
        url = _naechste_seite(link)
    return ergebnis


def rolle_von(eintrag):
    rolle = eintrag.get("role_name")
    if rolle:
        return rolle
    rechte = eintrag.get("permissions") or {}
    for name in ("admin", "maintain", "push", "triage", "pull"):
        if rechte.get(name):
            return {"push": "write", "pull": "read"}.get(name, name)
    return "unbekannt"


def schnappschuss_holen(repo, token, mit_einladungen=True):
    basis = API + "/repos/" + urllib.parse.quote(repo, safe="/")
    leute = api_holen(basis + "/collaborators?affiliation=all&per_page=100",
                      token)
    schnapp = {}
    for p in leute:
        login = p.get("login")
        if login:
            schnapp[login] = rolle_von(p)
    if mit_einladungen:
        try:
            einladungen = api_holen(basis + "/invitations?per_page=100", token)
        except SchreibrechteFehler as e:
            sys.stderr.write("Hinweis: Einladungen nicht lesbar: %s\n"
                             % e.meldung)
            einladungen = []
        for ein in einladungen:
            login = (ein.get("invitee") or {}).get("login")
            if login and login not in schnapp:
                schnapp[login] = "eingeladen:" + str(
                    ein.get("permissions", "unbekannt"))
    return schnapp


def verlauf_lesen(pfad=None):
    pfad = pfad or VERLAUF_DATEI
    zeilen = []
    if not os.path.exists(pfad):
        return zeilen
    with open(pfad, "r", encoding="utf-8") as f:
        for nr, zeile in enumerate(f, 1):
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                zeilen.append(json.loads(zeile))
            except ValueError:
                sys.stderr.write("Hinweis: Zeile %d im Verlauf unlesbar, "
                                 "wird uebersprungen.\n" % nr)
    return zeilen


def letzter_schnappschuss(verlauf, repo):
    for eintrag in reversed(verlauf):
        if eintrag.get("repo") == repo and eintrag.get("snapshot") is not None:
            return eintrag["snapshot"]
    return None


def unterschiede(alt, neu):
    alt = alt or {}
    aenderungen = []
    for login in sorted(set(neu) - set(alt)):
        aenderungen.append({"art": "hinzugefuegt", "login": login,
                            "neu": neu[login]})
    for login in sorted(set(alt) - set(neu)):
        aenderungen.append({"art": "entfernt", "login": login,
                            "alt": alt[login]})
    for login in sorted(set(alt) & set(neu)):
        if alt[login] != neu[login]:
            aenderungen.append({"art": "geaendert", "login": login,
                                "alt": alt[login], "neu": neu[login]})
    return aenderungen


def eintrag_bauen(repo, schnapp, aenderungen, erster_abruf):
    eintrag = {
        "zeit_utc": datetime.datetime.now(datetime.timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo": repo,
        "snapshot": schnapp,
        "changes": aenderungen,
    }
    if erster_abruf:
        eintrag["notiz"] = "Erster Abruf"
    return eintrag


def anhaengen(eintrag, pfad=None):
    """Nur anhaengen, nie ueberschreiben."""
    pfad = pfad or VERLAUF_DATEI
    with open(pfad, "a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False, sort_keys=True) + "\n")


def aenderung_text(a):
    if a["art"] == "hinzugefuegt":
        return "  + %s bekommt Rolle %s" % (a["login"], a["neu"])
    if a["art"] == "entfernt":
        return "  - %s entfernt (vorher %s)" % (a["login"], a["alt"])
    return "  ~ %s: %s -> %s" % (a["login"], a["alt"], a["neu"])


def verlauf_zeigen(pfad=None):
    verlauf = verlauf_lesen(pfad)
    if not verlauf:
        print("Verlauf ist leer.")
        return
    for e in verlauf:
        kopf = "%s  %s" % (e.get("zeit_utc", "?"), e.get("repo", "?"))
        if e.get("notiz"):
            kopf += "  (" + e["notiz"] + ")"
        print(kopf)
        if e.get("snapshot") is None:
            print("  kein Schnappschuss")
        else:
            rollen = ", ".join("%s=%s" % (k, v)
                               for k, v in sorted(e["snapshot"].items()))
            print("  Stand: " + (rollen or "niemand"))
        for a in e.get("changes") or []:
            print(aenderung_text(a))


def lauf(argv=None, pfad=None, holer=None):
    parser = argparse.ArgumentParser(
        description="Schreibrechte-Gedaechtnis: merkt sich, wer Schreibrechte "
                    "hat und wie sie sich aendern (nur Lesen bei GitHub, "
                    "nur Anhaengen lokal).")
    parser.add_argument("--repo", default=STANDARD_REPO,
                        help="Repo als besitzer/name (Standard: %(default)s)")
    parser.add_argument("--immer", action="store_true",
                        help="Auch ohne Aenderung eine Zeile anhaengen")
    parser.add_argument("--trocken", action="store_true",
                        help="Nur anzeigen, nichts schreiben")
    parser.add_argument("--zeigen", action="store_true",
                        help="Verlauf lesbar anzeigen und beenden")
    parser.add_argument("--ohne-einladungen", action="store_true",
                        help="Offene Einladungen nicht abfragen")
    parser.add_argument("--gedaechtnis", action="store_true",
                        help="Aenderungen zusaetzlich als Jack-Beobachtung "
                             "in NAMEN/Jack/erinnerungen.jsonl merken")
    args = parser.parse_args(argv)
    pfad = pfad or VERLAUF_DATEI

    if args.zeigen:
        verlauf_zeigen(pfad)
        return 0

    holer = holer or schnappschuss_holen
    token = token_holen()
    schnapp = holer(args.repo, token, not args.ohne_einladungen)
    verlauf = verlauf_lesen(pfad)
    alt = letzter_schnappschuss(verlauf, args.repo)
    aenderungen = unterschiede(alt, schnapp)
    erster = alt is None

    if not aenderungen and not args.immer and not erster:
        print("Keine Aenderung bei den Schreibrechten (%s)." % args.repo)
        return 0

    eintrag = eintrag_bauen(args.repo, schnapp, aenderungen, erster)
    if args.trocken:
        print("TROCKEN, nichts geschrieben:")
        print(json.dumps(eintrag, ensure_ascii=False, indent=2,
                         sort_keys=True))
        return 0
    anhaengen(eintrag, pfad)
    print("Verlauf ergaenzt: %d Aenderung(en)." % len(aenderungen))
    for a in aenderungen:
        print(aenderung_text(a))
    if args.gedaechtnis and aenderungen:
        gedaechtnis_melden(args.repo, aenderungen, eintrag["zeit_utc"])
    return 0


def gedaechtnis_melden(repo, aenderungen, zeit, basis=None):
    """Optionaler Haken: klappt es nicht, laeuft das Skript trotzdem weiter."""
    try:
        sys.path.insert(0, os.path.dirname(SKRIPT_ORDNER))
        import gedaechtnis
        g = gedaechtnis.Gedaechtnis("Jack", basis=basis)
        text = "Schreibrechte %s geaendert: %s" % (
            repo, "; ".join(aenderung_text(a).strip() for a in aenderungen))
        g.merken(text, beleg="schreibrechte/verlauf.jsonl " + zeit,
                 quelle="schreibrechte.py", ebene="konkret", wichtigkeit=4)
        return True
    except Exception as e:  # Haken darf nie den Lauf stoppen
        sys.stderr.write("Hinweis: Gedaechtnis-Haken uebersprungen: %s\n"
                         % e.__class__.__name__)
        return False


def main():
    try:
        return lauf()
    except SchreibrechteFehler as e:
        sys.stderr.write("FEHLER: " + e.meldung + "\n")
        return e.code


if __name__ == "__main__":
    sys.exit(main())
