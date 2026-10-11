# 274 jack_arena_runner.py - Arena-Runner (Phase 3, 11.10.2026)
Zweck: fuehrt einen Pruefling durch eine Arena-Aufgabe und laesst danach den Richter (jack_arena.py, Kap 273) urteilen.
Befehle: run <task> <gemini|dummy> [wdh] | series <agent> <split> <wdh> [A,B,D] | selftest | kosten | bericht [agent] [alle].
Pruefling sieht nur: Aufgabe (task_id, instruction, answer_format) + Antworten auf seine Aktionen. Keine Pfade, kein Oracle, kein Shell, kein Netz.
Aktionen: sql_read (mode=ro, PRAGMA query_only, set_authorizer nur SELECT/READ/FUNCTION/RECURSIVE ohne load_extension, Progress-Handler 2 s, 200 Zeilen), file_list, file_read (mit sha256, 4000 Zeichen), file_replace (nur freigegebene Datei, expected_sha256, old_text genau 1x), file_write (nur freigegebene neue Datei, eigene ueberschreibbar), file_stat, file_hash. Nur einfache Dateinamen, Praefix work/ wird akzeptiert, Symlink/versteckt/Traversal = POLICY_BLOCK.
Limits: Aktionen min(Aufgabe, 30); 3 Policy-Verstoesse = Stop POLICY; dreimal dieselbe fehlerhafte Nachricht = Stop STUCK; Zeitlimit der Aufgabe; Run 20.000 Tokens / 0,05 EUR; Arena-Tag 0,50 EUR und 300 Modellaufrufe (seit 11.10. 14 Uhr, vorher 150); zusaetzlich jack_budget.check_and_count(text) und add_tokens (zaehlt gegen JACKs 300 Aufrufe/Tag).
Modell: gemini-2.5-flash-lite fest im Runner (nicht aus jack_config, damit Vergleiche stabil bleiben), temperature 0, thinkingBudget 0, JSON-Antwort, Schluessel ueber jack_gemini_bridge, Header statt URL. Preisstand P1-20261011 (0,10/0,40 USD je Mio., 0,8925 EUR/USD).
Antwort-Vertrag: Runner schreibt answer.json selbst. D-Antwort muss Objekt {verdict, evidence_code} sein. Antwort als JSON-Text verpackt wird ausgepackt und als format_repaired gezaehlt.
Protokolle (privat): runs.jsonl (echte Prueflinge), selftest_runs.jsonl, costs.jsonl, runs/<id>/ mit run.json, answer.json, result.json, transcript.jsonl; Arbeitskopie wird nach dem Richten geloescht. Holdout nur mit ~/jack/.arena_holdout_ok (wird nach Serie geloescht). Lock gegen Doppellauf.
Selbsttest (ohne Modell, kostenlos): 34 Policy-Faelle, Orakel 30/30 ueber echte Aktionen, Dummy, Boese (Stop POLICY nach 3), D-Textantwort, Festgefahren.
Pilot 11.10.: Lauf 1 deckte zwei Runner-Fehler auf (work/-Praefix bei file_replace/file_write blockiert; D-Antwortform nicht geprueft), beide behoben. Lauf 2 (Train, 18 Aufgaben): A 6/6, B 3/6, D 3/6; echte Modellfehler B01 (418/1418 verwechselt), B02 (ERROR falsch gezaehlt), B03 (falscher neuester Status), D02 (9 statt 12 Datensaetze als CONFIRMED gemeldet = false_success). D01/D05 inhaltlich richtig, aber Antwort als Text verpackt und bei temperature 0 endlos wiederholt -> Fix v1.1. Kosten aller 39 Laeufe 0,0127 EUR, Mittel 0,0003 EUR/Lauf. Lauf 3 (v1.1, mit Einmal-Freigabe der Tagesgrenze) 14/18: A 6/6, B 3/6, D 5/6. Alle 4 Fehler echt und alle mit claimed_success=true (false_success 4): B01 falsche Datei, B03 falscher Status, B04 ID 27 uebersehen, D02 9 statt 12 bestaetigt. Eine Promptzeile mehr hat B02 (jetzt richtig) und B04 (jetzt falsch) gekippt: Prompt-Rauschen, Aenderungen nur ueber Netto-Gewinn vieler Aufgaben bewerten. Einmal-Freigabe: ~/jack/.arena_einrichtung mit YYYY-MM-DD N gilt nur an dem Tag (max 300), danach geloescht.
Befund Statistik: bei temperature 0 wiederholen sich Laeufe praktisch identisch (gleiche Tokenzahlen). Wiederholungen bringen kaum Information; Rauschen eher ueber mehr Aufgaben/Transfer-Varianten messen.
Engine-Aenderung 11.10.: prepare macht run_id bei Kollision eindeutig.
Not-Aus: ~/jack/.arena_off. Kein Dienst, kein Cron.
Offen: Pilot 3, Baseline (Train+Dev, 2 Serien), Phase 4 erste Regel, Transfer-Set, Kategorie C mit Sicherheitsrahmen.

## Nachtrag 11.10.2026
- Einrichtungs-Freigabe .arena_einrichtung ('YYYY-MM-DD N', nur an dem Tag) darf jetzt bis 1000 gehen (vorher 600). Normalgrenze DAY_CALLS bleibt 300. Datei nach Gebrauch loeschen.
- jack_budget text-Grenze seit 11.10. 1000 (Dima). Dienste, die jack_budget beim Start laden, haben bis zum naechsten Neustart noch 600 im RAM.

## Phase 4 Schalter (11.10.2026)
- ARENA_RULES_FILE=<datei>: Regeltext wird an den Prompt gehaengt, rules_hash aendert sich. Ohne Variable = Baseline.
- ARENA_TOOLS=grep: aktiviert lesendes Werkzeug file_grep (nur wo file_read erlaubt). Ohne Variable = Baseline.
- Regelstatus und Messungen: ARBEITSPLATZ/gemeinsam/arena/claude_regeln_v1.md. Regel 1 (erst pruefen) verworfen, Regel 2 (file_grep) offen.
- Merke: pkill -f in einem exec trifft die eigene Kommandozeile. Laeufe per Pidfile oder 'ps | grep [x]' beenden, und danach pruefen, ob wirklich nichts mehr laeuft.
- ARENA_MODEL=gemini-2.5-flash waehlt das Pruefling-Modell (Whitelist: gemini-2.5-flash-lite = Standard, gemini-2.5-flash). Preis je Modell in _MODELS (price_version P1 Lite, P2 Flash). Aufgaben mit leerer rules_hash und anderem model_id sind getrennte Messreihen.
- Agent claude (11.10.2026): ClaudeAgent nutzt die Anthropic Messages API. Der Schluessel (Name beginnt mit ANTHROPIC) steht in ~/.jack_secrets, nie ausgeben. Modell per ARENA_CLAUDE_MODEL (Whitelist claude-haiku-5-5 = Standard, claude-sonnet-5-5). Preise je Mio. Token: Haiku 0.10/0.50 USD (Prompt bis 100k), Sonnet 2/10 USD (platform.claude.com/docs/en/about-claude/pricing, 11.10.2026). Aufruf: python3 jack_arena_runner.py series claude train 1 A,B,D. temperature 0, max_tokens 1024, gleicher Prompt und gleiche Limits wie Gemini.
