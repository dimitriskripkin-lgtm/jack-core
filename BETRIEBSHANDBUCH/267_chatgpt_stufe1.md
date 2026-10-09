# 267 Rolle chatgpt Stufe 1 und Zusammenarbeit
Stand 09.10.2026, Probezeit. Freigabe durch Dima (Option A).

## Rechte (jack_mcp_auth.py, JACK_TUNE_CHATGPT_S1)
- Lesend wie bisher (ro_*, diag, file_exists, compile_ok, sv_ok). Graph/Memory-Tools und DB-Dateien bleiben gesperrt.
- NEU: create_mission mit act py_replace und file_create. Pruefung `_chatgpt_write_ok`: extra muss JSON mit file/path sein, Ziel nur in JACK_HOME (realpath), kein `..`, keine Secret-Woerter im Pfad, nicht in CHATGPT_NOWRITE (CORE_FILES, jack_mcp_oauth, jack_exec, jack_xiaomi, jack_xibreaker, jack_telegram, jack_publisher, jack_waechter, jack_logrot, .gitignore, Notaus-/Token-Dateien, config.ini, .ssh, .git, missions/, Attic/).
- Weiter verboten: exec_proposed, sv_restart, git_publish, batch, reload_module, Xiaomi. Das geht nur ueber Vorschlag an Claude (Vier-Augen).
- Das Handbuch-Gate (Quittung) gilt auch fuer ChatGPT: er muss das Kapitel zum Modul lesen, bevor er patcht.
- Getestet: 19 Faelle offline (reports/t_s1.py), Claude/Gemini/Grok unveraendert.

## Zusammenarbeit
Protokoll: ARBEITSPLATZ/gemeinsam/zusammenarbeit_claude_chatgpt.md (Besitzer/Pruefer, Review-Format, Bericht, Notbremse, Auswertung nach Probezeit).

## Offen
Live-Test ueber echte ChatGPT-Verbindung (ein erlaubter Patch, ein verbotener exec, diag). Auswertung der Probezeit fuer gezielte Erweiterung.
