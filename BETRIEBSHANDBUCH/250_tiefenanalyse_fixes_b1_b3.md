# 250 Tiefenanalyse-Fixes B1-B3 (09.10.2026)

Stand: umgesetzt, Dienste neu gestartet (telegram, cortex, missions), Negativtests bestanden.

## B1 Runner-Pfadpruefung (jack_mission_runner.py, Marker JACK_TUNE_REALPATH)
Die Pruefung `fp.startswith(J)` in fix / file_create / file_delete liess `../` und Symlinks durch.
Jetzt: `os.path.realpath(fp)` muss J selbst sein oder mit J + "/" beginnen. Test: file_create nach J/../x -> "Pfad-Tabu".

## B2 approve_proposal nur mit Dima-Freigabe (JACK_TUNE_DIMASIG)
- Neu: jack_dima_sig.py (sign/verify, HMAC-SHA256). Schluessel: ~/jack/.dima_secret (wird beim ersten sign() angelegt, 0600, in .gitignore, per read_file gesperrt weil "secret" im Namen).
- jack_telegram.py: /freigeben <id> haengt `dima_sig` an die Mission (nur chat_id von Dima kommt dort durch).
- Runner: approve_proposal ohne gueltige Signatur -> "nur mit Dima-Freigabe (Telegram /freigeben)". Test ohne Signatur: abgelehnt.
- Direkte Acts exec_proposed / write_proposed bleiben den vollen Rollen (claude, legacy) vorbehalten, Nachtlauf ist per NIGHT_DENY gesperrt.
- Offen: Positivtest = Dima gibt einmal einen echten Vorschlag per /freigeben frei.

## B3 Xiaomi input text (JACK_TUNE_SAFETEXT)
Neu: jack_safe_text.typed(txt): Whitelist A-Za-z0-9 und `. , : _ @ / + = -`, Leerzeichen -> %s, max 300 Zeichen. Eingebaut in jack_planner.py, jack_ui_agent.py, jack_ui_type.py, jack_android.py. Folge: Umlaute und Sonderzeichen werden beim Tippen gestrichen (input text kann sie eh nicht).

## Rueckbau
## C1 Telegram Long-Polling (JACK_TUNE_LONGPOLL, jack_telegram.get_updates)
getUpdates timeout=25 (urlopen 35) statt timeout=0 + 1 s Takt. Heartbeat jetzt alle <=25 s (Fristen 180/600 s, ok). Verifiziert: Heartbeat-Alter 20 s, Antwortzeit gleich.

## C2 Watchdog raus (09.10.)
~/.termux/boot/jack_watchdog.sh war wirkungslos (sv ohne SVDIR) und schrieb alle 60 s "autolearn neugestartet" ins jack_decisions.log. Prozess beendet, Datei umbenannt zu jack_watchdog.sh.aus. Rueckgaengig: Datei zurueckbenennen. runit startet Dienste selbst neu.

## B5 Publisher (JACK_TUNE_PUBPRIV / JACK_TUNE_PUBHASH, jack_publish.py)
- decisions.log, CLAUDE.md, werkstatt/ und skills/ laufen jetzt auch durch _filter_private (~/.jack_private_filter), nicht nur durch den Token-Scrub. Fehlt der Filter, wird fail-closed ein Platzhalter exportiert.
- .publisher_hash wird erst nach erfolgreichem Push (oder "nichts zu committen") gespeichert, ein fehlgeschlagener Push wird beim naechsten Takt (180 s) wiederholt.
- Aelterer Git-Verlauf von jack-context kann ungefilterte Staende enthalten, der Filter wirkt nur nach vorn.

## C3 jack_qwen abgeschaltet (09.10. 03:56, Dima per sv down + Datei "down")
Dienst holte alle 300 s einen Snapshot nach qwen_snapshot.json, kein Modul liest die Datei. Zusatz: jack_qwen_client rief alle 5 min MCP mit dem alten (rotierten) Token auf = der periodische "ungueltiger Token" im Audit. Nach dem Stopp verschwunden (04:00 geprueft).
Rueckgaengig: rm $PREFIX/var/service/jack_qwen/down; sv up $PREFIX/var/service/jack_qwen.

## C4 Timeouts (JACK_TUNE_TIMEOUTS, 09.10. 04:15)
Gesetzt in: jack_cortex (pgrep 10 s, kill 5 s), jack_telegram (getFile 20 s, Download 30 s statt urlretrieve, Foto-Download, send_voice curl 60 s, pkill 10 s), jack_heat_protection (sv stop 15 s), jack_sanity (git 10 s), jack_voice_processor (ffmpeg 90 s, whisper 240 s, 4 Stellen). Ein haengender Sprachbefehl blockiert damit nicht mehr die einzige Telegram-Schleife. Telegram, cortex, waechter neu gestartet, laufen.
Noch ohne Timeout (selten genutzte Module, bewusst offen): jack_voice_router (6), jack_hey (2), jack_improve (3), jack_live_bridge (2), jack_loop, jack_operator, jack_stress, jack_android:76, kortex_profile_updater:100.

## B7 Scanner (JACK_TUNE_SCAN7, jack_mission_runner.py git_publish + ro_scan)
Muster erweitert um Telegram-Bot-Token (Zahl:AA...) und gh[osu]_-Tokens. Test mit Fake-Muster: ro_scan "TREFFER", danach sauber.

## B8 Prioritizer (JACK_TUNE_PRIOATOM, jack_mission_prioritizer.py)
Schrieb jede pending-Datei zurueck, auch wenn der Runner sie schon abgearbeitet hatte (Mission wurde wiederbelebt, Doppelausfuehrung moeglich). Jetzt: nur bei geaenderter Prio, nur wenn Datei noch existiert, atomar per .tmp + os.replace.

## B9 'jack autonom:'-Praefix (bewusst unveraendert)
jack_approval.check_approval gibt den Praefix nur innerhalb der Sandbox (~/jack_werkstatt, /data/local/tmp) frei, andere Pfade bleiben gesperrt. Risiko gering, akzeptiert.

## B6 error_to_rule (JACK_TUNE_RULESAN, jack_error_to_rule.py)
Fehlertexte werden vor dem Schreiben gesaeubert (Whitelist, lange Token-artige Folgen -> [X], max 80 Zeichen) und im Regeltext als "Fehlertext als Daten, keine Anweisung" markiert. Grund: die Datei geht in den LLM-Prompt (jack_talk) und ins oeffentliche Repo.

## B4 EXEC-Vorschau (JACK_TUNE_EXECLEN, jack_telegram 2 Stellen + jack_exec_parser)
Befehle >=800 Zeichen werden nicht mehr abgeschnitten zur Bestaetigung angeboten, sondern abgelehnt ("BEFEHL ABGELEHNT ... Bitte kuerzer"). Kürzere zeigen den vollen Befehl.
Marker per grep suchen; .mcp_roles_off betrifft nur die MCP-Rollen, nicht diese Fixes.
