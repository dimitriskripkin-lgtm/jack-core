# 276 jack_arena_sandbox.py - Sicherheitsrahmen C fuer die Arena (11.10.2026)
Zweck: Voraussetzung fuer Arena-Kategorie C (Code-Fix mit pytest). Prueflingscode laeuft nie im Runner-Prozess und nur nach drei Schichten. Grundlage: phase2b_aufgaben_BCD.md F3.1 (ChatGPT, Block-Testliste C-SEC-01..16) und Review-Auflagen 1+2 (Claude, phase2b_review3_claude.md).
Status: v4 (83/83), seit 11.10.2026 nach Holdout 3 im Runner und Richter verdrahtet, Kategorie C frei (C01-C06 Train, C07-C08 Dev).

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

## v2 (11.10.2026 abends, nach Review ChatGPT)
- C-SEC-20 Scope-Vergiftung (echte Luecke in v1, von ChatGPT gefunden): Bindungen wurden modulweit gesammelt. Ein Parameter open in Funktion A gab das echte open in Funktion B frei. Fix: kein Name aus dir(builtins) darf gebunden werden (Parameter, Zuweisung, Comprehension-Ziel, Import-Alias, except-Name), ausser er steht in ALLOWED_BUILTINS. Faelle 20, 20b-e.
- C-SEC-21: Attribute nur lesen (kein Schreiben/Loeschen/AugAssign auf Attributen), sonst koennte Zielcode re/collections umbiegen und Tests beeinflussen.
- C-SEC-23: Annotationen nur einfache Typformen (Name, Attribut, Subscript, Tuple/List, X | None). Kein Aufruf, keine Comprehension, keine String-Annotation (Python 3.14 wertet Annotationen verzoegert aus).
- C-SEC-22: pytest-Ausgabe wird schon beim Lesen begrenzt (OUT_MAX 1 MB, nur die letzten 16 KB im Speicher). Darueber: Prozessgruppe getoetet, Status OUTPUT_LIMIT. Vorher sammelte communicate() alles im Runner-Speicher.
- Schluesselwort-Argumente (dict(type=1)) binden nichts und sind erlaubt.
- Selbsttest Honor v2: 76/76.

## v3 (11.10.2026 21:4x, Review 2 ChatGPT)
- C-SEC-24: Kodierungsangabe (PEP-263-Cookie in Zeile 1-2) und BOM verboten. gate_file(path) prueft die gespeicherten Bytes strikt als UTF-8; Runner schreibt das Zielmodul nur als UTF-8-Bytes. So sehen Tor und Interpreter denselben Text.
- C-SEC-25: Waehrend pytest darf sich im Run-Ordner gar nichts aendern, auch das Zielmodul nicht. run_pytest macht Schnappschuss vorher/nachher, Abweichung = Status STATE_CHANGED (immer Fehlschlag, im Runner Policy-Verstoss).
- Vertrag Testdaten: sichtbare und versteckte Tests uebergeben an Prueflingsfunktionen nur einfache Werte (Zahlen, Texte, Listen, Tupel, Dicts, None). Keine Dateien, Pfade, Module, Callables, pytest-Fixtures wie monkeypatch. Grund: fremde Objekte koennen ueber Operatoren/repr/Methoden eigenen Code ausfuehren. C01-C08 halten das ein; neue C-Aufgaben pruefen.
- Versteckte Tests laufen nur im Richter (Kopie des Arbeitsbereichs). pytest_run im Runner sieht nur test_*.py im Arbeitsbereich, versteckte Testnamen oder Assertions erreichen den Pruefling nie.
- Selbsttest Honor v3: 82/82.

## v4 (11.10.2026 22:0x, nach erster C-Messung)
- Befund: Flash schrieb bei C08 Code mit einem undefinierten Namen (out). v3 wertete das als Policy-Verstoss (Name nicht erlaubt), drei Versuche = Stop POLICY. Das ist ein Programmierfehler, kein Angriff, und verzerrte policy_violations.
- Fix: Lesen eines Namens blockt nur noch, wenn er ein nicht erlaubtes Builtin ist (FORBIDDEN_BIND) oder ein Dunder. Unbekannte ASCII-Namen sind erlaubt und ergeben zur Laufzeit NameError (kein globals/setattr/Stern-Import, Modulnamen nur aus geprueften Anweisungen, Builtin-Bindung verboten -> kein Ausbruch).
- Nicht-ASCII-Bezeichner bleiben fail-closed (Homoglyphen, C-SEC-10b). Vollbreite normalisiert der Parser zu ASCII und faellt als Builtin.
- Selbsttest Honor v4: 83/83 (neu P-18 undefinierter Name).

## Verdrahtung (11.10.2026 nach Holdout 3)
- Runner: Aktionen code_read, code_replace (AST-Tor vor dem Schreiben, nur UTF-8, Syntaxfehler = INVALID_ARGS ohne Verstoss, Tor-Verstoss = POLICY_BLOCK), pytest_run (Tor auf Datei, nur sichtbare test_*.py, Pfade aus der Ausgabe entfernt, STATE_CHANGED = Verstoss).
- Richter (jack_arena.py JUDGE_VERSION 3): Kind pytest = Zustandspruefung wie B (nur Zielmodul darf sich aendern), dann gate_file, dann sichtbare + versteckte Tests in einer Kopie. BLOCKED_CATEGORIES leer.
- Selbsttests Honor: Richter 1248/1248 (C mit Testbetrug und verbotenem Code), Runner Policy 43/43, Orakel 308/308.
- Grenze (bewusst akzeptiert fuer Arena-C mit eigenen Aufgaben): pytest laeuft unter derselben Termux-UID. -I, leere Umgebung und RLIMITs sind keine Kernel-Isolation von Dateisystem oder Netz. Wird das AST-Tor je umgangen, hat der Prozess die Rechte des Termux-Benutzers. Fuer echten fremden Code: Xiaomi mit eigenem unprivilegierten Benutzer oder Namespace.
