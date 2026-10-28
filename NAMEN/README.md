# NAMEN

Dieser Ordner ist **kein jack-Modul**. Er liegt bewusst abseits vom JACK-Code und stört nichts.
Hier liegen vier Namensordner nebeneinander und die Logik für das Schreibrechte-Gedächtnis.

## Aufbau

- `Grok/`: Notizen und Session-Erinnerungen von Grok
- `Tesla/`: Notizen und Session-Erinnerungen von Tesla
- `Dimitri/`: Notizen und Session-Erinnerungen von Dimitri
- `Jack/`: Notizen und Session-Erinnerungen zu Jack
- `schreibrechte/`: Schreibrechte-Gedächtnis (Skript, Tests, Verlaufsdatei)
- `gedaechtnis.py`: gemeinsames Gedächtnis für alle vier Namen, `test_gedaechtnis.py`: Tests dazu

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

Weitere Schalter: `--repo besitzer/name` (Standard: dimitriskripkin-lgtm/jack-core), `--immer`, `--ohne-einladungen`,
`--gedaechtnis` (optional: Änderungen zusätzlich als Jack-Beobachtung merken; klappt das nicht, läuft das Skript trotzdem normal weiter).
Hinweis: GitHub zeigt die Mitarbeiterliste nur einem Token mit Push-Rechten am Repo.

### Tests (ohne Netzwerk)

    python3 -m unittest NAMEN/schreibrechte/test_schreibrechte.py

## Gemeinsames Gedächtnis (`gedaechtnis.py`)

Ein Speicher pro Name: `NAMEN/<Name>/erinnerungen.jsonl`, nur anhängend. Nur Standardbibliothek, kein Netzwerk, keine Embeddings, kein Ollama.

Jeder Eintrag trägt `name`, `quelle`, `ebene` (konkret / strukturell / universell), `wichtigkeit` (1 bis 5), `beleg` und `status`.
Zähler, Freigaben und Widerrufe sind eigene, angehängte Zeilen. Alte Zeilen werden nie umgeschrieben.

    python3 NAMEN/gedaechtnis.py Jack beobachten "Text" --beleg "Woher" [--quelle ...] [--ebene ...] [--wichtigkeit 1-5]
    python3 NAMEN/gedaechtnis.py Jack reflektieren           (Beobachtungen werden zu Fakten, nichts wird gelöscht)
    python3 NAMEN/gedaechtnis.py Jack start                  (kompakter Startkontext, begrenzt mit --max-zeichen)
    python3 NAMEN/gedaechtnis.py Jack suchen "Text"          (Treffer x Wichtigkeit x Frische)
    python3 NAMEN/gedaechtnis.py Jack freigeben <id> --kurator Dimitri
    python3 NAMEN/gedaechtnis.py Jack zurueckrollen <id>     (markiert widerrufen, Zeile bleibt)
    python3 NAMEN/gedaechtnis.py Jack aufraeumen --trocken   (zeigt, was ins Attic käme)
    python3 NAMEN/gedaechtnis.py Jack zeigen

Regeln:
- Ohne `--beleg` wird nichts gespeichert.
- Doppelte (gleicher normalisierter Text oder Wort-Jaccard ab 0,8) erhöhen nur den Zähler.
- Universelle Einträge starten als `vorgeschlagen` und erscheinen erst nach Freigabe durch Dimitri im Startkontext.
- `aufraeumen` ist der einzige Schritt, der die Datei neu schreibt. Vorher gibt es immer eine Sicherung in `<Name>/attic/sicherungen/` (die letzten 5 bleiben dort, ältere wandern nach `attic/sicherungen/archiv/`, gelöscht wird nichts). Schwache oder widerrufene Einträge wandern nach `<Name>/attic/erinnerungen_attic.jsonl`. Freigegebene und wichtige Fakten bleiben.

Tests:

    python3 -m unittest NAMEN/test_gedaechtnis.py NAMEN/schreibrechte/test_schreibrechte.py

## Übernommene Ideen

Alle fünf Repos stehen unter MIT-Lizenz. Übernommen wurden nur Konzepte, der Code hier ist selbst geschrieben.

- [intertwine/grok-observational-memory](https://github.com/intertwine/grok-observational-memory) (MIT, laut Repo seit 05.09.2026 nicht mehr gepflegt): Beobachten, Reflektieren zu dauerhaften Fakten, kompakter begrenzter Startkontext. Nicht übernommen: Hooks in `~/.grok`, der externe `om`-CLI.
- [PLRTCore/shadow-vault](https://github.com/PLRTCore/shadow-vault) (MIT): bewertete Suche (Relevanz, Wichtigkeit, Frische), Jaccard-Dedup mit Verstärkung statt Doppel, Pruning nach Wichtigkeit, rotierende Sicherungen. Angepasst: Pruning verschiebt ins Attic statt zu löschen, alte Sicherungen werden archiviert statt gelöscht.
- [Wolfe-Jam/grok-faf-voice](https://github.com/Wolfe-Jam/grok-faf-voice) (MIT): Namepoint-Idee, also eine feste Adresse fürs Gedächtnis über Sitzungen, Geräte und Modelle hinweg. Hier: der Namensordner plus die Felder `name` und `quelle`. Nicht übernommen: Voice, LiveKit, MCPaaS-Dienst, `.fafm`-Format.
- [koreysmith123/recallsmith](https://github.com/koreysmith123/recallsmith) (MIT): drei Ebenen konkret / strukturell / universell als Feld `ebene`. Nicht übernommen: PostgreSQL, pgvector, EmbeddingGemma (Ollama-Sperre, keine Embeddings).
- [matthiasroder/grok-bot-learning](https://github.com/matthiasroder/grok-bot-learning) (MIT): jeder Eintrag braucht einen Beleg, Kurator-Freigabe für geteilte Lehren, Rückrollen ohne Verlust des Belegs. Hier: `universell` startet `vorgeschlagen`, Kurator ist Dimitri, `zurueckrollen` markiert `widerrufen`. Nicht übernommen: SQLite/FTS5, Flotten-Konfiguration, Review-Routine.
- LUCI Core von Memories.ai ([Release-Repo](https://github.com/Memories-ai-labs/luci-core-releases), Quellcode nicht öffentlich, keine Lizenz im Release-Repo angegeben): zeichnet auf, was auf dem Bildschirm des Bot-Computers zu sehen ist (unter `/workspace/.luci`). **Nicht übernommen:** Bildschirmverläufe können private Inhalte enthalten und gehören nicht in ein öffentliches Repo. Auf dem Assistenten-Computer ist es nicht installiert.

## Grundsätze

- GitHub ist Archiv und Spiegel, **kein Befehlsbus**: Daten gehen raus, Befehle kommen nie rein.
- Das Skript liest nur die GitHub-API und schreibt nur die lokale Verlaufsdatei.
- Die Honor bleibt die Live-Wahrheit. Im Zweifel gilt der Stand auf der Honor.
- Kein Token, keine privaten Daten in diesem Ordner.
