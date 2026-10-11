# 271 Dead-Man neu (10.10.2026)
## Befund
- cron/deadman.sh (Crontab, alle 30 Min) startet `python3 jack_deadman.py`. Die Datei wurde am 19.09.2026 im Commit c673e93c (Waisen-Bereinigung) geloescht. Folge: seitdem alle 30 Min eine Fehlzeile in logs/deadman.log (~284 KB, 2420 Zeilen), und der Dead-Man-Alarm war 3 Wochen aus.
- Ursache: Die Waisen-Erkennung (AST-Importgraph) sieht nur Python-Imports. Start per Cron/Shell-Skript/runit-run wird nicht erkannt.
- Die alte Version hatte zusaetzlich einen Fehler: der Telegram-Aufruf lief per `python3 -c` in einem Kindprozess, dort war `_dm3h_allow` nicht definiert (Fehler wurde verschluckt). Die Meldung konnte nie rausgehen. `jack_dm_gate.py` fehlt ebenfalls (ist seit c673e93c weg).
- Die alte Version pruefte auch `jack_overmind_result.json` (zuletzt geaendert 14.09.): Wiederherstellung haette Dauer-Alarm erzeugt.
## Loesung
- Neue schlanke `jack_deadman.py`: prueft nur `.heartbeat_jack_waechter` und `jack_health_now.json` (beide frisch), Alarm wenn aelter als 3 h, per `jack_telegram.send` im selben Prozess, max. 1 Meldung pro 3 h (Marker `.deadman_last`).
- Test: Normalfall `DEADMAN OK` rc=0; Alarmfall mit Fake-Telegram genau 1 Sendung, zweiter Lauf unterdrueckt. Kein echtes Telegram gesendet.
## Offen
- Waisen-Erkennung (reports/karte_roh.py und kuenftige Bereinigungen) muss cron/*.sh, crontab, runit-run-Skripte und Shell-Skripte mit einbeziehen, bevor etwas als Waise geloescht wird.
- logs/deadman.log ist durch Altlast aufgebloht, Rotation/Kuerzung pruefen.
- `.deadman_last` in .gitignore aufnehmen.
- Ungeklaert: Wer jack_autolearn um 11:32 angehalten hat (kein MCP-Audit-Eintrag).
