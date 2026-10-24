# 303 Lärm-Diät, Selbsttest, Gesprächs-Weichen (24.10.2026)

Claude, Auftrag Dima 24.10. 12:36: "proaktiv messen und Kleines selbst bauen". Alles auf dem Honor gemessen, jede Änderung live nachgeprüft (Prüfsumme, Probe-Aufruf, sv status).
Module: jack_graceful.py, jack_quota.py, jack_autolearn_loop.py, jack_selftest.py, jack_chat_router.py, jack_aenderung.py, jack_mcp_server.py, jack_monitor.py

**Gemessen**
- Dienste: telegram, cortex, waechter, autolearn, missions, mcp, publisher, focus_monitor, honor_watch laufen. Absichtlich down: jack_qwen, ollama_local, ssh_tunnel_ollama, mosquitto. Honor 38-42 °C, Xiaomi per SSH erreichbar.
- Fahrdigest (Kap 299) BEWIESEN: 22.10. 05:14 Sammelmeldung (2 Hinweise, Kennung a6e2e22532a8). 23.10. zwei Fahrten (05:14-07:49 und 08:34-11:25), beide korrekt LEER, 0 FAHRDIGEST-ERR. jack_log.log_decision schreibt nach ~/jack/jack_main.log.
- Chatlog 21.-24.10. (logs/telegram_chat.jsonl, 116 Zeilen): Antwortzeit Text Median 2 s (n=17, max 8 s), Befehle Median 3 s (n=9, max 5 s). Keine Sprachnachrichten im Log. Engpass ist die Antwortqualität, nicht das Tempo.
- Rauschen: 37 von 90 JACK-Nachrichten (41 %) waren "Xiaomi weg/da": GRACEFUL 18, "JACK Speicher" 6, Wächter "nicht mehr erreichbar" 4, Autolearn "seit X Min." 4, "Heartbeat 3x rot" 3, Cortex "wieder erreichbar" 2.
- Selbsttest jeden Morgen 85 %: einziger roter Check "missions" (fail<25 über alle 932 Fehlschläge seit Juli). Die 10 Fehlschläge der letzten 24 h waren Prüf-Acts von Claude.
- Gemini: ~/jack/.api_budget zuletzt am 20.10. 08:59 geschrieben, also seither kein Gemini-Aufruf über jack_gemini_bridge. Woche W43: 0,42 EUR. Modell weiter 2.5 (keine Marke .gemini25_weg). Achtung: Ersatz gemini-3.5-flash kostet laut PREISE_USD 1,50/9,00 USD je Mio Token, Flash-Lite 0,10/0,40, also etwa 15-20-fach. Wochendeckel 8 EUR greift.
- jack_budget live: text 10000/Tag, EUR_WEEK 8.0. START_HIER Abschnitt 12/13 (600/3 EUR) ist veraltet. Meldetext "Wochenlimit 3 EUR" in check_and_count ebenfalls (Kosmetik, offen).
- MCP-Auth: Rollen-Middleware ist fail-closed (503 ohne Tokens, 401 bei falschem). Der Rückfall _JackAuthMiddleware ließ ohne Legacy-Token jeden durch (Kap 26). Heute nicht ausnutzbar: .jack_mcp_token vorhanden (1 Zeile), .mcp_roles_off fehlt.
- Sperrliste (24 Pakete, Kap 296): Der UI-Agent ist schon geschützt (Start-App nur termux/settings/chrome, fremde Vordergrund-App führt zu ABBRUCH). Lücken: open_url_xiaomi (Deep-Links), skill_run, Tasker. Hier nichts geändert.

## Geändert
1. ~/jack/jack_mission_active.json (Testmission test_health_20260824 vom 24.08.) ins Attic: Attic/jack_mission_active.json_20261024_124921. jack_graceful meldet nicht mehr bei jedem Xiaomi-Wackler Pause/Fortsetzung (18 Push). Rückweg: Datei zurückschieben.
2. jack_quota.py JACK_TUNE_QUOTA1G: Warnschwelle 500 MB auf 1 GB, Text jetzt "JACK-Ordner X MB, Warnschwelle Y MB". Aufrufer ist jack_hb_alarm (nur bei Heartbeat-Fehler), deshalb kam die Meldung immer beim Xiaomi-Aussetzer. Wächter neu gestartet.
3. jack_autolearn_loop.py JACK_TUNE_XIDOWNSTALE: ~/jack/.xi_hb_down ist nur der 3-h-Abkühlstempel der Wächter-Meldung (CYCL3H/XIHB3H) und wird nie gelöscht. Autolearn fragt jetzt jack_heartbeat.is_xiaomi_alive() und meldet nur, wenn das Xiaomi wirklich weg ist: "Xiaomi SSH weiterhin nicht erreichbar (erste Meldung vor X Min.)". Offline 3/3. Autolearn neu gestartet.
4. jack_selftest.py JACK_TUNE_SELFTEST24H: missions-Check zählt nur Fehlschläge der letzten 24 h ohne Prüf-Acts (grep_count, sv_ok, hb_ok, file_exists, diag, fact, compile_ok, ro_*), Schwelle bleibt 25. Live 100 % (7/7). Hinweis: jack_health_monitor vergleicht den Score vor/nach einer Freigabe (Rollback ab -5). Die Basis ist jetzt 100 statt 85, das Verhalten bei Xiaomi weg bleibt gleich (vorher 85 auf 71, jetzt 100 auf 85).
5. jack_chat_router.py JACK_TUNE_GATE1WORT: zweite Wortgruppe von GATE1 prüft ganze Wörter (code*, modul*, datei*, dienst* außer dienstag*, log/logs/logdatei/logfile, py). Vorher steckte "log" in "Logik": Dimas Frage vom 22.10. 04:29 landete in DIAG und endete mit "Ok, beendet. Kein Fix.". ".py" griff nie, weil norm() Punkte entfernt. Test: alle 29 echten Dima-Nachrichten, genau 1 Unterschied (die Logik-Frage, DIAG auf TALK), dazu 16/16 Fälle. Telegram neu gestartet.
6. jack_aenderung.py JACK_TUNE_AENDSTOP: Gruß- und Füllwörter (moin, hallo, servus, geht, gehts, erzaehl/erzaehle/erzaehlen, hast, habt, gesehen, sehen, siehst, sage, sagen, zeig/zeige/zeigen, kannst, koennen, weisst) sind Stoppwörter. Vorher wurden sie Thema ("moin geht erzaehl hast gesehen") und die Antwort war "keine passenden Aenderungen" (22.10. 04:27). Live: der Satz liefert jetzt die Liste. Achtung Arena: die vorregistrierte Regel ist damit erweitert, alte und neue Läufe dieser Spur sind nicht direkt vergleichbar.
7. jack_mcp_server.py JACK_TUNE_MCPFAILCLOSED: Rückfall ohne Token antwortet 503 statt durchzulassen. Wirkt erst beim nächsten jack_mcp-Start (nur Dima, nie per Auftrag). Test mit Starlette: ohne Token 503/503/503, mit Token 401/401/200.
8. jack_monitor.py JACK_TUNE_MON3: Der Marker stand im Text und landete im Briefing ("Dienste: alle 3 laufen  # JACK_TUNE_MON3"), jetzt Kommentar. Wächter neu gestartet.

Rückweg für 2-8: py_replace mit vertauschtem old/new, die Strings stehen in missions/done/m_batch_20261024_125252 bis _125612.

## Erwartete Wirkung
Xiaomi-Rauschen von 37 auf etwa 9 Meldungen je 3,5 Tage (Wächter-Wegmeldung, Heartbeat-3x und Cortex "wieder da" bleiben). Selbsttest zeigt wieder echte Probleme statt Dauer-85.

## Offen (Vorschläge, nur mit Dima)
- "Heartbeat 3x rot: xiaomi" ist doppelt zur Wächter-Meldung: für xiaomi stumm schalten?
- Shadow-Fixer läuft etwa alle 2 Min per SSH auf dem Xiaomi ("Keine offenen Fehler", rund 720 am Tag).
- Sperrliste zentral erzwingen (jack_xiaomi.run_shell + open_url), Schätzung 45 Min.
- Aenderungs-Auskunft: Thema nur filtern, wenn der Begriff im Repo-Vokabular vorkommt (Idee aus Kap 280).
- Budget-Meldetext "Wochenlimit 3 EUR" auf 8 EUR.

## Gespraechsmessung 24.10. 13:34 (Dima Go 13:32)
Werkzeug jack_talk_probe e2e (Schreibsperre, kein Telegram), 10 Fragen im Stil von Dima. Runde 1 ohne frisches Selbstbild (die Probe sperrt den Unterprozess jack_selbstbild.py, Datei war vom 22.10.), Runde 2 mit frischem Selbstbild fuer die 6 kontextabhaengigen Fragen (= echte Bedingungen, im Chat erneuert sich das Selbstbild nach 30 Min). Tempo 0,1-2,0 s je Antwort.
Echte Bedingungen: richtig 3 (Erinnerungen, Akku 19 Prozent, Witz), vage 1 (Logik), teilweise 4 (Aenderungen nur bis Commit 21.10., Architektur nennt Ollama als Standard-LLM, Graph ueber mich mit Muellfakten wie decke weiss, Kap 303 mit Lesefehler kleines Geraet), falsch 1 (Standort verneint, obwohl /standort existiert), ehrlich verpasst 1 (heute erledigt: weiss ich nicht, obwohl das Log es hat).
Ohne Selbstbild (Runde 1) zwei Erfindungen: gestern Xiaomi-Modul per Hot-Reload neu geladen, heute Chrome-Suche und Spotify gestartet.
Hebel: 1 Heute-Antwort aus logs/telegram_chat.jsonl plus Missionen. 2 Befehlsliste ins Selbstbild. 3 Graph-Muell entfernen und Ollama-Fakt klarer (nur mit Dimas Wort). 4 Stand committen, sonst kennt die Aenderungs-Auskunft nur den 21.10.
Rohdaten privat: ~/jack_arena_private/talk/probes.jsonl (Tags claude_20261024_*, claude_20261024b_*).


## Auftrag H eingebaut 24.10. 14:01 (Vorarbeit ChatGPT, Review und Einbau Claude)
Neu ~/jack/jack_heute.py (JACK_TUNE_HEUTE, sha256 1e7e4671...): beantwortet Was hast du heute/in meiner Schicht gemacht deterministisch aus logs/telegram_chat.jsonl (nur JACKs Meldungen, ohne JACK online und claude_test) plus missions/done und fail im Fenster (Anzahl je src, Pruef-Acts getrennt). Schalter ~/jack/.heute_off. Claude-Aenderung JACK_TUNE_HEUTEGRUPPE: gleiche Meldungsart (Ziffern egal) wird zusammengefasst, chronologisch, sonst verdraengten 6 Akku-Warnungen Morgen-Status und Briefing. Tests 35/35 (Kopie BUEROS/claude/H_tests_claude.txt; Test 27 Zeitfehler und Test 28 an Gruppierung angepasst).
jack_chat_router.py: classify() fragt jack_heute.erkennt vor dem NEU-Block, neu_antwort() zuerst jack_heute.antwort (keine neue Spur). jack_selbstbild.py JACK_TUNE_HEUTEBEFEHLE: Zeile Befehle (/standort GPS, /akku, /status, /lage, /timer, /musik, /agent, /scan, /selftest, /sensor, /budget, /vorschlaege, /links, /befehle). Achtung MAX_CHARS 850, Selbstbild jetzt 774 Zeichen mit [GEKUERZT] am Ende.
Probe e2e nach Einbau (frisches Selbstbild): heute erledigt -> nur Belegtes (130 ms); Standort -> Ja, mit /standort; Logik-Frage bleibt TALK; Was hat sich veraendert bleibt Aenderungs-Auskunft.


Graph-Muell 24.10. 14:06 (Dima Go): fakt:decke, fakt:ist_wei, fakt:dir_ein samt Kanten geloescht, Backup graph_backups/jack_graph_vor_muell_20261024.db. JACK_TUNE_UEBERMICH: Ueber-mich-Antwort nimmt nur Fakten mit Kante von person:dima, ohne verworfene und Geraete (vorher die 10 neuesten Knoten jeder Art).
