# JACK LIVE-KONTEXT (auto, 2026-08-24T02:54:14.044536)

# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-08-24T02:54:14.012264

## Owner / Kern
- Owner: Dimitri
- Hardware: Honor Magic8 Pro (Host/Gehirn) + Xiaomi 11T Pro (Slave via SSH)
- Vision: Lokales autonomes AI-OS, offline-first, JACK als Exit-Vehicle fuer mehr Unabhaengigkeit
- WICHTIG: Dima ist der MENSCH/Nutzer. JACK ist das SYSTEM/die KI. Niemals verwechseln.

## Was JACK ueber Dima gelernt hat
- Dima ist Dimitri.
[PRIVAT GEFILTERT]
[PRIVAT GEFILTERT]
## Aktive Module (173)
- diag_full_dump.py
- diag_snapshot.py
- jack_accessibility_listener.py
- jack_activity_logger.py
- jack_agent.py
- jack_android.py
- jack_anomaly.py
- jack_approval.py
- jack_ast_gate.py
- jack_audit.py
- jack_audit_run.py
- jack_aufraeumen.py
- jack_auto_ingest.py
- jack_autofixer_shadow.py
- jack_autolearn_loop.py
- jack_autonomous.py
- jack_briefing.py
- jack_briefing_cron.py
- jack_budget.py
- jack_budget_status.py
- jack_bug_fixer.py
- jack_bugfix_loop.py
- jack_calltest.py
- jack_chains.py
- jack_circuit_breaker.py
- jack_claude.py
- jack_cmd_crawler.py
- jack_code_writer.py
- jack_coder.py
- jack_config.py
- jack_consolidate.py
- jack_context_compress.py
- jack_context_ingest.py
- jack_cortex.py
- jack_critic.py
- jack_curiosity.py
- jack_db_optimizer.py
- jack_db_queue.py
- jack_delta.py
- jack_episoden.py
- jack_error_to_rule.py
- jack_errors_status.py
- jack_exec.py
- jack_exec_parser.py
- jack_explorer.py
- jack_explorer_deep.py
- jack_faehigkeiten.py
- jack_focus_monitor.py
- jack_freigabe.py
- jack_gedanken.py
- jack_gemini_bridge.py
- jack_ghost.py
- jack_grid_vision.py
- jack_groq_bridge.py
- jack_guard.py
- jack_haliza.py
- jack_handshake_gen.py
- jack_harvest.py
- jack_harvest_lernen.py
- jack_heartbeat.py
- jack_heat_protection.py
- jack_hey.py
- jack_improve.py
- jack_inbox.py
- jack_install.py
- jack_intent.py
- jack_intent_apps.py
- jack_intent_lookup.py
- jack_intent_parser.py
- jack_karte.py
- jack_karte_loop.py
- jack_learn.py
- jack_lerner.py
- jack_live_bridge.py
- jack_log.py
- jack_log_rotate.py
- jack_logging.py
- jack_lokal.py
- jack_loop.py
- jack_math.py
- jack_mcp_server.py
- jack_memory.py
- jack_memory_maintenance.py
- jack_memory_pruning.py
- jack_memory_stale.py
- jack_memory_tree.py
- jack_missions.py
- jack_monitor.py
- jack_nav_learn.py
- jack_navi.py
- jack_observer.py
- jack_operator.py
- jack_oracle.py
- jack_orchestrator.py
- jack_outcome.py
- jack_outcome_tracker.py
- jack_patch.py
- jack_patch_memory.py
- jack_personality.py
- jack_planner.py
- jack_publish.py
- jack_publisher_loop.py
- jack_queue.py
- jack_radar.py
- jack_react.py
- jack_read_curl.py
- jack_reflexion.py
- jack_rhythm.py
- jack_router.py
- jack_sanity.py
- jack_scheduler.py
- jack_schema.py
- jack_scout.py
- jack_screen_mapper.py
- jack_screen_tracker.py
- jack_self_audit.py
- jack_self_improve.py
- jack_selftest.py
- jack_sensors.py
- jack_skill_builder.py
- jack_skill_lib.py
- jack_skill_self_creation.py
- jack_skill_trainer.py
- jack_skills.py
- jack_skills_db.py
- jack_snapshot.py
- jack_state.py
- jack_stress.py
- jack_subagent.py
- jack_system_tools.py
- jack_talk.py
- jack_telegram.py
- jack_thermal.py
- jack_traceback.py
- jack_tuev2.py
- jack_tuev3.py
- jack_tuev4.py
- jack_tuev5.py
- jack_tuev6.py
- jack_ui.py
- jack_ui_agent.py
- jack_ui_elements.py
- jack_ui_read.py
- jack_vecdb.py
- jack_vinted_radar.py
- jack_vision.py
- jack_vision_once.py
- jack_vision_selector.py
- jack_voice.py
- jack_voice_chat_live.py
- jack_voice_el.py
- jack_voice_live.py
- jack_voice_processor.py
- jack_voice_router.py
- jack_voraussetzung.py
- jack_web_agent.py
- jack_web_ingest.py
- jack_whisper_async.py
- jack_wissen_ernte.py
- jack_wissen_tief.py
- jack_workers.py
- jack_write.py
- jack_xiaomi.py
- jack_xiaomi_inspector.py
- jack_xiaomi_think.py
- jack_xiaomi_unlock.py
- jack_xiaomi_web.py
- jack_yt_sido.py
- kortex_controller.py
- kortex_memory.py
- kortex_profile_updater.py
- kortex_sensor_daemon.py
- wirkungs_check.py

## System-Status
- Offene Fehler: 0
- Erinnerungen: 2530
- Dienste:
run: jack_cortex: (pid 11260) 41061s
run: jack_telegram: (pid 13010) 27912s
run: jack_autolearn: (pid 449) 26961s
fail: ollama: unable to change to service directory: file does not exist

## Letzte Aenderungen
8fcdf1c fix(autolearn): indentation for skill SSH whitelist
5c79686 feat(autolearn): SSH skill cmds only xiaomi-jack + deny list
95a43e8 feat(operator): whitelist before execute_actions shell
0238240 feat(intent): UI gate via jack_exec.handle_ui_intent before keyword/gemini
77abb72 fix(gemini): init circuit-breaker globals _CB_RESET_AT/_CB_FAILS
890dace fix(exec): forsche/chrome via short SSH timeout, no hang on am start
978b0f6 feat: UI intent gate on talk_to_gemini + waechter heartbeat sv restart
faceb0e feat(voice): UI intents before Gemini - forsche/tap/kill via jack_exec
5c25897 feat(tg): /tap /forsche /kill via jack_exec main line
388492c feat(exec): tap_text via vision_selector before shell/Monkey path
8521341 fix(ui): guard falls back to do_step for unknown skill actions
b8615c0 fix(ui): run_guarded understands action=open target=SETTINGS
3da7e18 feat(ui): cortex skills via run_guarded (step_guard)
9d7f89e feat(ui): step_guard Preflight/Overlay/Rollback + guarded settings demo
f223361 Publisher: Push reaktiviert, Loop-Service angelegt

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.244.147.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.


## Letzte 20 Aktionen (Logbuch)

[2026-08-21 10:22:32] SELF-AUDIT | SYSTEM_STATE.md generiert
[2026-08-21 10:22:32] SCHEDULER | Power-Time aktiv - schwere Jobs erlaubt
[2026-08-21 10:22:34] EXPLORE | Xiaomi: CPU=Load: 0.54 RAM=2193MB frei Akku=100% Temp=33.6C
[2026-08-21 10:22:34] SHADOW-FIXER | Keine offenen Fehler
[2026-08-21 10:27:34] SELF-AUDIT | SYSTEM_STATE.md generiert
[2026-08-21 10:27:34] SCHEDULER | Power-Time aktiv - schwere Jobs erlaubt
[2026-08-21 10:27:35] EXPLORE | Xiaomi: CPU=Load: 0.34 RAM=2421MB frei Akku=100% Temp=33.0C
[2026-08-21 10:27:35] SHADOW-FIXER | Keine offenen Fehler
[2026-08-21 10:32:35] SELF-AUDIT | SYSTEM_STATE.md generiert
[2026-08-21 10:32:35] SCHEDULER | Power-Time aktiv - schwere Jobs erlaubt
[2026-08-21 10:32:37] EXPLORE | Xiaomi: CPU=Load: 0.59 RAM=2422MB frei Akku=100% Temp=32.7C
[2026-08-21 10:32:37] SHADOW-FIXER | Keine offenen Fehler
[2026-08-21 10:37:37] SELF-AUDIT | SYSTEM_STATE.md generiert
[2026-08-21 10:37:37] SCHEDULER | Power-Time aktiv - schwere Jobs erlaubt
[2026-08-21 10:37:38] EXPLORE | Xiaomi: CPU=Load: 0.90 RAM=2122MB frei Akku=100% Temp=32.7C
[2026-08-21 10:37:38] SHADOW-FIXER | Keine offenen Fehler
[2026-08-21 10:42:38] SELF-AUDIT | SYSTEM_STATE.md generiert
[2026-08-21 10:42:38] SCHEDULER | Power-Time aktiv - schwere Jobs erlaubt
[2026-08-21 10:42:40] EXPLORE | Xiaomi: CPU=Load: 0.64 RAM=1732MB frei Akku=100% Temp=32.2C
[2026-08-21 10:42:40] SHADOW-FIXER | Keine offenen Fehler

## Budget heute
Heute: Text 0/300 | Vision 0/40 | Tokens 0