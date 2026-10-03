# 230. Zweitpass scharf

Gelesen 03.10.2026, erste 40 Zeilen. Nicht gestartet, nicht geaendert.

**Gedaechtnis-Schneiden:** jack_memory_pruning.py loescht Eintraege aelter als 30 Tage, wenn parent_id leer ist. Ob ein Dienst das taeglich ruft, hier nicht bewiesen.

**Lerner:** jack_lerner.py probiert Xiaomi-Einstellungen. Tabu im Kopf: adb, debug, wlan, bluetooth, sim, usb. Journal .lerner_journal.json war im Repo leer.

**Ollama-Waechter:** jack_ollama_guard.py startet ollama serve auf dem Honor, wenn die Temperatur unter 42 Grad liegt, und stoppt darueber. Schleife alle 15 Sekunden. Datei ist nicht Prozess. Ob ein Dienst sie startet, hier nicht bewiesen.

**Zwei Erlaubt-Listen:** jack_whitelist_guard.py vergleicht die Liste im Missions-Läufer mit der Liste im MCP-Server. Bei Unterschied Ende 2.
