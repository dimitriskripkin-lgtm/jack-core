"""Tests fuer gedaechtnis.py, ohne Netzwerk, in einem Temp-Ordner."""

import datetime
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gedaechtnis as gd  # noqa: E402

JETZT = datetime.datetime(2026, 10, 28, 12, 0, 0,
                          tzinfo=datetime.timezone.utc)


class GedaechtnisTest(unittest.TestCase):
    def setUp(self):
        self.basis = tempfile.mkdtemp()
        self.g = gd.Gedaechtnis("Jack", basis=self.basis, jetzt=JETZT)

    def tearDown(self):
        shutil.rmtree(self.basis)

    def roh(self):
        with open(self.g.datei, encoding="utf-8") as f:
            return [json.loads(z) for z in f if z.strip()]

    def test_name_und_beleg_pflicht(self):
        with self.assertRaises(gd.GedaechtnisFehler):
            gd.Gedaechtnis("Unbekannt", basis=self.basis)
        with self.assertRaises(gd.GedaechtnisFehler):
            self.g.merken("Etwas", beleg="")

    def test_dedup_erhoeht_zaehler(self):
        a, neu1 = self.g.merken("Die Honor ist die Live-Wahrheit.", "t1")
        b, neu2 = self.g.merken("die honor ist die live wahrheit", "t2")
        c, neu3 = self.g.merken(
            "Die Honor ist die Live Wahrheit, immer.", "t3")
        self.assertTrue(neu1)
        self.assertFalse(neu2)
        self.assertEqual(a, b)
        self.assertEqual(len(self.g.eintraege()), 1 + (1 if neu3 else 0))
        self.assertGreaterEqual(self.g.finden(a)["zaehler"], 2)
        self.assertEqual(self.roh()[1]["typ"], "bestaetigung")

    def test_namepoint_felder(self):
        eid, _ = self.g.merken("Test", "beleg", quelle="handy")
        e = self.g.finden(eid)
        self.assertEqual((e["name"], e["quelle"]), ("Jack", "handy"))
        self.assertEqual(e["ebene"], "konkret")

    def test_bewertung_reihenfolge(self):
        alt = gd.Gedaechtnis("Jack", basis=self.basis,
                             jetzt=JETZT - datetime.timedelta(days=365))
        alt.merken("Backup vor jedem Patch", "b1", wichtigkeit=5)
        self.g.merken("Backup vor jedem Patch und py_compile", "b2",
                      wichtigkeit=5)
        self.g.merken("Backup Notiz", "b3", wichtigkeit=1)
        treffer = self.g.suchen("Backup Patch")
        texte = [e["text"] for _, e in treffer]
        # frisch + wichtig vor frisch + unwichtig vor ein Jahr alt
        self.assertEqual(texte, ["Backup vor jedem Patch und py_compile",
                                 "Backup Notiz", "Backup vor jedem Patch"])
        punkte = [p for p, _ in treffer]
        self.assertEqual(punkte, sorted(punkte, reverse=True))

    def test_reflektieren_loescht_nichts(self):
        a, _ = self.g.merken("Ollama bleibt gesperrt", "o1")
        self.g.merken("Ollama bleibt gesperrt", "o2")
        self.g.merken("Einmalige Kleinigkeit", "o3", wichtigkeit=2)
        vorher = len(self.roh())
        neu = self.g.reflektieren()
        self.assertEqual(len(neu), 1)
        self.assertEqual(len(self.roh()), vorher + 1)
        fakt = self.g.finden(neu[0])
        self.assertEqual(fakt["typ"], "fakt")
        self.assertEqual(fakt["aus"], [a])
        self.assertNotEqual(fakt["id"], a, "Fakt hat eigene ID")
        self.assertEqual(self.g.finden(a)["typ"], "beobachtung")
        self.assertEqual(self.g.reflektieren(), [], "nicht doppelt")
        self.assertIn("Ollama bleibt gesperrt", self.g.start())
        self.assertEqual(self.g.start().count("Ollama"), 1)

    def test_universell_vorgeschlagen_und_kurator(self):
        eid, _ = self.g.merken("Attic statt rm gilt ueberall", "u1",
                               ebene="universell", wichtigkeit=5)
        self.assertEqual(self.g.finden(eid)["status"], "vorgeschlagen")
        with self.assertRaises(gd.GedaechtnisFehler):
            self.g.freigeben(eid, "Grok")
        self.g.freigeben(eid, "Dimitri")
        self.assertEqual(self.g.finden(eid)["status"], "freigegeben")

    def test_zurueckrollen_append_only(self):
        eid, _ = self.g.merken("Falsche Annahme", "z1")
        vorher = self.roh()
        self.g.zurueckrollen(eid, "Dimitri", "falsch")
        nachher = self.roh()
        self.assertEqual(nachher[:len(vorher)], vorher)
        self.assertEqual(self.g.finden(eid)["status"], "widerrufen")
        self.assertEqual(self.g.suchen("Falsche Annahme"), [])

    def test_start_kontext_begrenzt(self):
        for i in range(30):
            self.g.merken("Fakt nummer %d %s" % (i, "x" * 40), "s%d" % i,
                          typ="fakt", wichtigkeit=(i % 5) + 1)
        v, _ = self.g.merken("Vorschlag universell", "s", typ="fakt",
                             ebene="universell")
        text = self.g.start(max_zeichen=300)
        self.assertLessEqual(len(text), 300)
        self.assertTrue(text.startswith("Startkontext Jack"))
        self.assertNotIn("Vorschlag universell", text)
        zweite = text.splitlines()[1]
        nummer = int(zweite.split("nummer ")[1].split()[0])
        self.assertEqual(nummer % 5, 4, "wichtigster Fakt steht oben")

    def test_aufraeumen_ins_attic_mit_sicherung(self):
        alt = gd.Gedaechtnis("Jack", basis=self.basis,
                             jetzt=JETZT - datetime.timedelta(days=720))
        schwach, _ = alt.merken("Alte unwichtige Notiz", "a1", wichtigkeit=1)
        stark, _ = self.g.merken("Neue wichtige Regel", "a2", wichtigkeit=5)
        weg, _ = self.g.merken("Widerrufene Sache", "a3", wichtigkeit=5)
        self.g.zurueckrollen(weg, "Dimitri")
        ids, _ = self.g.aufraeumen(trocken=True)
        self.assertEqual(set(ids), {schwach, weg})
        self.assertEqual(len(self.g.eintraege()), 3, "trocken aendert nichts")
        ids, sicherung = self.g.aufraeumen()
        self.assertTrue(os.path.exists(sicherung))
        self.assertEqual([e["id"] for e in self.g.eintraege()], [stark])
        attic = os.path.join(self.g.attic, "erinnerungen_attic.jsonl")
        with open(attic, encoding="utf-8") as f:
            attic_ids = {json.loads(z).get("id") or json.loads(z)["bezug"]
                         for z in f}
        self.assertEqual(attic_ids, {schwach, weg})
        with open(sicherung, encoding="utf-8") as f:
            self.assertEqual(len([z for z in f if z.strip()]), 4)

    def test_sicherungen_rotieren_ohne_loeschen(self):
        for i in range(gd.SICHERUNGEN_BEHALTEN + 2):
            alt = gd.Gedaechtnis("Jack", basis=self.basis,
                                 jetzt=JETZT - datetime.timedelta(days=900))
            alt.merken("Alt %d eindeutig %s" % (i, "q" * i), "r",
                       wichtigkeit=1)
            self.g.aufraeumen()
        ordner = os.path.join(self.g.attic, "sicherungen")
        oben = [f for f in os.listdir(ordner) if f.endswith(".jsonl")]
        archiv = os.listdir(os.path.join(ordner, "archiv"))
        self.assertEqual(len(oben), gd.SICHERUNGEN_BEHALTEN)
        self.assertEqual(len(oben) + len(archiv),
                         gd.SICHERUNGEN_BEHALTEN + 2)

    def test_cli(self):
        aus = io.StringIO()
        with redirect_stdout(aus):
            gd.lauf(["Grok", "beobachten", "CLI Test", "--beleg", "cli"],
                    basis=self.basis, jetzt=JETZT)
            gd.lauf(["Grok", "suchen", "CLI"], basis=self.basis, jetzt=JETZT)
            gd.lauf(["Grok", "start"], basis=self.basis, jetzt=JETZT)
        self.assertIn("Neu gemerkt", aus.getvalue())
        self.assertIn("CLI Test", aus.getvalue())
        self.assertTrue(os.path.exists(
            os.path.join(self.basis, "Grok", "erinnerungen.jsonl")))


if __name__ == "__main__":
    unittest.main()
