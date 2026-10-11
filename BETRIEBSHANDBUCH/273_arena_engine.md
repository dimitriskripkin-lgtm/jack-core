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
