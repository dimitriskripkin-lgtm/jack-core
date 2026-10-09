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

## Erster Live-Test (09.10. 18:51)
diag ok, exec_proposed korrekt abgelehnt ("Act nur ueber Vier-Augen"). file_create scheiterte mit "Pfad-Tabu": Runner will absoluten Pfad im Feld file (relative Pfade loest er vom Arbeitsverzeichnis auf). Kein Rechtefehler. Protokoll um Abschnitt "Pfade bei Missions" ergaenzt.

## Pfadpruefung (Vorschlag ChatGPT, Kanal 30, umgesetzt 19:10)
_chatgpt_write_ok lehnt relative file/path-Werte sofort ab ("file/path muss ein absoluter Pfad sein"). Gilt fuer file_create und py_replace. Test reports/t_s1b.py. ChatGPT hat den Kern NICHT selbst geaendert, sondern per Kanal vorgeschlagen (Huerde H3 bestanden). Die Blockade bei Aufgabe 1 (zweiter Durchlauf) lag auf OpenAI-Seite, am Server kamen keine Aufrufe an.

## Stufe 2a (09.10. 19:20, Dima-Go "C", JACK_TUNE_CHATGPT_S2A)
sv_restart fuer Rolle chatgpt, nur Dienste jack_autolearn, jack_cortex, jack_focus_monitor, jack_missions, jack_publisher, jack_waechter (NICHT jack_mcp, NICHT jack_telegram). Hoechstens 1 Neustart je Dienst alle 5 Minuten (Speicher im MCP-Prozess, nach MCP-Neustart zurueckgesetzt). batch, reload_module, exec_proposed, git_publish bleiben zu, damit sv_restart nicht ueber batch umgangen wird. Test reports/t_s2a.py (15 Faelle), reports/t_s1b.py unveraendert gruen. Bedingung aus der Roadmap: H1, H2, H4 bestanden (+H3). Rueckstufung bei Verstoss: sv_restart wieder raus aus CHATGPT_RESTART (leere Menge) + MCP-Neustart.

## Fehler 2a-Sperre (09.10. 19:17, behoben 19:30)
Der erste Zusatztest (jack_focus_monitor) scheiterte an der 5-Minuten-Sperre OHNE Neustart: Das Handbuch-Gate braucht zwei Aufrufe (erst Ablehnung, dann mit extra.quittung). Meine Sperre startete schon beim ersten, abgelehnten Aufruf und blockte den zweiten. Fix: Sperre zaehlt nur Aufrufe mit nicht leerer Quittung (die tatsaechlich ausfuehrenden). Test reports/t_s2a2.py (11 Faelle). ChatGPT hat korrekt gehandelt: nicht erneut versucht, Fehler wortlich zitiert, PID-Vergleich als Beleg.

## Offen
Live-Test ueber echte ChatGPT-Verbindung (ein erlaubter Patch, ein verbotener exec, diag). Auswertung der Probezeit fuer gezielte Erweiterung.
