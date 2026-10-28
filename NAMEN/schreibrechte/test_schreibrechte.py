"""Tests fuer schreibrechte.py, ohne Netzwerk (API wird ersetzt)."""

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import schreibrechte as s  # noqa: E402


def falscher_holer(schnapp):
    def holer(repo, token, mit_einladungen=True):
        return dict(schnapp)
    return holer


class SchreibrechteTest(unittest.TestCase):
    def setUp(self):
        self.ordner = tempfile.mkdtemp()
        self.pfad = os.path.join(self.ordner, "verlauf.jsonl")
        os.environ["GITHUB_TOKEN"] = "test-token-nicht-echt"

    def tearDown(self):
        shutil.rmtree(self.ordner)
        os.environ.pop("GITHUB_TOKEN", None)

    def lauf(self, argv, schnapp):
        aus = io.StringIO()
        with redirect_stdout(aus), redirect_stderr(io.StringIO()):
            code = s.lauf(argv, pfad=self.pfad, holer=falscher_holer(schnapp))
        return code, aus.getvalue()

    def zeilen(self):
        if not os.path.exists(self.pfad):
            return []
        with open(self.pfad, encoding="utf-8") as f:
            return [json.loads(z) for z in f if z.strip()]

    def test_unterschiede(self):
        alt = {"a": "admin", "b": "write", "c": "read"}
        neu = {"a": "admin", "b": "read", "d": "write"}
        arten = {(x["art"], x["login"]) for x in s.unterschiede(alt, neu)}
        self.assertEqual(arten, {("hinzugefuegt", "d"), ("entfernt", "c"),
                                 ("geaendert", "b")})
        geaendert = [x for x in s.unterschiede(alt, neu)
                     if x["art"] == "geaendert"][0]
        self.assertEqual((geaendert["alt"], geaendert["neu"]),
                         ("write", "read"))

    def test_append_only_und_nur_bei_aenderung(self):
        with open(self.pfad, "w", encoding="utf-8") as f:
            f.write(json.dumps({"zeit_utc": "x", "repo": "o/r",
                                "snapshot": None, "changes": [],
                                "notiz": "Start"}) + "\n")
        self.lauf(["--repo", "o/r"], {"a": "admin"})
        self.assertEqual(len(self.zeilen()), 2)
        self.lauf(["--repo", "o/r"], {"a": "admin"})
        self.assertEqual(len(self.zeilen()), 2, "ohne Aenderung keine Zeile")
        self.lauf(["--repo", "o/r"], {"a": "admin", "b": "write"})
        z = self.zeilen()
        self.assertEqual(len(z), 3)
        self.assertEqual(z[0]["notiz"], "Start", "alte Zeile unveraendert")
        self.assertEqual(z[2]["changes"][0]["art"], "hinzugefuegt")
        self.lauf(["--repo", "o/r", "--immer"], {"a": "admin", "b": "write"})
        self.assertEqual(len(self.zeilen()), 4)

    def test_trocken_schreibt_nichts(self):
        code, aus = self.lauf(["--repo", "o/r", "--trocken"], {"a": "admin"})
        self.assertEqual(code, 0)
        self.assertIn("TROCKEN", aus)
        self.assertFalse(os.path.exists(self.pfad))

    def test_kein_token(self):
        os.environ.pop("GITHUB_TOKEN", None)
        alt_gh = os.environ.pop("GH_TOKEN", None)
        try:
            with self.assertRaises(s.SchreibrechteFehler) as k:
                self.lauf(["--repo", "o/r"], {})
            self.assertEqual(k.exception.code, 2)
        finally:
            if alt_gh is not None:
                os.environ["GH_TOKEN"] = alt_gh

    def test_token_nie_ausgegeben(self):
        _, aus = self.lauf(["--repo", "o/r", "--trocken"], {"a": "admin"})
        self.assertNotIn("test-token-nicht-echt", aus)

    def test_rolle_und_seiten(self):
        self.assertEqual(s.rolle_von({"role_name": "maintain"}), "maintain")
        self.assertEqual(s.rolle_von({"permissions": {"push": True,
                                                      "pull": True}}), "write")
        link = ('<https://api.github.com/x?page=2>; rel="next", '
                '<https://api.github.com/x?page=3>; rel="last"')
        self.assertEqual(s._naechste_seite(link),
                         "https://api.github.com/x?page=2")
        self.assertIsNone(s._naechste_seite(None))

    def test_zeigen(self):
        self.lauf(["--repo", "o/r"], {"a": "admin"})
        _, aus = self.lauf(["--zeigen"], {})
        self.assertIn("a=admin", aus)
        self.assertIn("+ a bekommt Rolle admin", aus)


if __name__ == "__main__":
    unittest.main()
