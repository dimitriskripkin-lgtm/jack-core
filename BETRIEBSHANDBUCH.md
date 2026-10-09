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
106. [jack_voice_handler.py](BETRIEBSHANDBUCH/106_voice_handler.md) — Sprache rein
107. [jack_self_improve.py](BETRIEBSHANDBUCH/107_self_improve.md) — stiller Fixmann, unbewiesen
108. [Naechste Schnitte](BETRIEBSHANDBUCH/108_naechste.md) — nicht entschieden
109. [Gegenzeichnung](BETRIEBSHANDBUCH/109_gegenzeichnung.md) — Kern 15:54
110. [Waechter-Neustart](BETRIEBSHANDBUCH/110_waechter_neustart.md) — sv up ohne down-Datei
111. [Publisher-Loop](BETRIEBSHANDBUCH/111_publisher_loop.md) — 180s
112. [Autolearn-Takt](BETRIEBSHANDBUCH/112_autolearn_rate.md) — 6h
113. [Talk-Kopf](BETRIEBSHANDBUCH/113_talk_kopf.md) — Version dreimal
114. [Router](BETRIEBSHANDBUCH/114_router.md) — eine Leitung
115. [Zweitpass](BETRIEBSHANDBUCH/115_zweitpass.md) — Kern zu
116. [jack_agent.py](BETRIEBSHANDBUCH/116_agent.md) — nur Werkstatt
117. [jack_freigabe.py](BETRIEBSHANDBUCH/117_freigabe.md) — siebter Weg
118. [jack_guard.py](BETRIEBSHANDBUCH/118_guard.md) — RAM
119. [jack_haliza.py](BETRIEBSHANDBUCH/119_haliza.md) — vor dem Patch
120. [jack_ghost.py](BETRIEBSHANDBUCH/120_ghost.md) — UI-Dump
121. [jack_deadletter.py](BETRIEBSHANDBUCH/121_deadletter.md) — nach 3
122. [jack_hey.py](BETRIEBSHANDBUCH/122_hey.md) — Sprache
123. [jack_inbox.py](BETRIEBSHANDBUCH/123_inbox.md) — Eingang
124. [jack_dep_map.py](BETRIEBSHANDBUCH/124_dep_map.md) — Import-Graph
125. [jack_intent_apps.py](BETRIEBSHANDBUCH/125_intent_apps.md) — App ohne Modell
126. [jack_aufraeumen.py](BETRIEBSHANDBUCH/126_aufraeumen.md) — loescht nie
127. [jack_auto_ingest.py](BETRIEBSHANDBUCH/127_auto_ingest.md) — exports
128. [jack_bug_fixer.py](BETRIEBSHANDBUCH/128_bug_fixer.md) — Fixer
129. [jack_code_writer.py](BETRIEBSHANDBUCH/129_code_writer.md) — Schreiber
130. [jack_curiosity.py](BETRIEBSHANDBUCH/130_curiosity.md) — Neugier
131. [jack_gedanken.py](BETRIEBSHANDBUCH/131_gedanken.md) — warum
132. [jack_harvest.py](BETRIEBSHANDBUCH/132_harvest.md) — Chrome-Screenshot
133. [jack_hb_alarm.py](BETRIEBSHANDBUCH/133_hb_alarm.md) — 3 und 3h
134. [jack_health_monitor.py](BETRIEBSHANDBUCH/134_health_monitor.md) — nach Freigabe
135. [jack_improve.py](BETRIEBSHANDBUCH/135_improve.md) — achter Weg
136. [jack_budget_status.py](BETRIEBSHANDBUCH/136_budget_status.md) — nur lesen
137. [jack_calltest.py](BETRIEBSHANDBUCH/137_calltest.md) — Aufruf da
138. [jack_changelog.py](BETRIEBSHANDBUCH/138_changelog.md) — Git zu Mission
139. [jack_cmd_crawler.py](BETRIEBSHANDBUCH/139_cmd_crawler.md) — Xiaomi nur lesen
140. [jack_code_analyzer.py](BETRIEBSHANDBUCH/140_code_analyzer.md) — CHECK
141. [jack_errors_status.py](BETRIEBSHANDBUCH/141_errors_status.md) — nur lesen
142. [jack_exec_parser.py](BETRIEBSHANDBUCH/142_exec_parser.md) — neunter Weg
143. [jack_faehigkeiten.py](BETRIEBSHANDBUCH/143_faehigkeiten.md) — Liste
144. [jack_gemini_cache.py](BETRIEBSHANDBUCH/144_gemini_cache.md) — Token
jack_briefing_cron.py fehlt.
145. [jack_grid_vision.py](BETRIEBSHANDBUCH/145_grid_vision.md) — Gitter
146. [jack_harvest_lernen.py](BETRIEBSHANDBUCH/146_harvest_lernen.md) — Fakten aus Chats
147. [jack_install.py](BETRIEBSHANDBUCH/147_install.md) — Install
148. [jack_lokal.py](BETRIEBSHANDBUCH/148_lokal.md) — lokal mit Gitter
149. [jack_loop.py](BETRIEBSHANDBUCH/149_loop.md) — Schleife
150. [jack_math.py](BETRIEBSHANDBUCH/150_math.md) — Rechnen
151. [jack_monitor.py](BETRIEBSHANDBUCH/151_monitor.md) — Scan
152. [jack_outcome_tracker.py](BETRIEBSHANDBUCH/152_outcome.md) — Ergebnis
jack_net_discover.py fehlt. jack_persona.py fehlt, Persona ist kern.md.
153. [jack_subagent.py](BETRIEBSHANDBUCH/153_subagent.md) — Thread
154. [jack_talk_contract.py](BETRIEBSHANDBUCH/154_talk_contract.md) — Proben
155. [jack_thermal.py](BETRIEBSHANDBUCH/155_thermal.md) — Hitze
156. [jack_ui_type.py](BETRIEBSHANDBUCH/156_ui_type.md) — tippen
157. [jack_verify_gate.py](BETRIEBSHANDBUCH/157_verify_gate.md) — n mal OK
Fehlen: jack_pull.py, jack_seal.py, jack_seal_night.py, jack_spotify.py, jack_watchdog.py.
158. [jack_android.py](BETRIEBSHANDBUCH/158_android.md) — Xiaomi
159. [jack_missions.py](BETRIEBSHANDBUCH/159_missions.md) — Liste
160. [jack_publish.py](BETRIEBSHANDBUCH/160_publish.md) — ohne Secrets
161. [jack_skill_trainer.py](BETRIEBSHANDBUCH/161_skill_trainer.md) — 3 am Tag
162. [jack_skills.py](BETRIEBSHANDBUCH/162_skills.md) — Bausteine
163. [jack_vecdb.py](BETRIEBSHANDBUCH/163_vecdb.md) — Vektoren
164. [jack_voice_router.py](BETRIEBSHANDBUCH/164_voice_router.md) — Stimme
165. [jack_xiaomi_unlock.py](BETRIEBSHANDBUCH/165_xiaomi_unlock.md) — Wake und Wisch
Fehlen auch: jack_identity.py, jack_main.py.
166. [jack_ui_nav.py](BETRIEBSHANDBUCH/166_ui_nav.md) — Tasten
167. [jack_ui_session.py](BETRIEBSHANDBUCH/167_ui_session.md) — erst lesen
168. [jack_ui_read.py](BETRIEBSHANDBUCH/168_ui_read.md) — Doku
169. [jack_ui_elements.py](BETRIEBSHANDBUCH/169_ui_elements.md) — Ziel
170. [jack_vision_once.py](BETRIEBSHANDBUCH/170_vision_once.md) — ein Bild
171. [jack_vision_selector.py](BETRIEBSHANDBUCH/171_vision_selector.md) — frischer Dump
172. [jack_voraussetzung.py](BETRIEBSHANDBUCH/172_voraussetzung.md) — vor dem Fail
173. [jack_xiaomi_think.py](BETRIEBSHANDBUCH/173_xiaomi_think.md) — Denken
174. [jack_xiaomi_web.py](BETRIEBSHANDBUCH/174_xiaomi_web.md) — Web
175. [jack_yt_hybrid.py](BETRIEBSHANDBUCH/175_yt_hybrid.md) — RVX
176. [jack_accessibility_listener.py](BETRIEBSHANDBUCH/176_accessibility_listener.md) — hoert Barrierefreiheits-Erei
177. [jack_audit_run.py](BETRIEBSHANDBUCH/177_audit_run.md) — startet den Audit.
178. [jack_callback_handler.py](BETRIEBSHANDBUCH/178_callback_handler.md) — Telegram-Knoepfe. Speichern 
179. [jack_focus_monitor.py](BETRIEBSHANDBUCH/179_focus_monitor.md) — schaut, welche App vorne ist
180. [jack_heat_protection.py](BETRIEBSHANDBUCH/180_heat_protection.md) — Waerme-Gitter. Werte OK, weg
181. [jack_intent_lookup.py](BETRIEBSHANDBUCH/181_intent_lookup.md) — sucht eine Absicht nach.
182. [jack_intent_parser.py](BETRIEBSHANDBUCH/182_intent_parser.md) — zerlegt den Satz in eine Abs
183. [jack_karte.py](BETRIEBSHANDBUCH/183_karte.md) — Karte. Ob sie live gelesen w
184. [jack_keyboards.py](BETRIEBSHANDBUCH/184_keyboards.md) — Telegram-Tastaturen.
185. [jack_lerner.py](BETRIEBSHANDBUCH/185_lerner.md) — Lerner. Journal war leer im 
186. [jack_live_bridge.py](BETRIEBSHANDBUCH/186_live_bridge.md) — Bruecke live. Ziel hinter de
187. [jack_memory_pruning.py](BETRIEBSHANDBUCH/187_memory_pruning.md) — schneidet altes Gedaechtnis.
188. [jack_memory_tree.py](BETRIEBSHANDBUCH/188_memory_tree.md) — Baum ueber dem Gedaechtnis.
189. [jack_mission_gen.py](BETRIEBSHANDBUCH/189_mission_gen.md) — erzeugt Missionen.
190. [jack_mission_prioritizer.py](BETRIEBSHANDBUCH/190_mission_prioritizer.md) — sortiert Missionen nach Wich
191. [jack_mission_pull.py](BETRIEBSHANDBUCH/191_mission_pull.md)
192. [jack_nav_learn.py](BETRIEBSHANDBUCH/192_nav_learn.md)
193. [jack_navi.py](BETRIEBSHANDBUCH/193_navi.md)
194. [jack_observer.py](BETRIEBSHANDBUCH/194_observer.md)
195. [jack_ollama_gate.py](BETRIEBSHANDBUCH/195_ollama_gate.md)
196. [jack_ollama_guard.py](BETRIEBSHANDBUCH/196_ollama_guard.md)
197. [jack_operator.py](BETRIEBSHANDBUCH/197_operator.md)
198. [jack_orchestrator.py](BETRIEBSHANDBUCH/198_orchestrator.md)
199. [jack_overmind_client.py](BETRIEBSHANDBUCH/199_overmind_client.md)
200. [jack_patch.py](BETRIEBSHANDBUCH/200_patch.md)
201. [jack_patch_memory.py](BETRIEBSHANDBUCH/201_patch_memory.md)
202. [jack_personality.py](BETRIEBSHANDBUCH/202_personality.md)
203. [jack_queue_gate.py](BETRIEBSHANDBUCH/203_queue_gate.md)
204. [jack_quota.py](BETRIEBSHANDBUCH/204_quota.md)
205. [jack_qwen_client.py](BETRIEBSHANDBUCH/205_qwen_client.md)
206. [jack_reflexion.py](BETRIEBSHANDBUCH/206_reflexion.md)
207. [jack_sanity.py](BETRIEBSHANDBUCH/207_sanity.md)
208. [jack_scheduler.py](BETRIEBSHANDBUCH/208_scheduler.md)
209. [jack_score_avg.py](BETRIEBSHANDBUCH/209_score_avg.md)
210. [jack_scout.py](BETRIEBSHANDBUCH/210_scout.md)
211. [jack_selftest.py](BETRIEBSHANDBUCH/211_selftest.md)
212. [jack_skill_builder.py](BETRIEBSHANDBUCH/212_skill_builder.md)
213. [jack_skills_db.py](BETRIEBSHANDBUCH/213_skills_db.md)
214. [jack_state.py](BETRIEBSHANDBUCH/214_state.md)
215. [jack_traceback.py](BETRIEBSHANDBUCH/215_traceback.md)
216. [jack_ui_agent.py](BETRIEBSHANDBUCH/216_ui_agent.md)
217. [jack_vinted_radar.py](BETRIEBSHANDBUCH/217_vinted_radar.md)
218. [jack_voice_chat_live.py](BETRIEBSHANDBUCH/218_voice_chat_live.md)
219. [jack_voice_el.py](BETRIEBSHANDBUCH/219_voice_el.md)
220. [jack_voice_live.py](BETRIEBSHANDBUCH/220_voice_live.md)
221. [jack_voice_processor.py](BETRIEBSHANDBUCH/221_voice_processor.md)
222. [jack_web_ingest.py](BETRIEBSHANDBUCH/222_web_ingest.md)
223. [jack_whisper_async.py](BETRIEBSHANDBUCH/223_whisper_async.md)
224. [jack_whitelist_guard.py](BETRIEBSHANDBUCH/224_whitelist_guard.md)
225. [jack_wissen_ernte.py](BETRIEBSHANDBUCH/225_wissen_ernte.md)
226. [jack_wissen_tief.py](BETRIEBSHANDBUCH/226_wissen_tief.md)
227. [jack_workers.py](BETRIEBSHANDBUCH/227_workers.md)
228. [jack_xiaomi_inspector.py](BETRIEBSHANDBUCH/228_xiaomi_inspector.md)
229. [jack_yt_sido.py](BETRIEBSHANDBUCH/229_yt_sido.md)
Repo-Luecke 03.10. zu. 197 jack_*.py haben einen Namen im Handbuch.
230. [Zweitpass scharf](BETRIEBSHANDBUCH/230_zweitpass_scharf.md) — loeschen, lernen, Ollama-Datei
231. [jack_tun.py](BETRIEBSHANDBUCH/231_tun_cleartask.md) — Intent-Bruecke, CLEARTASK-Fix (06.10.)

## Wichtigste Funde bisher, über alle Kapitel hinweg
- **Mindestens fünf unabhängige Freigabe-/Bestätigungs-Mechanismen** im Gesamtsystem (Shadow+pending_approvals,
  Self-Tooling-Proposals, PENDING_EXEC, PENDING_WRITE, selfsee_pending) — kennen sich nicht, nie vereinheitlicht.
- **Zwei unabhängige Wege, Fakten in den Graph zu schreiben** (`_do_save_fakt` im Chat, `graph_add_fact` als Act).
- **GELOEST 06.10.2026** (JACK_TUNE_DEADTHREADS): Zwei parallele Mission-Systeme bestaetigt real -
  `jack_missions.py`-Thread im Waechter lief seit Wochen leer mit (niemand fuettert jack_missions.db
  mehr), Thread-Start entfernt. jack_missions.py selbst bleibt (Telegram-Status-Befehl /missions_alt
  liest uebersicht()), nur der Ausfuehr-Thread ist weg. jack_oracle.py bleibt (wird anderswo gebraucht).
- Doppelte Codepfade für Xiaomi-App-Steuerung (MCP-Act vs. Freitext-Regex direkt in jack_telegram.py) -
  weiterhin offen.
- **GELOEST 06.10.2026** (JACK_TUNE_DEADTHREADS): `_publisher_loop`-Thread im Waechter war echte
  Dopplung zum `jack_publisher`-Dienst (identische push()-Funktion alle 180s) - Thread-Start entfernt.
- **NEU 06.10.2026**: Ein zweiter, komplett ungefilterter Plan-Ausfuehrungsweg existiert in
  jack_telegram.py: `[[PLAN:...]]`-Syntax (Zeile ~347) ruft jack_planner.run_plan() direkt auf,
  OHNE Act-Whitelist und ohne den exec-Schritt-Filter, den plan_try (Kapitel 1) hat. Noch nicht
  gehaertet. Naechster Kandidat fuer die Haertungs-Reihe.
- Eine bisher undokumentierte vierte Datenbank: `jack_outcomes.db`.

## Technische Lehre aus dem Bau dieses Handbuchs selbst (02.10.2026)
Das Mission-System hat ein Größenlimit von ca. 10KB pro Schreib-Mission. Eine einzelne wachsende
Datei per `py_replace` mit der kompletten alten Datei als Anker verdoppelt das Paket bei jedem
Schritt und reißt dieses Limit schnell — Fehlschläge wurden dabei lange **nicht ehrlich gemeldet**
(`ok: true` trotz tatsächlich nicht geschriebenem Inhalt). Zusätzlich blähte eine eigene
Werkzeug-Fehler (`json.dumps` ohne `ensure_ascii=False`) deutsche Sonderzeichen auf das Dreifache
auf. Lösung: viele kleine, einzeln verifizierte Dateien statt einer wachsenden großen.
**Für jeden Schreibvorgang gilt ab jetzt: roh gegenlesen, nicht nur `ok: true` vertrauen.**

## Update 06.10.2026 (Claude, Honor-Live-Session)
Vier neue Module/Erweiterungen seit dem letzten Stand dieses Index, siehe eigene Kapitel:
- `jack_tun.py` bekam CLEARTASK-Fix (Kapitel 231) - Android liess vorherige Settings-Seite haengen.
- `jack_mission_runner.py`: neue Acts `plan_try`/`skill_confirm` (Skill-Werkstatt mit Dima als
  Pruefer), `honor_net_scan` (read-only Netzdiagnose, `ip neigh` scheitert ohne Root - siehe
  Kapitel 1), `xiaomi_screenshot` (echter Screenshot als Base64-Datei fuer read_file, kein
  Gemini-Umweg, kein Budget-Verbrauch), `xiaomi_ssh_check` mit optionalem `ip`-Override.
- `jack_cortex.py`: `find_xiaomi()` synct `~/.ssh/config` jetzt in JEDEM Erfolgszweig
  (vorher nur im arp-scan-Zweig, der auf Root-freiem Honor nie laufen konnte) - Kapitel 34.
- `jack_autonomous.py`: zwei tote Threads entfernt (`_missions_loop`, `_publisher_loop`) - Kapitel 3.
Alle vier live bewiesen, Backups im Attic, committed als `2a7cb2d2`.

## Stand 08.10.2026 (Kapitel 241-247)
- [241 Stufe R + Nachtlauf](BETRIEBSHANDBUCH/241_stufe_r_lese_acts.md)
- [243 Ladealarm + Cloud-Nachtlauf](BETRIEBSHANDBUCH/243_ladealarm_cloudzugang.md)
- [244 Xiaomi-Gateway](BETRIEBSHANDBUCH/244_xiaomi_gateway.md)
- [245 Telemetrie](BETRIEBSHANDBUCH/245_telemetrie.md)
- [246 Ausduennung](BETRIEBSHANDBUCH/246_ausduennung.md)
- [247 Neu seit 07.10. Ueberblick](BETRIEBSHANDBUCH/247_neu_seit_0710.md)
- [248 MCP-Rollen-Zugang](BETRIEBSHANDBUCH/248_mcp_rollen_zugang.md)
- [249 Tiefenanalyse 09.10.2026](BETRIEBSHANDBUCH/249_tiefenanalyse_20261009.md)
- [250 Tiefenanalyse-Fixes B1-B3](BETRIEBSHANDBUCH/250_tiefenanalyse_fixes_b1_b3.md)
- [251 Dienst-Logs und Log-Prozesse](BETRIEBSHANDBUCH/251_dienst_logs.md)
- [252 Xiaomi-Karte und Vorfall offene Root-API](BETRIEBSHANDBUCH/252_xiaomi_karte_vorfall.md)
- Modulkarte (generiert): MODULKARTE.md
