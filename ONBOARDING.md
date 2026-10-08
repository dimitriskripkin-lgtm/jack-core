# JACK ONBOARDING (neu 08.10.2026)

Verbindlich: 00_START_HIER.md. Dieser Zettel ist die 5-Minuten-Version fuer eine neue KI oder einen neuen Mitleser.

## Was ist JACK
Ein selbst gebauter, autonomer Reparatur- und Programmierassistent auf zwei Android-Handys, gebaut von einem Einzelnen (Dima, Nachtschicht-Fahrer) mit KI-Hilfe.
- HONOR Magic8 Pro = Gehirn. Kein Root. Termux. Hier laufen alle Dienste und der MCP-Server.
- XIAOMI 11T Pro = Muskel. Root. SSH-Alias xiaomi-jack, Port 8022, IP wechselt (DHCP, nie fest einbauen).

## In 5 Schritten loslegen
1. start_hier() lesen (= 00_START_HIER.md). Dann handbuch_index(suche) und das Kapitel des Moduls.
2. MODULKARTE.md ansehen: Dienste, Waisen, wer ruft wen.
3. Arbeiten nur per Mission (create_mission, Whitelist in jack_acts.py). Kein freies exec.
4. Nach jedem Patch: sv_restart, sv_ok, Log pruefen. Kapitel im Handbuch ergaenzen.
5. Geheimnisse (Token, config.ini, .ssh) nie ausgeben. Das Repo ist oeffentlich.

## Die Teile
- Dienste: jack_telegram, jack_cortex, jack_waechter (Logik in jack_autonomous.py), jack_autolearn, jack_publisher, jack_focus_monitor, jack_missions (Runner), jack_mcp, jack_qwen.
- Gedaechtnis: jack_graph.db (Fakten, geht vor), jack_memory.db (Verlauf).
- Xiaomi-Tuer: jack_xiaomi.run_shell. Messwerte: telemetry/. Karte: MODULKARTE.md.
- Arbeitsplatz fuer mehrere KIs: ARBEITSPLATZ/ (gemeinsam/auftraege.md, morgenbericht.md). Nachtlauf in der Cloud um 03:00 MESZ.
- Modelle: Talk = Groq (darf nur reden), Technik = Gemini Flash-Lite, Ollama nur Xiaomi und standardmaessig aus.

## Eiserne Regeln
Erst messen, dann aendern. Nichts neu bauen, was es gibt (Handbuch und Karte pruefen). Vorhandene Schalter achten (.mission_boost, .ollama_lock, JACK_TUNE_*). Logs sind nie automatisch Fakten.

## Geschichte
Alte Uebergaben, Koenigsdokumente und Wahrheit-Dateien liegen in Attic/ (nicht im Repo) und sind nur Geschichte.
