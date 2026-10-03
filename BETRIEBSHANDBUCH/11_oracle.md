# 11. jack_oracle.py

Gelesen 03.10.2026, Grok, live per read_file. Kein Umbau.

**Zweck:** Alter bidirektionaler Kanal. Pollt alle 60s jack_cmd.json aus dem Repo dimitriskripkin-lgtm/jack-commands, fuehrt lokal aus, schreibt Ergebnis nach jack-commands und pusht. Nicht die MCP-Whitelist und nicht jack_mission_runner.

**Dienst:** Eigenes main mit Endlosschleife und sleep 60. Kein runit-Name in dieser Datei.

**Funktionen:**
- fetch_cmd, last_uuid, save_uuid: eine UUID nur einmal.
- check_rate_limit: 10 pro Stunde, nur im RAM. Neustart leert den Zaehler.
- verify_sig: HMAC-SHA256. Secret aus der Secrets-Datei. Signatur wird nur geprueft, wenn das Feld sig gesetzt ist. Ohne sig laeuft der Befehl weiter.
- resolve_alias: Kurzworte dienste, ram, speicher, fehler, datum, uptime, modelle, budget, log. modelle zeigt auf ollama list.
- is_safe: Default deny. Kill-Substring, Pfad-Tabu, erstes Wort muss in ALLOW (echo, sv, free, df, ls, cat, git, ollama, python3, termux-battery-status, termux-wifi-connectioninfo, pwd, date, uptime, grep, wc, head, tail). python3 nur ueber _py_skript_ok.
- SKRIPT_ALLOW: jack_wissen_ernte, jack_errors_status, jack_budget_status, jack_freigabe, jack_stress, jack_lerner, jack_wissen_tief, jack_karte. realpath muss jack-Home sein, kein Flag, kein Symlink.
- run_cmd: subprocess shell=True, timeout 30, Output 2000.
- push_result: jack_result.json plus Stack 5, dann git add, commit, push per shell=True.
- cycle: holt, limit, optional Signatur, Alias, UUID speichern, is_safe, run, push, Telegram.

**Reihenfolge-Fund:** Die main-Schleife steht vor _py_skript_ok und SKRIPT_ALLOW. Als Skript gestartet erreicht der Prozess diese Defs nie. Als Import schon. Ob ein Prozess laeuft, nicht geprueft.

**Freigabe:** Eigenes Gate. Kennt proposals, shadow, PENDING_EXEC und intent-Level nicht. Signatur optional. Alias modelle widerspricht der Ollama-Politik vom 28.09., falls der Kanal noch pollt.

**Offen:** Laeuft Oracle heute? Ist jack-commands noch aktiv?
