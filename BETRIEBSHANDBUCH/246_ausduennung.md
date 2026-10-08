# 246 Ausduennung 08.10.2026 (Stufe 1 + 2)

Warum: Ordner war auf 612 Eintraege gewachsen (127 Sicherungen, 145 pyc, 3 Archivordner, tote Logs, alte Uebergaben). Neue KI verlief sich.

Stufe 1 (201 Dinge nach Attic/, alles rueckholbar, Attic steht in .gitignore):
- 127 *.bak_* Dateien, __pycache__, LEGACY_ARCHIVE, apk_lab, archiv_cleanup, archiv_tot, archiv_voice, titan_legacy, tmp_limit, tests, harvest_dumps, archive, attic(klein), shadow.
- Tote Logs (letzte Zeile Aug/Sep), Test-Muell (wav, png, tap-txt), alte Dokumente (KOENIGSDOKUMENT*, UEBERGABE v8/v9/v28, WAHRHEIT, ARCHITEKTUR, ROADMAP_GROK_50, alte handshake*.json).
- Bewusst gelassen: Ordner '\~' (Backslash im Namen irritiert den Runner), fingerprints/, aktive Logs waechter.log, jack_decisions.log, changelog.log.

Stufe 2 (19 Waisen-Module nach Attic): diag_full_dump, harness, patch_template, jack_accessibility_listener, jack_aufraeumen, jack_calltest, jack_install, jack_nav_learn, jack_navi, jack_orchestrator, jack_personality, jack_pruefstand, jack_react, jack_schema, jack_screen_tracker, jack_sehen, jack_testbed, jack_vision_once, jack_voice_chat_live.
Bewusst GEHALTEN (Waise oder fast): jack_qwen_client (laeuft als Dienst jack_qwen), jack_telemetry/jack_thermal (neu), jack_whitelist_guard, jack_error_door (Sicherheits-/Lesetuer), jack_pyflakes_lauf, jack_diag_snapshot (Daten werden gelesen), jack_vinted_radar (kortex_controller liest jack_vinted.db), jack_cmd_crawler+jack_intent_parser (A-011), jack_bug_fixer+jack_code_writer, jack_skill_self_creation+jack_audit_run (moegliche Faehigkeiten, Dima entscheidet).

Methode: Verweis-Graph per Namenssuche ueber alle Module (siehe MODULKARTE.md), dazu ro_ps (laufende Dienste), letzte Logzeile. Falle: dynamisch gebaute Namen (.heartbeat_*) sieht die Suche nicht, deshalb keine Zustandsdateien angefasst.
Nachweis: danach sv_restart + sv_ok von telegram, cortex, waechter, autolearn, publisher, focus_monitor, alle up, keine Importfehler in den Logs.
Rueckholen: Attic/<name>_<zeitstempel> per Hand zurueck nach ~/jack/<name>.
Lehre: Paralleler read_file-Abruf mit gemeinsamer MCP-Session vermischt Antworten. Immer einzeln abrufen und das Feld 'path' der Antwort pruefen.
Offen: log-Prozess von jack_mcp und jack_autolearn startet immer wieder neu ('down: log'), Dienste selbst laufen.
