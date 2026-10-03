## 9. jack_missions.py (372 Zeilen, altes Mission-System — AUFGELÖST)

**Zweck:** Ein älteres, SQLite-Datenbank-basiertes Aufgabensystem (eigene DB, Tabelle `missions`,
Status "offen"/"fertig"/"blockiert"/"wartet_freigabe"/"verschoben"). Läuft als interner Thread im
Wächter (`_missions_loop()`, Kapitel 3) über `dispatch_once()`.

**Die wichtigste offene Frage der gesamten bisherigen Kartierung ist damit geklärt:** Laufen
`jack_mission_runner.py` (diese Woche, Kapitel 1, JSON-Dateien in `missions/pending/`) und dieses
System hier wirklich gleichzeitig? **Nein, praktisch nicht.** `jack_missions.add()` — die einzige
Funktion, die neue Einträge in dieses System einspeist — wird im gesamten Code **nur von
`jack_stress.py`** aufgerufen, einem Stresstest-Werkzeug. Im normalen Alltag bleibt die Warteschlange
leer; `naechste()` liefert `None`, `dispatch_once()` tut nichts, der Thread im Wächter dreht leer.
**Keine echte parallele Verarbeitung, keine Ressourcen-Konkurrenz — nur ungenutzter, aber
harmloser Code.** Die beiden Systeme sind historisch getrennt entstanden, eins ist faktisch durch
das andere abgelöst worden, ohne je aufgeräumt zu werden.

**`dispatch_once()` — Typen, falls das System doch mal befüllt wird (z. B. bewusst über
`jack_stress.py`):**
- `notiz` — wird sofort als "fertig" markiert, keine echte Ausführung.
- `befehl` — geht durch `jack_oracle.resolve_alias()` + `jack_oracle.is_safe()` (ein **eigenes**
  Sicherheits-Gate, getrennt von der `ALLOWED`-Act-Whitelist aus Kapitel 1!) und wird dann per
  `jack_oracle.run_cmd()` ausgeführt.
- `code` — ruft `jack_coder.write_code()`, setzt Status auf `wartet_freigabe`. **Das ist die
  Quelle des "wartet_freigabe"-Status** — vermutlich verwandt mit der Shadow-Pipeline aus Kapitel 1,
  aber über einen eigenen Weg (`jack_coder`), noch nicht im Detail mit `_run_fix_shadow` verglichen.
- `fix` — eigener Pfad (`_run_fix`), noch nicht im Detail gelesen.
- Vor `code`-Missionen prüft `ressourcen_ok()`, ob genug Kapazität frei ist, sonst wird die Mission
  auf "verschoben" gesetzt statt sofort auszuführen.

**`recover_stale()`** — holt Missionen zurück, die zu lange in einem Zwischenzustand hängen
(vermutlich ähnlich dem Selbst-Neustart-Deadlock-Problem aus Kapitel 1, aber für dieses System;
nie live beobachtet, da die Warteschlange ja praktisch nie befüllt wird).

**Fazit für die Gesamtarchitektur:** Dieses Modul ist ein lebender Beleg dafür, wie das Projekt
gewachsen ist — ein komplettes, funktionsfähiges Aufgabensystem mit eigenem Sicherheits-Gate,
eigener Freigabe-Logik und eigenem Code-Generator, das vollständig durch ein neueres System
(Kapitel 1) ersetzt wurde, ohne je entfernt zu werden. Kein akutes Risiko, aber ein klarer
Aufräum-/Archivierungs-Kandidat, sobald Dima das möchte.

**Offene Fragen für später:** Was genau ist `jack_oracle.py` (eigenes Sicherheits-Gate — wie
verhält es sich zur `ALLOWED`-Whitelist)? Was ist `jack_coder.py` (Code-Generator)? Was macht
`jack_stress.py` genau, und wird es überhaupt noch genutzt?
