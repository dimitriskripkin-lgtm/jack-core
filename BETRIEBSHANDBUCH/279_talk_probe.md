# 279 jack_talk_probe.py - Gespraechs-Arena: Proben ohne Schreibwirkung (12.10.2026)
Zweck: JACKs Gespraechsfaehigkeit messen, ohne dass Testsaetze in sein Gedaechtnis oder seine Lernsignale gelangen. Idee Dima (Wartezeit nutzen), Design mit ChatGPT (probe_mode, zwei Ebenen, Claim-Richter).
Aufruf: python3 jack_talk_probe.py ask <unit|e2e> "<frage>" | selftest. Protokoll: ~/jack_arena_private/talk/probes.jsonl (privat, 600).
Ebenen: unit = jack_talk.talk_to_gemini(frage) (Antwort schon durch _scrub_out). e2e = jack_telegram.handle(frage), also der echte Weg mit Router-Lanes (NEU/FACT/...), Sendefunktionen abgefangen.
probe_mode (jede Probe eigener Kindprozess, Sperre vor dem Import von JACK-Modulen):
- Dateischreiben unter HOME -> Overlay im Temp-Ordner (open, io.open, os.open, os.replace/rename/remove, mkdir). Ausnahme nur Kostenzaehlung: .api_budget, .api_budget_week, reports/groq_usage.jsonl.
- SQLite unter HOME -> beim ersten Zugriff per Backup ins Overlay kopiert, Schreiben trifft nur die Kopie (db_changed im Protokoll).
- Unterprozesse nur Lese-Liste (dumpsys, getprop, uptime, df, free, date, termux-battery-status, git log/show/diff/...), sonst PROBE_DENY. Netz zu Telegram verweigert.
- Folge: Proben beeinflussen sich nicht gegenseitig (jede sieht den Produktionszustand, nicht die vorige Probe).
Selftest (Kanarienwort, Positivkontrolle): 4 Proben inkl. "merk dir", Korrektur, Talk; 26 Schreibversuche abgefangen (jack_graph.db, jack_memory.db, last_msg.json, promptlog, decisions, audit_journal, jack.log, Session-ID), Lecks: keine. Lecksuche = jede Datei unter HOME, die seit Probenbeginn geaendert wurde, auf das Kanarienwort pruefen.
Erster Befund (e2e, 12.10.): "Hast du die Arena bemerkt", "Was ist in den letzten 48/24 Stunden im Code passiert" -> "Ich weiss das nicht". "Was hat sich in den letzten Stunden getan?" -> echte Commits (NEU-Lane, neu_report). Ursache: classify() kennt nur feste Woerter ("letzten stunden" ohne Zahl), neu_report hat fest 10 Stunden. Die Faehigkeit existiert, der Weg dorthin nicht. Reparatur erst nach Fragensatz + Basismessung (keine Nachkorrektur einzelner Saetze).
Offen: Fragensatz (Uebung + versiegelter Holdout), eingefrorener Fakten-Snapshot pro Probe, Claim-Richter (belegt/falsch/erfunden/ehrlich unbekannt/verfuegbar verpasst/teilweise, RETRIEVAL_ERROR getrennt, Zeitgrenzen und veraltete Daten).
