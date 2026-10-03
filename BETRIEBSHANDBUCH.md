# JACK — BETRIEBSHANDBUCH (Index)

Angelegt 02.10.2026. Ziel: jedes wirklich verdrahtete Modul verstehen und nachschlagbar machen.
Ein Ordner, eine Datei pro Modul — nicht eine wachsende Monster-Datei (technischer Grund: das
Mission-System hat ein Größenlimit von ~10KB pro Schreibvorgang, siehe Lehre unten).

Methode: von den Dienst-Einstiegspunkten aus nach Zentralität sortiert, nicht alphabetisch.
Waisen (unverdrahtete Module, siehe Modulkarte) bekommen nur einen Einzeiler, keine Tiefenanalyse.

## Kapitel
1. [jack_mission_runner.py](BETRIEBSHANDBUCH/01_mission_runner.md) — Ausführungs-Engine
2. [jack_telegram.py](BETRIEBSHANDBUCH/02_telegram.md) — Haupteinstieg, Befehlsinterpreter
3. [jack_autonomous.py](BETRIEBSHANDBUCH/03_autonomous.md) — Wächter-Logik, 8 interne Threads
4. [jack_talk.py](BETRIEBSHANDBUCH/04_talk.md) — Prompt-Bau, LLM-Anbindung
5. [jack_chat_router.py](BETRIEBSHANDBUCH/05_chat_router.md) — Lane-Klassifikation, "Kiste"
6. [jack_android.py](BETRIEBSHANDBUCH/06_android.md) — UI-Automatisierung, autonomer Vision-Agent
7. [jack_autolearn_loop.py](BETRIEBSHANDBUCH/07_autolearn_loop.md) — Hintergrund-Kognition, Skills, proaktive Beobachtung
8. [jack_intent.py](BETRIEBSHANDBUCH/08_intent.md) — Autonomie-Level-System (numerisches Gate, 6. Freigabe-Variante)
9. [jack_missions.py](BETRIEBSHANDBUCH/09_missions_alt.md) — altes Mission-System, AUFGELOEST: Warteschlange praktisch immer leer
10. [jack_exec.py](BETRIEBSHANDBUCH/10_exec.md) — Freitext-EXEC, Outcomes, Denylist
11. [jack_oracle.py](BETRIEBSHANDBUCH/11_oracle.md) — alter GitHub-Befehlskanal, eigenes Gate
12. [jack_cmd_handler.py](BETRIEBSHANDBUCH/12_cmd_handler.md) — Slash, shadow/pending_approvals
13. [jack_coder.py](BETRIEBSHANDBUCH/13_coder.md) — Werkstatt, HALIZA, kein wartet_freigabe
14. [jack_write.py](BETRIEBSHANDBUCH/14_write.md) — Werkstatt-Schreiben, Critic
15. [jack_planner.py](BETRIEBSHANDBUCH/15_planner.md) — Plan-Schritte Xiaomi
16. [jack_selfsee.py](BETRIEBSHANDBUCH/16_selfsee.md) — DIAG, .selfsee_pending
17. [jack_ui_type.py](BETRIEBSHANDBUCH/17_ui_type.md) — Xiaomi-UI, zwei Tueren
18. [jack_outcome_tracker.py](BETRIEBSHANDBUCH/18_outcome_tracker.md) — jack_outcomes.db
19. [jack_graph.py](BETRIEBSHANDBUCH/19_graph.md) — Graph-Kueche
20. [jack_groq_bridge.py](BETRIEBSHANDBUCH/20_groq_bridge.md) — Groq-Ruf
21. [jack_health.py](BETRIEBSHANDBUCH/21_health.md) — Health, bat_fresh
22. [jack_gemini_bridge.py](BETRIEBSHANDBUCH/22_gemini_bridge.md) — Gemini-Ruf
23. [jack_memory.py](BETRIEBSHANDBUCH/23_memory.md) — Episoden, FTS
24. [jack_vision_selector.py](BETRIEBSHANDBUCH/24_vision_selector.md) — Text-Tap Xiaomi
25. [jack_xiaomi_unlock.py](BETRIEBSHANDBUCH/25_xiaomi_unlock.md) — Wake plus Swipe
26. [jack_mcp_server.py](BETRIEBSHANDBUCH/26_mcp_server.md) — MCP-Tuer, Token fail-open
27. [jack_heat_protection.py](BETRIEBSHANDBUCH/27_heat.md) — 55/65/75
28. [jack_callback_handler.py](BETRIEBSHANDBUCH/28_callback.md) — PENDING_EXEC im RAM
29. [jack_voice_handler.py](BETRIEBSHANDBUCH/29_voice.md) — Telegram-Sprache
30. [jack_overmind_client.py](BETRIEBSHANDBUCH/30_overmind.md) — Whitelist, 180s
31. [jack_react.py](BETRIEBSHANDBUCH/31_react.md) — Fehleranalyse
32. [jack_db_queue.py](BETRIEBSHANDBUCH/32_db_queue.md) — ein Schreiber
33. [jack_focus_monitor.py](BETRIEBSHANDBUCH/33_focus.md) — Vordergrund
34. [jack_cortex.py](BETRIEBSHANDBUCH/34_cortex.md) — Xiaomi-Steuerung
35. [jack_approval.py](BETRIEBSHANDBUCH/35_approval.md) — Pfad-Gatter
36. [jack_log.py](BETRIEBSHANDBUCH/36_log.md) — gemeinsamer Logger
37. [jack_vecdb.py](BETRIEBSHANDBUCH/37_vecdb.md) — Vektor-Suche
38. [jack_screen_mapper.py](BETRIEBSHANDBUCH/38_screen_mapper.md) — UI-Signaturen
39. [jack_budget.py](BETRIEBSHANDBUCH/39_budget.md) — 300/40, 3 Euro
40. [jack_episoden.py](BETRIEBSHANDBUCH/40_episoden.md) — Momente
41. [jack_degraded.py](BETRIEBSHANDBUCH/41_degraded.md) — Xiaomi-Flagge
42. [jack_chains.py](BETRIEBSHANDBUCH/42_chains.md) — feste Ketten
43. [jack_circuit_breaker.py](BETRIEBSHANDBUCH/43_circuit_breaker.md) — 3 Fehler, 30 min
44. [jack_critic.py](BETRIEBSHANDBUCH/44_critic.md) — verbotene Muster
45. [jack_delta.py](BETRIEBSHANDBUCH/45_delta.md) — nur Aenderungen
46. [jack_error_to_rule.py](BETRIEBSHANDBUCH/46_error_to_rule.md) — Fehler werden Regeln
47. [jack_explorer.py](BETRIEBSHANDBUCH/47_explorer.md) — App-Liste Xiaomi
48. [jack_config.py](BETRIEBSHANDBUCH/48_config.md) — config.ini
49. [jack_context_compress.py](BETRIEBSHANDBUCH/49_context_compress.md) — Top-Fakten
50. [jack_audit.py](BETRIEBSHANDBUCH/50_audit.md) — Gesundheits-Check
51. [jack_autodoc.py](BETRIEBSHANDBUCH/51_autodoc.md) — Docstrings staged
52. [jack_ast_gate.py](BETRIEBSHANDBUCH/52_ast_gate.md) — AST vor Lauf
53. [jack_context_ingest.py](BETRIEBSHANDBUCH/53_context_ingest.md) — Exporte nach Memory
54. [jack_self_audit.py](BETRIEBSHANDBUCH/54_self_audit.md) — SYSTEM_STATE
55. [jack_thermal.py](BETRIEBSHANDBUCH/55_thermal.md) — Hitze-Anzeige
56. [jack_skill_trainer.py](BETRIEBSHANDBUCH/56_skill_trainer.md) — 3 Skills am Tag
57. [jack_snapshot.py](BETRIEBSHANDBUCH/57_snapshot.md) — Zustand
58. [jack_publisher_loop.py](BETRIEBSHANDBUCH/58_publisher_loop.md) — context.md alle 3 min
59. [jack_skills.py](BETRIEBSHANDBUCH/59_skills.md) — Bausteine
60. [jack_tuev3.py](BETRIEBSHANDBUCH/60_tuev3.md) — Funktionstest
61. [jack_activity_logger.py](BETRIEBSHANDBUCH/61_activity_logger.md) — Events
62. [jack_autofixer_shadow.py](BETRIEBSHANDBUCH/62_autofixer_shadow.md) — Shadow-Fix
63. [jack_bugfix_loop.py](BETRIEBSHANDBUCH/63_bugfix_loop.md) — Fix plus Freigabe
64. [jack_corr.py](BETRIEBSHANDBUCH/64_corr.md) — Kennung
65. [jack_db_optimizer.py](BETRIEBSHANDBUCH/65_db_optimizer.md) — WAL
66. [jack_explorer_deep.py](BETRIEBSHANDBUCH/66_explorer_deep.md) — Dialog
67. [jack_radar.py](BETRIEBSHANDBUCH/67_radar.md) — eigene DB
68. [jack_ui_read.py](BETRIEBSHANDBUCH/68_ui_read.md) — Doku tippen
69. [jack_approval_digest.py](BETRIEBSHANDBUCH/69_approval_digest.md) — eine Nachricht
70. [jack_schema.py](BETRIEBSHANDBUCH/70_schema.md) — Missions-Schema
71. [jack_screen_tracker.py](BETRIEBSHANDBUCH/71_screen_tracker.md) — XML, keine Vision
72. [jack_semantic_analyzer.py](BETRIEBSHANDBUCH/72_semantic_analyzer.md) — Review staged
73. [jack_skill_self_creation.py](BETRIEBSHANDBUCH/73_skill_self_creation.md) — Kopf duenn
74. [jack_stress.py](BETRIEBSHANDBUCH/74_stress.md) — Gates hart
75. [jack_ui.py](BETRIEBSHANDBUCH/75_ui.md) — UI-Helfer
76. [jack_publish.py](BETRIEBSHANDBUCH/76_publish.md) — oeffentlicher Kontext
77. [jack_briefing.py](BETRIEBSHANDBUCH/77_briefing.md) — 07:55
78. [jack_heartbeat.py](BETRIEBSHANDBUCH/78_heartbeat.md) — Lebenszeichen
79. [jack_voraussetzung.py](BETRIEBSHANDBUCH/79_voraussetzung.md) — vor der Aktion
80. [jack_loop.py](BETRIEBSHANDBUCH/80_loop.md) — kleine Schleife
81. [jack_voice_router.py](BETRIEBSHANDBUCH/81_voice_router.md) — Sprache
82. [jack_xiaomi_think.py](BETRIEBSHANDBUCH/82_xiaomi_think.md) — Denken auf Xiaomi
83. [jack_subagent.py](BETRIEBSHANDBUCH/83_subagent.md) — Nebenlaeufer
84. [jack_ui_elements.py](BETRIEBSHANDBUCH/84_ui_elements.md) — Experiment
85. [jack_vision_once.py](BETRIEBSHANDBUCH/85_vision_once.md) — ein Bild
86. [Schwanz](BETRIEBSHANDBUCH/86_rest.md) — restliche Köpfe
87. [jack_claude.py](BETRIEBSHANDBUCH/87_claude.md) — Claude read-only
88. [jack_testbed.py](BETRIEBSHANDBUCH/88_testbed.md) — Kern-Test
89. [jack_vinted_radar.py](BETRIEBSHANDBUCH/89_vinted.md) — eigener Bot
90. [jack_stand.py](BETRIEBSHANDBUCH/90_stand.md) — Ist-Zustand
91. [jack_thermal_guard.py](BETRIEBSHANDBUCH/91_thermal_guard.md) — vor schweren Jobs
92. [jack_sensors.py](BETRIEBSHANDBUCH/92_sensors.md) — Sinne
93. [jack_xiaomi_web.py](BETRIEBSHANDBUCH/93_xiaomi_web.md) — Web auf Xiaomi
94. [jack_yt_hybrid.py](BETRIEBSHANDBUCH/94_yt_hybrid.md) — YouTube
95. [jack_adb_heal.py](BETRIEBSHANDBUCH/95_adb_heal.md) — ADB wieder an
96. [jack_graceful.py](BETRIEBSHANDBUCH/96_graceful.md) — Pause wenn offline
97. [jack_talk_trainer.py](BETRIEBSHANDBUCH/97_talk_trainer.md) — Persona-Schreiber
98. [jack_monitor.py](BETRIEBSHANDBUCH/98_monitor.md) — /scan
99. [jack_ui_session.py](BETRIEBSHANDBUCH/99_ui_session.md) — Vordergrund
100. [jack_ui_nav.py](BETRIEBSHANDBUCH/100_ui_nav.md) — Tasten
101. [jack_verify_gate.py](BETRIEBSHANDBUCH/101_verify_gate.md) — dreimal pruefen
102. [jack_talk_contract.py](BETRIEBSHANDBUCH/102_talk_contract.md) — Talk-Proben
103. [jack_skill_lib.py](BETRIEBSHANDBUCH/103_skill_lib.md) — Skills-DB
104. [jack_mission_queue.py](BETRIEBSHANDBUCH/104_mission_queue.md) — naechste Mission
105. [jack_logging.py](BETRIEBSHANDBUCH/105_logging.md) — zweiter Logger

## Wichtigste Funde bisher, über alle Kapitel hinweg
- **Mindestens fünf unabhängige Freigabe-/Bestätigungs-Mechanismen** im Gesamtsystem (Shadow+pending_approvals,
  Self-Tooling-Proposals, PENDING_EXEC, PENDING_WRITE, selfsee_pending) — kennen sich nicht, nie vereinheitlicht.
- **Zwei unabhängige Wege, Fakten in den Graph zu schreiben** (`_do_save_fakt` im Chat, `graph_add_fact` als Act).
- **Zwei mögliche parallele Mission-Systeme**: `jack_mission_runner.py` (diese Woche, MCP-Acts) und ein
  älteres `jack_missions.py` (deutsche Status-Wörter), Letzteres läuft als interner Thread im Wächter —
  noch nicht live geprüft, ob beide wirklich gleichzeitig aktiv sind. **Wichtigster offener Punkt.**
- Doppelte Codepfade für Xiaomi-App-Steuerung (MCP-Act vs. Freitext-Regex direkt in jack_telegram.py).
- Mögliche doppelte Publisher-Aktivität (`_publisher_loop`-Thread im Wächter vs. `jack_publisher`-Dienst).
- Eine bisher undokumentierte vierte Datenbank: `jack_outcomes.db`.

## Technische Lehre aus dem Bau dieses Handbuchs selbst (02.10.2026)
Das Mission-System hat ein Größenlimit von ca. 10KB pro Schreib-Mission. Eine einzelne wachsende
Datei per `py_replace` mit der kompletten alten Datei als Anker verdoppelt das Paket bei jedem
Schritt und reißt dieses Limit schnell — Fehlschläge wurden dabei lange **nicht ehrlich gemeldet**
(`ok: true` trotz tatsächlich nicht geschriebenem Inhalt). Zusätzlich blähte eine eigene
Werkzeug-Fehler (`json.dumps` ohne `ensure_ascii=False`) deutsche Sonderzeichen auf das Dreifache
auf. Lösung: viele kleine, einzeln verifizierte Dateien statt einer wachsenden großen.
**Für jeden Schreibvorgang gilt ab jetzt: roh gegenlesen, nicht nur `ok: true` vertrauen.**
