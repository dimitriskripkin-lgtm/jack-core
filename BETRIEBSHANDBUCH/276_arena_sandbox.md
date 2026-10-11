# 276 jack_arena_sandbox.py - Sicherheitsrahmen C fuer die Arena (11.10.2026)
Zweck: Voraussetzung fuer Arena-Kategorie C (Code-Fix mit pytest). Prueflingscode laeuft nie im Runner-Prozess und nur nach drei Schichten. Grundlage: phase2b_aufgaben_BCD.md F3.1 (ChatGPT, Block-Testliste C-SEC-01..16) und Review-Auflagen 1+2 (Claude, phase2b_review3_claude.md).
Status: Modul gebaut und getestet (Selbsttest 60/60 auf dem Honor). NOCH NICHT im Runner/Richter verdrahtet, Kategorie C bleibt gesperrt (BLOCKED_CATEGORIES in jack_arena.py), bis C-Aufgaben, Aktionen und Richter-Teil gebaut sind.

Schicht 1 ast_gate(source): Positivliste, fail-closed. Rueckgabe {ok, code OK|POLICY_BLOCK|SYNTAX_ERROR, reason}.
- Knoten nur aus STMT_OK/EXPR_OK/MISC_OK. Keine Klassen, Lambda, With, Global/Nonlocal, Yield, Walross, Match, async.
- Imports nur math, itertools, re, functools, collections, typing, string, je mit eigener Namensliste (z.B. re ohne re.enum). Keine Untermodule, keine relativen Imports, kein Stern-Import, Modulname darf nicht ueberschrieben werden.
- Modul nur als modul.name nutzbar (nie m = math, nie als Argument). Sonst waeren re.enum.sys / typing.sys Ausbruchswege.
- Namen lesen nur, wenn im Modul gebunden oder in ALLOWED_BUILTINS. Kein Bezeichner mit __ am Anfang. Pruefung auf AST-Namen (NFKC, Vollbreite faellt), nie auf Quelltext.
- Attribute nur aus ALLOWED_ATTRS (oeffentliche Methoden von str/list/dict/set/tuple/int/float/re.Pattern/re.Match/Counter/defaultdict/OrderedDict/deque plus args), nie mit _ am Anfang, ohne format/format_map. Damit faellt gi_frame.f_globals (Generator-Ausbruch).
- Modulebene: nur Docstring, Imports, def, Zuweisungen ohne Aufruf/Comprehension. Keine Dekoratoren, keine Aufrufe in Default-Werten.
- Abweichung von Auflage 1 (bewusst): Expr-Anweisungen innerhalb von Funktionen erlaubt (out.append(x) braucht das); auf Modulebene nur Docstring. ALLOWED_BUILTINS um map, filter, divmod, ord, chr, iter, next, repr, frozenset und einige Exception-Namen erweitert.

Schicht 2 run_pytest(run_dir, tests): Subprozess python -I -B -m pytest -q -p no:cacheprovider -p no:stepwise, leere ini und --rootdir, Umgebung nur PATH/HOME/TMPDIR/LANG (HOME und TMPDIR in einem Seitenordner ausserhalb des Run-Ordners), PYTEST_DISABLE_PLUGIN_AUTOLOAD=1, eigene Prozessgruppe (bei Zeitueberschreitung killpg), Limits CPU, RLIMIT_DATA, FSIZE, NOFILE 64, CORE 0.
- Status: PASSED (rc 0), FAILED (1), ERROR (2 Sammelfehler, z.B. Zielmodul kaputt), NO_TESTS (5), KILLED (Signal), TIMEOUT, INFRA (pytest fehlt, Testpfad unzulaessig). Zusammenfassung max 1500 Zeichen.
- Android-Befund (gemessen 11.10.): RLIMIT_AS unter 16 GB laesst Python nicht starten (SIGABRT), deshalb RLIMIT_DATA. Speicherueberlauf endet per SIGABRT (KILLED), nicht per MemoryError.

Schicht 3 file_state / state_diff: sha256 aller Dateien und Ordner im Run-Ordner vorher/nachher. Nur die ausdruecklich erlaubte Zieldatei darf sich aendern; neue Dateien (conftest.py, __pycache__, .pth), geloeschte oder geaenderte Testdateien = Verstoss. Ehrlicher pytest-Lauf hinterlaesst nachweislich nichts.

Selbsttest: python3 jack_arena_sandbox.py selftest. 39 Blockfaelle (C-SEC-01..16 plus X-01..18: re.enum.sys, typing.sys, Generator-Frame, Modul als Wert, Formatfeld, lambda, Untermodul, relativ, global, Walross, yield, with, Stern, Modul ueberschreiben, type(), Top-Level-Comprehension, __future__, unbekannter Name), 13 Positivfaelle (Loesungsformen C01-C08, math, typing, collections, f-string), 4 Ressourcenfaelle (C-SEC-17 Endlosschleife, 18 Speicherbombe, 18b wachsender Speicher, 19 Rekursion), 5 Zustandsfaelle. Ergebnis Honor: 60/60.
Einzelpruefung: python3 jack_arena_sandbox.py gate <datei.py>.

Naechste Schritte (nach Holdout 3, Runner/Richter vorher nicht anfassen): C-Aktionen code_read / code_replace (nur Zielmodul, expected_sha256) / pytest_run im Runner, Richter-Teil C in jack_arena.py (Tor + pytest + state_diff, Teständerung = FAIL), Aufgaben C01-C08 plus Varianten, Selbsttest Richter, dann C freischalten. Optional spaeter: C auf dem Xiaomi unter eigenem unprivilegierten Benutzer.
Merke: Wer ALLOWED_* erweitert, muss vorher einen neuen Blockfall in SEC schreiben, der den Ausbruchsweg prueft, und den Selbsttest gruen sehen.
