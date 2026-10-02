## 5. jack_chat_router.py (565 Zeilen, Lane-Klassifikation)

**Zweck:** Entscheidet, ob eine Nachricht eine Fakten-/Status-Anfrage (FACT), eine Diagnose (DIAG),
eine Erklärung (EXPLAIN), eine Zeitfrage (NEU, diese Woche gebaut) oder normales Gespräch (TALK) ist,
und beantwortet die ersten vier Fälle **ohne** einen LLM-Aufruf — schnell, billig, deterministisch.

**`classify(text)`** — reine Schlüsselwort-Erkennung, keine KI. Reihenfolge ist Priorität: NEU zuerst
geprüft (diese Woche ergänzt), dann FACT/EXPLAIN/DIAG, sonst TALK.

**`_tools(text)` — die "Kiste"** (140 Zeilen, der Begriff aus älteren Notizen ist hiermit erstmals
im Code verortet): ein handgeschriebener Sensor-Dispatcher. Erkennt Schlüsselwörter wie "temperatur",
"akku", "knoten zeigen" und ruft dafür gezielt `dumpsys battery` (per SSH auf Xiaomi oder lokal auf
Honor), Graph-Abfragen o. ä. auf. "komplette kiste"/"zeig mir alles" löst mehrere Einzelabfragen
hintereinander aus und fasst sie zusammen. Das ist die Quelle der Ehrlichkeits-Garantie hinter
`JACK_TUNE_NOFAKEACTION` (Kapitel 4) — ein Mess-Wunsch ohne passenden Kiste-Treffer bekommt die
Ehrlichkeits-Anweisung statt einer Antwort.

**Weiterer wichtiger Fund: ein zweiter, unabhängiger Weg, Fakten in den Graph zu schreiben.**
`_is_save_fakt()`/`_do_save_fakt()` in `talk_local()` erkennen Freitext-Merkbefehle direkt im Chat
(z. B. "merk dir: ...") und schreiben **ohne Umweg über eine KI** in den Graph. Das läuft komplett
getrennt von `graph_add_fact` (Kapitel 1, diese Woche für Claude gebaut). **Zwei Schreibwege in
denselben Speicher, die sich nicht kennen** — ähnliches Muster wie die drei Freigabe-Pipelines.

**Korrektur-Erkennung (`JACK_TUNE_LERN1`/`LERN2`):** merkt sich die letzte Nachricht
(`reports/last_msg.json`) und erkennt, wenn Dima sich innerhalb von 2 Minuten selbst korrigiert
(gemeinsame Schlüsselwörter oder explizite Formulierungen wie "hoer auf", "falsch") — schreibt das
als Paar nach `reports/korrekturen.jsonl`. Eine Lernsignal-Erfassung, getrennt von
`jack_learned_rules.md` und `jack_lerner.py` (beide noch eigene Kapitel).

**`dispatch(text, send_keyboard)`** — der zentrale Umschalter: NEU → `neu_report()` (diese Woche
gebaut), FACT → `fact_report()`, EXPLAIN → delegiert an `jack_selfsee.explain()`, DIAG → delegiert
an `jack_selfsee` (mit einer **weiteren**, eigenständigen Bestätigungs-Datei `.selfsee_pending` plus
Ausführen/Abbrechen-Knopf — dieselbe Familie wie `PENDING_EXEC`/`PENDING_WRITE` aus Kapitel 2, aber
eigener Code). Sonst `talk_local()`, und erst wenn das auch nichts liefert: `None` zurück an
`jack_telegram.py`, das dann den LLM-Fallback zieht.

**Gesamtbild der Freigabe-/Bestätigungs-Mechanismen nach fünf Kapiteln:** mindestens fünf eigenständige
Varianten (Shadow+pending_approvals, Self-Tooling-Proposals, PENDING_EXEC, PENDING_WRITE,
selfsee_pending), dazu zwei eigenständige Graph-Schreibwege (`_do_save_fakt`, `graph_add_fact`).
Keine Dopplung ist für sich ein Bug — aber die Summe ist ein klarer Vereinheitlichungs-Kandidat,
sobald die Kartierung fertig ist.

**Offene Fragen für später:** Was ist `jack_selfsee.py` genau (EXPLAIN/DIAG-Logik, Overmind/Deadman)?
Was ist `jack_learned_rules.md` vs. `reports/korrekturen.jsonl` — führt eins ins andere?
