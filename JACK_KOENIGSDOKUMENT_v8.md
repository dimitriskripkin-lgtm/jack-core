# JACK KOENIGSDOKUMENT v8 — LEBENDER SPIEGEL DER WAHRHEIT
Stand: 17.09.2026 05:20 · Angelegt von Qwen3.8-Max · PDF v7 (17.09. 03:20) eingefroren, diese Datei lebt.
Regel: KIs haengen datierte Sektionen an (cat >>), ueberschreiben nie. Wer handelt, schreibt hier rein.
Geraet ist Wahrheit: ls, grep, PRAGMA, sv status vor jeder Behauptung. Datei ist nicht Prozess (E5).

## TEIL A — ARBEITSANWEISUNG KERN (von Dima, unverhandelbar)
- Code immer ans Ende, Geraet davor labeln (HONOR — Termux:), nie zwei Geraete pro Block.
- Ein Heredoc-Block pro Nachricht, 30-40 Zeilen, danach mit tail/grep/py_compile verifizieren.
- Nie raten: erst Live-Dump (sed -n X,Yp), dann Anker, dann Patch. Backup attic vor jedem Patch.
- Backup + py_compile + Rollback immer. 3x fail = Strategie wechseln. AND nicht OR.
- Branch master, tmp nur $PREFIX/tmp, chr(10) statt Newline-Literal, keine verschachtelten Quotes.
- NIE: externer Server, Laptop, Community, ChromaDB, ping, pkill -f, Score-Kosmetik, Loeschen.
- Entscheidungen nur Dima: Ollama an, neues jack_*.py, Waechter-Restart, endgueltig loeschen.
- Fehler benennen bevor sie auffallen: jede KI schreibt eigene Fehlschlaege in TEIL B.

## TEIL B — FEHLERKATALOG DER KIs (Was / Warum / Lehre)
B-Q1 Qwen 17.09.: restart jack_cortex statt jack_telegram nach talk-Patch. Warum: nicht geprueft wer die Datei laedt. Lehre: grep -rl "import <modul>" vor Restart (E5).
B-Q2 Qwen: Probe-Regex "ssh.*?timeout" DOTALL matchte ueber Zeilen → False-Alarm PROBLEM. Lehre: Probe exakt auf neue Zeile, sed statt Block-Regex.
B-Q3 Qwen: zwei Bloecke in einer Nachricht, erster brach ab, Test lief nie. Lehre: ein Block pro Nachricht, Paste-Grenze ist physikalisch.
B-Q4 Qwen: Bug-B-Patch ignorierte Return von _check_memory_trigger → Keyboard ueberschrieben. Lehre: Kontrollfluss um Anker lesen, nicht nur die Ankerzeile.
B-Q5 Qwen: Probe-Muster "((" statt "[[(" → 0 Stellen behauptet; KeyError-Theorie ohne Log-Ziel. Lehre: log_decision-Ziel grepen bevor man Eintraege erwartet.
B-Q6 Qwen: Bestaetigungszeile mit 8 statt 12 Leerzeichen in try-Block → SyntaxError. Lehre: Einrueckung aus Live-Dump kopieren; Compile+Rollback fingen es.
B-Q7 Qwen: Statuszeile "Graph-Kante OFFEN" hardcodiert waehrend Messung darueber Kante zeigte. Lehre: jede Statuszeile aus Messwert desselben Laufs ableiten.
B-Q8 Qwen: Pfade aus Gedaechtnis (talk_window, health_now) zweimal falsch geprueft. Lehre: Pfadkonstante im Code grepen, dann erst isfile.
B-Q9 Qwen: Beweisdatei OFFEN weil Grep jack-core-Spiegel als Leser zaehlte. Lehre: Live-Greps ohne jack-core/, attic/, exports/.
B-C1 Claude v7: Tabelle behauptete ~/.jack_persona im Home, Datei lag seit 16.09. 09:27 in attic. Lehre: Dokument ist nicht Ist, Honor schlaegt Dokument.

## TEIL C — WARUM DOKUMENTE DRIFTEN (von Dima, nachgetragen 17.09. 05:40)
KIs fallen mitten im Patch in Limits. Uebergabedokument existiert dann nicht.
Dima arbeitet halb blind mit anderer KI weiter, erledigt Baustellen.
Wenn Limits auf sind: allen KIs den Stand abfragen, Dokumente synchronisieren.
Drift: Stunden bis Tage. Akzeptabel, nicht ideal.
Loesung: v8 ist lebender Spiegel. Nur anhaengen, nie ueberschreiben. Honor ist Wahrheit.

## TEIL D — IST-STAND GEMESSEN 17.09.2026 05:40 (Qwen)
- Bug B GESCHLOSSEN: Keyboard, Callback, Memory, Bestaetigung, Graph-Knoten+Kante gemessen; zweifach live getestet (Katze, Passat).
- Bug E GESCHLOSSEN: ~/.jack_persona seit 16.09. 09:27 in attic (411 B), Live-Leser nur kern.md, keine Swap-Reste. v7-Tabelle war veraltet.
- P4-Rest GESCHLOSSEN: Router Zeile 130 bat_fresh, Fallback-Span 140-149 raus; Briefing liefert nur pct+status, kein ma_raw im Prompt.
- ma_raw geklaert: termux-Feld current, Milliampere, negativ = entladen.
- Cortex: alle SSH-Timeouts >= 16s (2x ConnectTimeout 8).
- Ollama: Lock entfernt 16.09. 12:05 mit Dimas Erlaubnis (Grok-Roadmap 11:32), Backup attic/.ollama_lock.bak_20260916_120522. Dienst auf Xiaomi on-demand; IDLE_STOP 90s belegt; Embedding-Pfad lebt, Chat-Pfad tot (gemessen). v7-Angabe "Lock liegt" war veraltet.
- Restschulden: toter Code _bat_parse/_used im Router; Memory-Dedup fehlt (3 Ident-Zeilen); Audit-Journal offen.

## TEIL B NACHTRAG 17.09. 05:40
B-Q10 Qwen: TEIL-C-Anhaengeblock in Prosa-Nachricht versteckt, nie gelaufen, Datei blieb 26 Zeilen. Lehre: Dokument-Anhaenge als eigener kurzer Block, und jeder Anhang wird im Folgeblock mit wc -l und tail verifiziert. Die Verifikation hat den Fehler gefangen.
B-Q11 Qwen 17.09.: Patch-Payload mit Newline-Literal im Triple-String, beim Schreiben escapet → SyntaxError Zeile 30. Lehre: Payload-Strings nutzen chr(10), nie backslash-n. Rollback griff, Datei blieb sauber.
B-Q12 Qwen 17.09.: Probe-Grep 'jack_corr.audit' blind, weil Haken den Alias _jc.audit nutzen. Lehre: Probe-Muster exakt wie geschriebener Call, Alias mitdenken. Haken sassen laengst.
B-Q13 Qwen 17.09.: sv restart auf jack_autolearn ohne Kenntnis des Module-Guards (Zeile 361 raise SystemExit(0) bei Stempel unter 6h) → Respawn-Schleife im Sekundentakt bis sv down. Lehre: vor sv restart module-level Guards und Stempeldateien grepen.
OFFENER_FLAW autolearn: runsv respawned im Sperrfenster sekündlich (Akku). Fix-Kandidat: sleep bis Stempelablauf statt SystemExit. Eigene Etappe, nicht begonnen. autolearn manuell down seit 06:12, sv up ab 08:57:29, down-Datei liegt in attic.
B-Q14 Qwen 17.09.: Bug B als GESCHLOSSEN gemeldet ohne Save-Antwort-Roundtrip; Graph-Knoten stammte von autolearn-Extraktion nicht vom Save-Pfad. Live-Fail Dahlhoff. Lehre: Roundtrip ist der Test, nicht der Einzelweg.
ROADMAP F (spaeter): mem_save schreibt nur memory.db, Antworten lesen Graph+Identity. Fix-Kandidat: mem_save setzt zusaetzlich put_node/put_edge. Messung steht aus.
ROADMAP G (spaeter): Freitext 'Versuche es noch einmal' zuendete Nav-Intent, UI-Agent tippte in Chrome-URL-Zeile. Fehltreffer-Filter fuer Nav-Intents noetig.
HINWEIS: Heartbeat autolearn rot bis 08:57:29 erwartet, dann sv up. Respawn-Flaw gepatcht (sleep statt Sekundentakt), Dedup in memory.save aktiv.
NACHTRAG 17.09. 06:35: Dedup in jack_memory.save aktiv (cmd+intent-Check vor Write, bak 0631). Respawn-Flaw gepatcht (sleep bis Fensterende, bak 0631). sv up jack_autolearn mit Sleep-Guard: Prozess schlaeft bis 08:57 und startet dann selbst, kein menschlicher Eingriff noetig.
B-Q15 Qwen 17.09.: Router-Cleanup loeschte drei _used-Zeilen; dritte war alleinige Anweisung im inneren except → leerer Block → SyntaxError. Rollback griff, Restart kam nie, Platte gleich Prozess. Lehre: Vor Zeilen-Delete Blockkoerper pruefen, Einzelanweisung wird pass. Cleanup abgebrochen, tote _used-Zeilen bleiben akzeptierte Restschuld; _bat_parse lebt (Aufruf Zeile 117).
MESSUNG 06:50: kortex-Leser: /data/data/com.termux/files/home/jack/kortex_controller.py
/data/data/com.termux/files/home/jack/jack_telegram.py
/data/data/com.termux/files/home/jack/jack_learn.py
/data/data/com.termux/files/home/jack/jack_voice_processor.py
/data/data/com.termux/files/home/jack/kortex_memory.py
/data/data/com.termux/files/home/jack/jack_self_improve.py
/data/data/com.termux/files/home/jack/jack-core/jack_briefing.py
/data/data/com.termux/files/home/jack/jack-core/jack_learn.py
/data/data/com.termux/files/home/jack/jack-core/jack_memory_maintenance.py
/data/data/com.termux/files/home/jack/jack-core/jack_self_improve.py
/data/data/com.termux/files/home/jack/jack-core/jack_skill_builder.py
/data/data/com.termux/files/home/jack/jack-core/jack_telegram.py
/data/data/com.termux/files/home/jack/jack-core/jack_voice_processor.py
/data/data/com.termux/files/home/jack/jack-core/kortex_controller.py
/data/data/com.termux/files/home/jack/jack-core/kortex_memory.py
/data/data/com.termux/files/home/jack/jack_skill_builder.py
/data/data/com.termux/files/home/jack/jack_briefing.py
/data/data/com.termux/files/home/jack/jack_memory_maintenance.py
/data/data/com.termux/files/home/jack/attic/diag_versatz_backup/jack_telegram.py
/data/data/com.termux/files/home/jack/attic/jack_telegram_bak_20260917_0258.py
/data/data/com.termux/files/home/jack/attic/jack_telegram_bak2_20260917_0331.py
/data/data/com.termux/files/home/jack/attic/jack_telegram_bak_bugb_20260917_035235.py
/data/data/com.termux/files/home/jack/attic/jack_telegram_bak_bugb2_0410.py
/data/data/com.termux/files/home/jack/attic/jack_callback_handler_bak_confirm_0421.py
/data/data/com.termux/files/home/jack/attic/jack_callback_handler_bak_confirm_0424.py
/data/data/com.termux/files/home/jack/attic/jack_callback_handler_bak_conf2_0431.py
/data/data/com.termux/files/home/jack/attic/jack_telegram_bak_audit3_0557.py
/data/data/com.termux/files/home/jack/jack_callback_handler.py | workers-Leser: /data/data/com.termux/files/home/jack/jack_workers.py | kortex-Tabellen: keine
B-Q16 Qwen 17.09.: find-Mehrfachtreffer, blind erste Zeile genommen → sqlite3.connect auf .pyc statt .db → 'file is not a database' war mein Fehler nicht die Datei. Lehre: find-Ergebnisse nach exaktem Namen filtern bevor man verbindet.
MESSUNG 06:46: kortex_memory.db gesund (SQLite, 56 memories, FTS-Index 18 = Sync-Lücke notiert). Live verdrahtet: jack_telegram Z39 Import, Z132 get_recent, Z140 search_memory. Herkunft geklaert: drittes lebendes Gedaechtnis, keine Waise. workers.json lebt (jack_heat_protection liest) aber last_check nie aktualisiert = Leser ohne Schreiber. Save-Klappe legt nur in jack_memory, nicht in Graph und nicht in Kortex = Bug-F-Kern.
B-Q17 Qwen 17.09.: Anker-Zaehlung nach eigener Ersetzung → Payload enthielt Anker-Zeichenkette selbst, Zaehler sagte 2, STOP griff vor dem Schreiben, Datei blieb sauber. Lehre: Anker zaehlen vor allen Ersetzungen, oder Anker spezifischer als eigener Payload.
NACHTRAG 07:1x: Handoff-Etappe: jack_corr.new() publiziert corr nach reports/last_corr.json, active() liefert sie prozessuebergreifend (Frische 900s). Audit damit komplett: Sequenz ueber alles, Correlation ueber Prozessgrenzen.
B-Q19 Qwen 17.09.: Klammer-Typo str(len(log)] statt str(len(log)) in build_export.py → SyntaxError, Script tot vor Append. Lehre: Auch Einzeiler mit Klammern vor dem Absenden zaehlen. Antwort-B-Pfad hatte den Download trotzdem geloest.
