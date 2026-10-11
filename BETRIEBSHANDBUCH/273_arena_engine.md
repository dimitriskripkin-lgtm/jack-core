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
- gen2 Flash ohne/mit grep2: 104 -> 112/120, Wins 13 / Losses 5, false_success 16 -> 7, false_alarm 4 -> 1. Tor bestanden.
- Holdout 3 (11.10.2026 21:35, vorgezogen, Tagesgrenze per day_eur_cap auf 3 EUR): 102 -> 110/120, Wins 16 / Losses 8, false_success 17 -> 7, false_alarm 4 -> 1, violations 0. BESTANDEN. Satz in holdout_verbraucht/. grep2 ist seitdem Arena-Standard (ARENA_TOOLS-Vorgabe grep2, ARENA_TOOLS= leer = ohne).

## Sicherheitsrahmen C (11.10.2026 abends)
- Kap 276, jack_arena_sandbox.py: AST-Tor (Positivliste), pytest im begrenzten Subprozess, Dateizustand vorher/nachher. Seit 11.10.2026 verdrahtet (v4, 83/83), C frei.
## Kategorie C v2 (11.10.2026 abends, Plan ChatGPT)
- Generator jack_arena_private/generator/make_c2.py: 11 Typen (K1 Fenster, K2 Schluessel=Wert, K3 Skalieren, K4 Top-n stabil, K5 Zaehler mischen, K6 Gruppieren, K7 Buchungen mit Zustand, K8 Textreihenfolge, K9 Neueste je id, KA Lauflaenge zwei Funktionen, KB freie Zeiten), je Variante 2-3 gekoppelte Bugs, Namen/Grenzen/Daten/Bug-Kombination variieren.
- Sichtbare Tests = Hauptfall (mindestens ein Bug sichtbar), versteckte Tests = Randfaelle/Invarianten/Regression. Fast alle Varianten haben einen Teilfix-Falle (sichtbar gruen, versteckt rot). Erwartungswerte rechnet die Musterloesung, Pruefung im selben Modulzustand wie pytest.
- Jede Variante in der Sandbox geprueft: kaputt faellt sichtbar, Loesung besteht alles, Teilfix sichtbar gruen + versteckt rot. Satz genC2: 88 Aufgaben (Seed 2100, Praefix G), Teilfix-Fallen 87.
- C2-Basis (11.10.2026 abends, genC2 88 Aufgaben, je 1 Lauf, temperature 0):
  Flash A (ohne lambda-Hinweis): 67/88, false_success 13, public_overfit 15, Policy 15 (lambda).
  Flash-Lite A: 46/88, false_success 34, public_overfit 34 (jede falsche Erfolgsmeldung war Teilfix auf sichtbare Tests).
  Flash B (offizielle Basis, code_replace-Doku nennt lambda/Builtin-Namen): 70/88, false_success 12, public_overfit 12, Policy 11 (lambda trotz Hinweis), STUCK 4.
  Schwer fuer Flash: KA Lauflaenge 0/8 (4x gleicher code_replace mit mehrdeutigem old_text = STUCK, 4x Teilfix), KB freie Zeiten 5/8, K6/K7/K9 6/8. Leicht: K1, K2, K3, K5, K8 8/8.
  Richter-Selbsttest mit C2: 1776/1776.
- C2-Aenderung AMBIGUOUS_MATCH (11.10.2026 23:00, vorregistriert): genC2 netto -2 (W5 L7, 84 von 88, Abbruch durch jack_budget-Wochenlimit), false_success 10 -> 14, public_overfit 10 -> 15, STUCK 4 -> 1. Verworfen, Schalter bleibt aus. genC2 fuer Werkzeugaenderungen verbraucht, C2-Holdout QK unbenutzt und versiegelt.
- Merke: jack_budget-Wochenlimit (Schaetzung tokens x 0.40 EUR/Mio, 3 EUR) zaehlt Arena und JACK gemeinsam. Grosse Arena-Serien am Wochenende koennen JACKs eigene Gemini-Aufrufe bis Montag 00:00 sperren.
- Neue Metrik public_overfit (JUDGE_VERSION 4): Richter laesst sichtbare Tests allein laufen; sichtbar gruen + Richter rot = public_overfit, steht in results/runs.jsonl. Auswertung: jack_arena_private/evc2.py.
- C-Basismessung Flash (11.10.2026 21:55, grep2-Standard, fuer C ohne Wirkung): Train 6/6, Dev 2/2, false_success 0, 1.2 Cent. C01-C08 sind fuer Flash zu leicht (Decke wie bei A). Erster Versuch davor (Sandbox v3) verworfen: undefinierter Name wurde als Policy-Verstoss gewertet, siehe Kap 276 v4.
