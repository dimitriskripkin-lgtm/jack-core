# NAMEN

Dieser Ordner ist **kein jack-Modul**. Er liegt bewusst abseits vom JACK-Code und stört nichts.
Hier liegen vier Namensordner nebeneinander und die Logik für das Schreibrechte-Gedächtnis.

## Aufbau

- `Grok/`: Notizen und Session-Erinnerungen von Grok
- `Tesla/`: Notizen und Session-Erinnerungen von Tesla
- `Dimitri/`: Notizen und Session-Erinnerungen von Dimitri
- `Jack/`: Notizen und Session-Erinnerungen zu Jack
- `schreibrechte/`: Schreibrechte-Gedächtnis (Skript, Tests, Verlaufsdatei)

## Schreibrechte-Gedächtnis

`schreibrechte/schreibrechte.py` merkt sich, wer Schreibrechte am Repo hat und wie sich das über die Zeit ändert.

- Liest nur die GitHub-API (Collaborators und offene Einladungen).
- Schreibt nur die lokale Verlaufsdatei `schreibrechte/verlauf.jsonl`, und zwar nur anhängend. Nichts wird gelöscht oder umgeschrieben.
- Eine neue Zeile kommt nur dazu, wenn sich etwas geändert hat (oder mit `--immer`).
- Nur Python-Standardbibliothek.

### Aufruf

Token nur in der Umgebung setzen, nie in eine Datei schreiben, nie pushen:

    export GITHUB_TOKEN=...   (oder GH_TOKEN)
    python3 NAMEN/schreibrechte/schreibrechte.py --trocken   (nur anzeigen)
    python3 NAMEN/schreibrechte/schreibrechte.py             (Verlauf ergänzen)
    python3 NAMEN/schreibrechte/schreibrechte.py --zeigen    (Verlauf lesbar)

Weitere Schalter: `--repo besitzer/name` (Standard: dimitriskripkin-lgtm/jack-core), `--immer`, `--ohne-einladungen`.
Hinweis: GitHub zeigt die Mitarbeiterliste nur einem Token mit Push-Rechten am Repo.

### Tests (ohne Netzwerk)

    python3 -m unittest NAMEN/schreibrechte/test_schreibrechte.py

## Grundsätze

- GitHub ist Archiv und Spiegel, **kein Befehlsbus**: Daten gehen raus, Befehle kommen nie rein.
- Das Skript liest nur die GitHub-API und schreibt nur die lokale Verlaufsdatei.
- Die Honor bleibt die Live-Wahrheit. Im Zweifel gilt der Stand auf der Honor.
- Kein Token, keine privaten Daten in diesem Ordner.
