# 262 Jack-Training ueber den Dialogkanal (09.10.2026)

Methode: m.frage() / jack_dialog.py (Kapitel 260), Fragen stellen, Fehler messen, patchen, gleiche Fragen erneut.

## Befunde vorher
- Antworten zu sich selbst waren erfunden (Dashboard, Sprachbefehl, verschluesselte Verbindungen).
- "Wie lernst du?" kippte einen alten Prompt-Dump aus dem Memory in die Antwort (Lese-Tuer).
- Folgewuensche ("in einfachen Worten") hingen an der falschen Antwort, Themenwechsel wiederholte alte Fragen.

## Gebaut
- jack_selbst.md + Lane SELBST (JACK_TUNE_SELBST): Abschnitte mit Schluesselwoertern, laengster Treffer gewinnt, Antwort kommt woertlich aus der Datei (Fakten statt Phantasie). Pflege: Abschnitt ergaenzen, wenn sich der Aufbau aendert.
- Lane UMFORMEN (JACK_TUNE_UMFORMEN): "in einfachen Worten", "kuerzer", "nochmal kurz" formt Jacks letzte Antwort per Groq um (2-3 Saetze, nichts Neues). Fallback bei Fehler: normales Gespraech.
- Lese-Tuer: Dump-Filter (JACK_TUNE_DUMPFILTER, Treffer >300 Zeichen oder "AKTUELLE UHRZEIT" raus); nur noch bei Fragewort am Satzanfang; Wohnort-Synonym (wohne/wohnst -> Wohnort).
- Talk-Prompt: Verlauf "bei neuem Thema ignorieren", "DIMA JETZT nur DIESE Nachricht beantworten".

## Ergebnis
Selbstfragen, Folgewuensche, Themenwechsel, Abruf (Frau, Lieblingssong, Wohnort), Rechnen: alle sauber.

## Offen
- "Nein, ich meinte das davor": Jack fragt nach, statt die vorletzte Antwort zu nehmen.
- jack_selbst.md muss bei Aenderungen am Aufbau mitgepflegt werden (Eintrag in 00_START_HIER sinnvoll).
