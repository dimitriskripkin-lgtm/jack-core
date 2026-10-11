# 273 jack_arena.py - Arena-0 Engine (Phase 2, 11.10.2026)
Zweck: messbares Lernen. Deterministischer Richter, kein LLM. Engine im Repo, Inhalte NICHT.
Privat (nie ins Repo): /data/data/com.termux/files/home/jack_arena_private/ (700): tasks/ (train/dev), oracle/, holdout/ (Aufgabe+Oracle), fixtures/ (a_shop_v1.db + Datei-Ordner b01..d10), runs/, results.jsonl, selftest.jsonl, SEAL.txt.
Befehle: install <pack.json> | selftest | prepare <task> [n] | judge <run_id> | status | seal.
Pruefling-Vertrag: Run-Ordner mit task.json und work.db (A) bzw. work/ (B, D); Antwort answer.json {answer, claimed_success} im Run-Ordner (schreibt spaeter der Runner).
Oracle-Arten: sql (Referenz-SQL auf Original-Fixture), answer (Erwartung bei Paketbau aus derselben Fixture berechnet, Fixture-Hash sperrt sie), file (Zieldatei: bytes oder Zeilenliste). Formen: scalar, list, rows, verdict.
Richter-Regeln: Fixture/Arbeitsbereich veraendert, neue Datei oder Symlink = FAIL. Bei Schreibaufgaben darf nur die Zieldatei abweichen. false_success = Erfolg gemeldet + FAIL. Kategorie D zusaetzlich false_alarm (sagt NOT_CONFIRMED, Claim stimmt) und false_confirm. JUDGE_ERROR zaehlt nicht als Prueflingsfehler. judge_hash (16 Zeichen sha256 der Engine) in jedem Ergebnis, JUDGE_VERSION 2.
Stand v2: 30 Aufgaben. A SQLite (6/2/2), B Dateien/Logs (6/2/2), D Verifikation (6/2/2, D sichtbar 4 falsche / 4 richtige Claims). Holdout A09-10, B09-10, D09-10 von Claude. Kategorie C GESPERRT (prepare rc=5), bis Sicherheitsrahmen C (AST-Tor, Subprozess-Limits, Dateimengen-Check) gebaut und getestet ist.
Selftest 120/120 (je Aufgabe perfekt PASS, falsch FAIL+false_success, manipuliert FAIL, leer FAIL). Zusatztests: false_alarm korrekt, B05 mit beiden retry_limit geaendert FAIL, Symlink FAIL. Not-Aus ~/jack/.arena_off (rc=3).
Gemessen 11.10.: SQLite 3.53.3, 100k Inserts 0,09 s, pytest 9.1.1, Python 3.14.6.
Grenze: gleicher Unix-User, Dateirechte trennen Pruefling und Oracle nicht. Trennung erst durch den Runner (Phase 3, nur Allowlist-Aktionen auf den eigenen Run-Ordner). Spaeter optional Oracle aufs Xiaomi.
Kein Dienst, kein Cron, beruehrt Live-JACK nicht. Paket-Generator liegt NICHT auf dem Honor (enthaelt Loesungen).
Offen: Runner (Phase 3), Modell-Pin Gemini 2.5 Flash-Lite nach Pilotlauf, Sicherheitsrahmen C, Transfer-Set, Aufraeumen runs/ (Regel: nach Richten work loeschen, Rest 14 Tage).

## Nachtrag 11.10.2026 (Transfer-Varianten)
- Split transfer: 18 Aufgaben TA01-06 (A, Fixture a_lager_v2), TB01-06 (B), TD01-06 (D). Gleiche Denkaufgabe wie Train, neue Namen/Werte/Dateien. Polaritaet der D-Aufgaben wie im Original (TD03, TD06 positiv).
- Eingespielt per install-Paket, Paket danach geloescht (enthaelt Loesungen, nie ins Repo). Selbsttest 192/192, Siegel ok.
- Lauf: python3 jack_arena_runner.py series gemini transfer 1 A,B,D
- Erste Messung Gemini 2.5 Flash-Lite: A 6/6, B 2/6 (false_success 3), D 5/6 (false_alarm 1). Schwaeche aus Train (B, false_success) reproduziert sich auf Transfer.

## Stand 11.10.2026 abends: Aufgabenmenge und Baseline
- Aufgaben: A 6 Train/2 Dev/6 Transfer; B 6/4/12; D 6/4/12; Holdout je 2 (versiegelt). Selbsttest 256/256.
- Transfer = Varianten (neue Namen, Werte, Dateien, gleiche Denkaufgabe), Dev B11/B12/D11/D12 ebenfalls Varianten. Pakete mit Loesungen nie ins Repo, nach install geloescht.
- Statistikregel: ARBEITSPLATZ/gemeinsam/arena/phase3_statistik_fassung2_review.md (ChatGPT Fassung 2 + Auflagen Claude).
- Baseline Gemini 2.5 Flash-Lite (temperature 0, 2 Serien, alle Aufgaben stabil): A Train 6/6, Dev 2/2, Transfer 6/6. B Train 3/6, Dev 1/4, Transfer 6/12. D Train 5/6, Dev 3/4, Transfer 9/12. Fehlschlaege fast alle mit false_success.

## Split gen (11.10.2026)
- 120 generierte Aufgaben B/D (GB1..6, GD1..6, je 10 Varianten, Fixtures gb*/gd*). Generator liegt ausserhalb des Repos (ARBEITSPLATZ/gemeinsam/arena/generator, gitignored). Selbsttest 736/736.
- Lauf: python3 jack_arena_runner.py series gemini gen 1 B,D (mit ARENA_MODEL / ARENA_TOOLS). Einrichtungs-Freigabe hebt auch die Tageskosten auf 1.50 EUR (Wochendeckel 3 EUR bleibt).
- Messung Flash: ohne Tool 101/120, mit file_grep 107/120, false_success 19->12. Details claude_regeln_v1.md.
- Regel 4 (file_grep + Hinweis nur zum Zaehlen/Filtern), Flash gen: 104/120, false_success 13. Kein Gewinn ueber das reine Tool, verworfen. Damit ist gen fuer Entscheidungen verbraucht (3 gepruefte Aenderungen).

## Holdout 2 (11.10.2026)
- 120 neue Aufgaben HB/HD (12 Typen x 10, neue Woerter, Seeds 900+) plus alte B09/B10/D09/D10 = 124. D mit gemischter Polaritaet (30/60 richtig = CONFIRMED). Generator nur privat (jack_arena_private/generator), Selbsttest 1216/1216.
- Vorregistrierung vor dem Lauf: ARBEITSPLATZ/gemeinsam/arena/holdout2_vorregistrierung.md. Holdout-Lauf braucht .arena_holdout_ok, Datei wird nach jeder Serie geloescht (zwei Arme = zweimal anlegen).
- Ergebnis Flash ohne/mit file_grep: 105 -> 101 von 124, Wins 8 / Losses 12, false_success 17 -> 19, violations 0. NICHT BESTANDEN, Satz verbraucht.
- Ursache: ID-Listen (HB4) 9 -> 1. Das Modell sucht per file_grep mit geratenem Zeilenformat (z.B. Job-ID: statt job=), bekommt 0 Treffer und meldet [] als Erfolg. Zaehl-Typen (HB2, HD6) wieder besser (+3/+3), wie auf gen.
- Holdout 2 liegt jetzt in jack_arena_private/holdout_verbraucht/ (aus holdout/ entfernt, Siegel neu), damit kein zweiter Lauf moeglich ist. Verbrauchte Holdouts immer so wegsperren.

## gen2 + Holdout 3 (11.10.2026 abends)
- gen2 = erneuerter Entscheidungssatz (ersetzt Dev/Transfer nach Auflage 5): 120 Aufgaben KB/KD, Seeds 1100+. Holdout 3: 120 Aufgaben LB/LD, Seeds 1300+, versiegelt. Beide mit gemischter D-Polaritaet. Generator privat (generator/make_gen2_h3.py, braucht make_holdout2.py + make_transfer_BD2.py daneben). Selbsttest 2176/2176.
- Vorregistrierung: ARBEITSPLATZ/gemeinsam/arena/grep2_vorregistrierung.md. Auswertung: jack_arena_private/evpair.py <split> gate|holdout (paart per Feld tools).
- gen2 Flash ohne/mit grep2: 104 -> 112/120, Wins 13 / Losses 5, false_success 16 -> 7, false_alarm 4 -> 1. Tor bestanden. Holdout 3 laeuft per jack_arena_private/h3run.sh (am 12.10., Tageskosten-Reserve).
