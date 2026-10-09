# 257 Erfahrungsmuster /muster

jack_muster.py (JACK_TUNE_MUSTER). Telegram /muster [Tage] (Standard 14, max 60).
- Liest missions/logs/*.json der letzten Tage (nur lesen, kein LLM, 0,1 s bei ca. 2000 Logs).
- Pruefungs-Acts (grep_count, file_exists, sv_ok, compile_ok, ro_scan usw.) zaehlen nicht als Fehler, dort ist ok=false ein Ergebnis.
- Gruppiert Fehler je Act nach normalisiertem Grund (Zahlen -> #, Pfade gekuerzt, Token-Folgen -> [X]) und gibt die 6 haeufigsten mit Quote und einem Tipp aus statischer Liste (_HINTS) aus.
- Nur Vorschlag. Nichts wird gespeichert, nichts wird zum Fakt.
- Befund 09.10. (14 Tage, 1985 Missionen): sv_restart 13x 'timeout' (offen: pruefen ob Neustart trotzdem klappt), ro_log_tail 50 % Fehler (kein Log fuer Dienste ohne log/run, siehe Kap. 251), file_create Pfad-Tabu 14x, py_replace Anker nicht gefunden 3x.
- Tipps erweitern: _HINTS in jack_muster.py.
