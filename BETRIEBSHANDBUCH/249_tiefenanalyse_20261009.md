# JACK Tiefenanalyse 08./09.10.2026

Basis: 198 Module, 28.151 Zeilen, verifizierte Live-Kopien vom Honor. Methode: statische Prüfung aller Module (pyflakes + eigene Musterprüfung), Sicherheitskern Zeile für Zeile, Laufzeit (Dienst-Logs, Entscheidungslog, Prozessliste, Takte), gezielte Prüfung der Pfade, auf denen Text zu Befehlen wird. Gruppe A (Sicherheitskern) ist vollständig geprüft. Die Gruppen B bis F sind gezielt geprüft (Telegram-Eingang, Ausführungspfade, Takte, Gedächtnis-Schreiber, UI-Eingaben, Rest). Eine Zeile-für-Zeile-Prüfung aller 198 Module steht noch aus.

## A. Sofort behoben (live, geprüft)
| # | Schwere | Wo | Problem | Fix (Marker) |
|---|---|---|---|---|
| 1 | KRITISCH | jack_telegram.py Hauptschleife | Text, Foto und Sprache wurden von JEDER chat_id verarbeitet, nur Knöpfe waren geprüft. Fremde hätten blind Befehle auslösen können. | Nur noch Dimas CHAT_ID, Fremde werden ignoriert und als TG-FREMD protokolliert (JACK_TUNE_ONLYDIMA) |
| 2 | KRITISCH | jack_inbox.py | Der Telegram-Dienst holt alle 60 s jack_inbox.json aus dem öffentlichen Repo und führte Pläne ohne Rückfrage aus, auch Shell-Schritte. Jeder mit Push-Recht hätte so alle Sperren umgehen können. | Pläne mit exec-Schritten laufen nicht mehr automatisch, Dima bekommt eine Meldung (JACK_TUNE_INBOXGATE) |
| 3 | KRITISCH | jack_mcp_server.read_file | Die neue Token-Datei .jack_mcp_tokens war lesbar (die Sperrliste kannte nur den alten Namen). | Geheimnis-Sperre nach Namen: token, secret, credential, passw, config.ini, .env, .netrc (JACK_TUNE_SECRETBLOCK). Im Protokoll: niemand hat sie ausgelesen. |
| 4 | KRITISCH | jack_mcp_auth (Rolle nachtlauf) | Der Nachtlauf hätte sich über propose_fix + approve_proposal selbst eine Shell freigeben können. Mit ".." im Pfad hätte er außerhalb des Jack-Ordners schreiben können. | Diese Acts und ".." sind für den Nachtlauf gesperrt (JACK_TUNE_NIGHTDENY2) |
| 5 | HOCH | jack_mcp_auth | Grok, Gemini und Nachtlauf durften den ganzen Handyspeicher lesen. Die Fehlversuch-Sperre traf auch gültige Tokens. | Diese Rollen lesen nur noch im Jack-Ordner. Die Sperre trifft nur noch ungültige Tokens. |

Insgesamt 28 lokale Tests grün, danach live verifiziert. Dienste laufen ohne Fehler.

## B. Offen: braucht Dimas Go (Sicherheitskern und Verhalten)
1. **HOCH: Runner-Pfadprüfung.** jack_mission_runner.py Zeilen 103/171/196 prüfen nur `fp.startswith(J)`, ohne realpath. `~/jack/../.termux/boot/x` kommt dadurch durch. Fix: realpath plus Trennzeichen-Prüfung.
2. **HOCH: Freigabe ohne Mensch.** approve_proposal führt einen Vorschlag aus, ohne dass ein Mensch zustimmt. Für Claude ist das bewusst so, für alle anderen soll es nur über deinen Telegram-Knopf gehen. Fix: Dima-Marker in der Vorschlagsdatei.
3. **HOCH: Root-Befehlsinjektion auf dem Xiaomi.** Text wird ungequotet in `su -c "input text ..."` eingesetzt, in jack_planner Zeile 75 (step_input_text), jack_ui_agent Zeile 26 und jack_ui_type Zeile 59. `$( )`, Backticks und `;` würden als root ausgeführt, sobald der Text von einer KI oder einer Webseite kommt. Fix: Zeichen-Whitelist plus shlex.quote.
4. **MITTEL: Telegram-EXEC-Vorschau.** Sie zeigt nur die ersten 800 Zeichen, der Rest des Befehls wird unsichtbar mit bestätigt. Fix: längere Befehle ablehnen.
5. **MITTEL: Publisher.** Werkstatt- und Skills-Ordner gehen nur token-gefiltert (nicht privat-gefiltert) ins öffentliche Kontext-Repo. Außerdem wird der Hash vor dem Push gesetzt, ein gescheiterter Push wird deshalb nie wiederholt.
6. **MITTEL: jack_error_to_rule.** Fehlertexte werden als "REGEL" in jack_learned_rules.md geschrieben. Diese Datei lädt jack_talk (Zeile 433) in den Prompt, und sie geht per git_publish öffentlich ins Repo. Fix: Fehlertext nicht in den Prompt nehmen und die Datei in .gitignore aufnehmen.
7. **MITTEL: Geheimnis-Scan.** ro_scan/git_publish kennen das Telegram-Bot-Token-Muster nicht, jack_publish kennt es. Fix: ein gemeinsamer Scanner.
8. **MITTEL: Rennen auf Missionsdateien.** jack_mission_prioritizer überschreibt pending-Missionsdateien nicht-atomar, während der Runner sie liest. Folge sind falsche fail-Einträge. Fix: tmp-Datei plus os.replace.
9. **MITTEL: Autofreigabe per Präfix.** In jack_approval gibt das Präfix "jack autonom:" automatisch frei.
10. **NIEDRIG: Tote Code-Stellen.** Im Runner gibt es tote Acts (xiaomi_ollama_*_v1). In jack_chains steht chain_oauth_final doppelt, mit eval auf einer Vision-Antwort, und hat keinen Aufrufer. jack_skills_db.run_skill führt Code mit exec aus, egal welchen Status der Skill hat, und sein timeout-Parameter wirkt nicht. Fix: entfernen.

## C. Robustheit und Optimierung
1. **HOCH (Akku/Hitze): Telegram-Abfrage.** Telegram fragt jede Sekunde mit timeout=0 ab, das sind etwa 86.400 Anfragen am Tag. Long-Polling (timeout=25, urlopen-Timeout 35) senkt das auf etwa 3.500, bei gleicher Reaktionszeit.
2. **MITTEL: Watchdog ohne Wirkung.** jack_watchdog.sh (aus ~/.termux/boot) schreibt alle 60 s "jack_autolearn neugestartet" ins Entscheidungslog, obwohl autolearn läuft. Das Log besteht inzwischen fast nur daraus. Vermutung: `sv` findet ohne SVDIR den Dienst nicht. runit überwacht autolearn ohnehin. Fix: Watchdog aus dem Boot-Skript nehmen.
3. **MITTEL: Dienst jack_qwen ohne Nutzen.** Seine Ausgabe qwen_snapshot.json liest niemand, und er bekommt alle 5 min 401. Kandidat zum Abschalten.
4. **MITTEL: Hängegefahr.** 29 Programmaufrufe haben kein Zeitlimit, kritisch sind die in Diensten: jack_telegram send_voice (curl), get_voice (urlopen/urlretrieve), Foto-Thread (urlopen ohne timeout), jack_cortex 267/269. Fix: timeout ergänzen.
5. **MITTEL: Stille Fehler.** 394 Stellen verschlucken Fehler still, 33 davon in Endlosschleifen (23 allein in jack_autonomous). Nach und nach mit jack_logging.fehler melden.
6. **NIEDRIG: Werkzeug-Grenze.** read_file liest bei großen Logs nur den Anfang (erste 5000 Zeilen). Für das Ende nutzt man ro_log_tail mit service=jack_decisions usw.
7. **Architektur: enge Kopplung.** Jeder Dienst erreicht über Importe 164 der 198 Module. Ein Fehler in einem gemeinsamen Modul kann so alle Dienste treffen. Die Fix-Logik gibt es dreifach (Runner, jack_missions, jack_patch), die Check-Acts doppelt.
8. **Takte (in Ordnung):** Wächter 120 s, Cortex 60–120 s, Focus 15/45 s, Missions-Queue 1 s (billig, Git-Pull 30 s), Publisher 180 s, Lerner/Reflexion 1 h, Scout 24 h. Die Dienst-Logs sind ohne Tracebacks.

## D. Empfohlene Reihenfolge
1. B1 bis B3 (Pfad, Freigabe, Injektion). Das sind kleine Patches mit großer Wirkung.
2. C1 (Telegram Long-Polling) und C2 (Watchdog raus). Das bringt sofort weniger Last.
3. B5 bis B8 (Publisher, Regeln, Scanner, atomar).
4. Danach die Zeile-für-Zeile-Prüfung der Gruppen B bis F nachholen (Gedächtnis-Wachstum, Voice-Pfad, Rest).
