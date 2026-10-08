# MODULKARTE (generiert 08.10.2026, Live-Honor, 197 Module)

Wahrheit ist die Live-Datei. Diese Karte zeigt: welcher Dienst, wer ruft wen. Verweise per Namenssuche, dynamisch gebaute Namen fehlen.
Aufgeräumt am 08.10.2026: 19 tote Module sowie 127 .bak-Dateien nach Attic/ (rückholbar, nicht im Repo). Siehe Handbuch 246.

## Dienste (runit)

- Dienst jack_telegram: jack_telegram.py
- Dienst jack_cortex: jack_cortex.py
- Dienst jack_waechter: jack_autonomous.py
- Dienst jack_autolearn: jack_autolearn_loop.py
- Dienst jack_publisher: jack_publisher_loop.py
- Dienst jack_focus_monitor: jack_focus_monitor.py
- Dienst jack_missions: jack_mission_runner.py
- Dienst jack_mcp: jack_mcp_server.py
- Dienst jack_qwen: jack_qwen_client.py

## Waisen (kein Aufrufer, Stand heute): 9

diag_snapshot, jack_bug_fixer, jack_error_door, jack_intent_parser, jack_pyflakes_lauf, jack_skill_self_creation, jack_vinted_radar, jack_whitelist_guard, kortex_controller

## Alle Module

| Modul | Rolle | Zweck (erste Zeile) |
|---|---|---|
| diag_snapshot | ORPHAN | Diagnose-Snapshot - liest nur, schreibt eine einzige Datei. |
| jack_activity_logger | Bibliothek (2 Aufrufer) | Activity-Logger: Xiaomi + Roller Events loggen (Qwen 21.08.) |
| jack_acts | Bibliothek (4 Aufrufer) | JACK_TUNE_ACTS Schritt 3. Eine Liste. Noch niemand liest sie. |
| jack_adb_heal | Bibliothek (2 Aufrufer) | SSH ok -> ADB-TCP an -> adb connect. Return 0 nur bei status device. |
| jack_agent | Bibliothek (1 Aufrufer) | JACK Autonomer Agent: arbeitet SELBSTSTAENDIG an einem Ziel - NUR in der Werkstatt. |
| jack_android | Bibliothek (1 Aufrufer) | jack_android.py - JACK 2 Android Control Module |
| jack_approval | Bibliothek (5 Aufrufer) | import os |
| jack_approval_digest | Bibliothek (1 Aufrufer) | jack_approval_digest.py — Sammel-Approval statt Einzelnachrichten. |
| jack_arbeitsplatz | Bibliothek (2 Aufrufer) | JACK_TUNE_ARBEITSPLATZ: gemeinsamer Arbeitsplatz fuer alle KIs (claude, grok, gemini). |
| jack_ast_gate | Bibliothek (1 Aufrufer) | AST-Gate: strukturelle Code-Pruefung vor Ausfuehrung. |
| jack_audit | Bibliothek (3 Aufrufer) | JACK Audit - Gesundheits- und Sicherheits-Check. Kern-Modul (nicht gegated). |
| jack_audit_run | Bibliothek (1 Aufrufer) | import sqlite3 |
| jack_auto_ingest | Bibliothek (1 Aufrufer) | jack_auto_ingest.py - Überwacht exports/ Ordner und importiert neue Dateien automatisch. |
| jack_autodoc | Bibliothek (1 Aufrufer) | jack_autodoc.py — Gemini schreibt fehlende Docstrings automatisch (staged). |
| jack_autofixer_shadow | Bibliothek (3 Aufrufer) | JACK AutoFixer mit Shadow-Execution und Ollama-Loop. |
| jack_autolearn_loop | Dienst jack_autolearn | MODULE_VERSION = 1 |
| jack_autonomous | Dienst jack_waechter | MODULE_VERSION = 1 |
| jack_briefing | Bibliothek (1 Aufrufer) | JACK Morgen-Briefing - 07:55 Uhr |
| jack_budget | Bibliothek (11 Aufrufer) | MODULE_VERSION = 1 |
| jack_budget_status | Bibliothek (1 Aufrufer) | API-Budgetstand. Read-only, keine Nebenwirkungen. |
| jack_bug_fixer | ORPHAN | import sqlite3, json, subprocess, os, sys, time, shutil |
| jack_bugfix_loop | Bibliothek (2 Aufrufer) | Autonomer Bugfix: Bug aus errors.db -> Analyse -> Fix -> Test -> Freigabe. |
| jack_callback_handler | Bibliothek (1 Aufrufer) | JACK_TUNE_CBH |
| jack_chains | Bibliothek (3 Aufrufer) | import os, sys, sqlite3, datetime, time |
| jack_changelog | Bibliothek (1 Aufrufer) | jack_changelog.py — Git-Delta → Verify-Missions für veränderte Module. |
| jack_chat_router | Bibliothek (7 Aufrufer) | MODULE_VERSION = 1 |
| jack_circuit_breaker | Bibliothek (3 Aufrufer) | jack_circuit_breaker.py — Gemini Fehler-Counter + Ollama-Failover. |
| jack_claude | Bibliothek (2 Aufrufer) | Bruecke zu Claude Code (headless) auf dem Geraet. |
| jack_cmd_crawler | Bibliothek (1 Aufrufer) | Phase 7: cmd-Namespace-Crawler |
| jack_cmd_handler | Bibliothek (2 Aufrufer) | MODULE_VERSION = 1 |
| jack_code_analyzer | Bibliothek (1 Aufrufer) | jack_code_analyzer.py — Liest Code, erkennt selbst neue Probleme, schreibt CHECK-Missions. |
| jack_code_writer | Bibliothek (1 Aufrufer) | import os |
| jack_coder | Bibliothek (5 Aufrufer) | JACK schreibt und testet Code - NUR in der Werkstatt, mit Risiko-Gate. |
| jack_config | Bibliothek (21 Aufrufer) | import os, configparser |
| jack_context_compress | Bibliothek (1 Aufrufer) | JACK Kontext-Kompression: FTS5 Pre-Filter vor Gemini. Nur Top-3 relevante Fakten senden. |
| jack_context_ingest | Bibliothek (2 Aufrufer) | jack_context_ingest.py - Ingestion pipeline for ChatGPT/Claude/MD exports. |
| jack_corr | Bibliothek (4 Aufrufer) | MODULE_VERSION = 1 |
| jack_cortex | Dienst jack_cortex | MODULE_VERSION = 2 |
| jack_critic | Bibliothek (2 Aufrufer) | import re |
| jack_curiosity | Bibliothek (1 Aufrufer) | import time, subprocess, sqlite3, os, random |
| jack_db_optimizer | Bibliothek (1 Aufrufer) | JACK DB Optimizer: Erzwingt busy_timeout=5000 und managed WAL-Checkpointing. |
| jack_db_queue | Bibliothek (2 Aufrufer) | Zentraler SQLite Write-Queue: ein Thread schreibt, alle anderen queuen. |
| jack_deadletter | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_degraded | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_delta | Bibliothek (1 Aufrufer) | Nur Veraenderungen in den Kontext - nicht bei jeder Nachricht denselben Status. |
| jack_dep_map | Bibliothek (1 Aufrufer) | jack_dep_map.py — Import-Graph für alle JACK-Module. |
| jack_episoden | Bibliothek (2 Aufrufer) | Episodisches Gedaechtnis: Momente statt Datenpunkte. |
| jack_error_door | ORPHAN | JACK_TUNE_ERRDOOR Eine Lesetuer. Dateien bleiben. |
| jack_error_to_rule | Bibliothek (1 Aufrufer) | P1 Error-to-Rule: Fehler aus jack_errors.db werden zu harten Regeln. |
| jack_errors_status | Bibliothek (1 Aufrufer) | Offene Fehler aus jack_errors.db. Read-only, keine Nebenwirkungen. |
| jack_exec | Bibliothek (8 Aufrufer) | import subprocess, os, re |
| jack_exec_parser | Bibliothek (1 Aufrufer) | import re |
| jack_explorer | Bibliothek (2 Aufrufer) | import subprocess, os, time, json, sys |
| jack_explorer_deep | Bibliothek (1 Aufrufer) | DIALOG_KEYWORDS=[ |
| jack_faehigkeiten | Bibliothek (2 Aufrufer) | jack_faehigkeiten.py - Deterministische Faehigkeits-Registry. |
| jack_focus_monitor | Dienst jack_focus_monitor | Phase 9 Delta-Layer: Fokus pollen, Dump nur bei Wechsel. |
| jack_freigabe | Bibliothek (1 Aufrufer) | Gegenstueck zum AutoFixer-Kill-Switch: Vorschlaege ansehen und freigeben. |
| jack_gedanken | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_gemini_bridge | Bibliothek (21 Aufrufer) | MODULE_VERSION = 1 |
| jack_gemini_cache | Bibliothek (1 Aufrufer) | jack_gemini_cache.py — Context Caching für Gemini API. |
| jack_ghost | Bibliothek (5 Aufrufer) | import subprocess, re, xml.etree.ElementTree as ET |
| jack_graceful | Bibliothek (1 Aufrufer) | Wenn Xiaomi offline: aktive Mission pausieren, Telegram kurz informieren. |
| jack_graph | Bibliothek (9 Aufrufer) | MODULE_VERSION = 2 |
| jack_grid_vision | Bibliothek (1 Aufrufer) | import base64, io, re, json |
| jack_groq_bridge | Bibliothek (8 Aufrufer) | MODULE_VERSION = 1 |
| jack_guard | Bibliothek (4 Aufrufer) | MODULE_VERSION = 1 |
| jack_haliza | Bibliothek (5 Aufrufer) | MODULE_VERSION = 1 |
| jack_handbuch_gate | Bibliothek (1 Aufrufer) | JACK_TUNE_HBGATE: Handbuch-Pflicht fuer jede KI, die ueber MCP schreibt. |
| jack_harvest | Bibliothek (2 Aufrufer) | MODULE_VERSION = 1 |
| jack_harvest_lernen | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_hb_alarm | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_health | Bibliothek (13 Aufrufer) | Kurz-Health: Dienste, SSH, Heartbeats, Tune  # JACK_TUNE_HEALTH → jack_health_now.json |
| jack_health_monitor | Bibliothek (2 Aufrufer) | jack_health_monitor.py — Nach Approve: Selftest, Score gesunken → Rollback. |
| jack_heartbeat | Bibliothek (11 Aufrufer) | MODULE_VERSION = 2  # bumped by shadow |
| jack_heat_protection | Bibliothek (8 Aufrufer) | Heat-Protection + Worker-Target (Qwen 22.08. P4) |
| jack_hey | Bibliothek (2 Aufrufer) | JACK Hey - Hands-free Sprach-Interaktion mit End-to-End-Stoppuhr. |
| jack_improve | Bibliothek (2 Aufrufer) | JACK verbessert eigenen Code: Vorschlag -> Freigabe -> Patch -> Auto-Rollback. |
| jack_inbox | Bibliothek (1 Aufrufer) | import urllib.request,json,os,time,threading |
| jack_intent | Bibliothek (6 Aufrufer) | MODULE_VERSION = 1 |
| jack_intent_apps | Bibliothek (2 Aufrufer) | App-Starts ohne LLM - verifizierte Map aus pm list packages (Qwen 21.08.) |
| jack_intent_lookup | Bibliothek (2 Aufrufer) | Settings-Navigation mit standardisierten Actions (Qwen 21.08.) |
| jack_intent_parser | ORPHAN | Phase 8: Intent-Katalog-Parser |
| jack_kanal | Bibliothek (1 Aufrufer) | JACK_TUNE_KANAL: Briefkasten + Reservierung zwischen den KIs (claude, grok, gemini, dima). |
| jack_karte | Bibliothek (1 Aufrufer) | JACK Kartierung v2: Settings-Bildschirme mit Fokus-Verifikation. |
| jack_keyboards | Bibliothek (2 Aufrufer) | MODULE_VERSION = 1 |
| jack_learn | Bibliothek (3 Aufrufer) | import sys, json, sqlite3, datetime |
| jack_lerner | Bibliothek (3 Aufrufer) | Stufe 2: lernt Xiaomi-Einstellungen durch reversible Experimente. |
| jack_live_bridge | Bibliothek (1 Aufrufer) | import os |
| jack_log | Bibliothek (51 Aufrufer) | jack_log.py — Zentraler Logger für alle JACK-Module. |
| jack_logging | Bibliothek (54 Aufrufer) | Zentrales strukturiertes Logging fuer JACK. |
| jack_lokal | Bibliothek (3 Aufrufer) | Lokale Inferenz mit harten Guards: RAM, Temperatur, Timeout. |
| jack_loop | Bibliothek (1 Aufrufer) | import json, os, time, subprocess, sys |
| jack_math | Bibliothek (1 Aufrufer) | import re |
| jack_mcp_server | Dienst jack_mcp | JACK MCP Server — Tools für externe KIs (Claude, Gemini, Qwen) |
| jack_memory | Bibliothek (29 Aufrufer) | import sqlite3, os, hashlib |
| jack_memory_pruning | Bibliothek (1 Aufrufer) | P2 Memory-Pruning: Alte Einträge komprimieren (Qwen 21.08.) |
| jack_memory_tree | Bibliothek (2 Aufrufer) | Baumstruktur fuer JACK Memory. |
| jack_mission_gen | Bibliothek (1 Aufrufer) | jack_mission_gen.py — JACK generiert Fix-Missions aus fail/-Einträgen. |
| jack_mission_prioritizer | Bibliothek (1 Aufrufer) | jack_mission_prioritizer.py — Sortiert pending/ nach Priorität. |
| jack_mission_pull | Bibliothek (1 Aufrufer) | JACK_TUNE_BRIDGE |
| jack_mission_queue | Bibliothek (1 Aufrufer) | Einfache Mission-Queue: JSON-Liste, nächste aktiv setzen. |
| jack_mission_run | Bibliothek (1 Aufrufer) | Aktive Mission -> plan_in -> overmind client -> result. |
| jack_mission_runner | Dienst jack_missions | MODULE_VERSION = 1 |
| jack_missions | Bibliothek (13 Aufrufer) | MODULE_VERSION = 1 |
| jack_monitor | Bibliothek (4 Aufrufer) | JACK Monitor: Event-driven Ueberwachung + /scan Befehl. |
| jack_nc | Bibliothek (2 Aufrufer) | import os, subprocess |
| jack_observer | Bibliothek (1 Aufrufer) | import re |
| jack_ollama_gate | Bibliothek (4 Aufrufer) | --------------------------------------------------------------- |
| jack_operator | Bibliothek (1 Aufrufer) | from jack_approval import confirm_action |
| jack_oracle | Bibliothek (7 Aufrufer) | MODULE_VERSION = 1 |
| jack_outcome | Bibliothek (1 Aufrufer) | import json, os, time, subprocess, sys |
| jack_outcome_tracker | Bibliothek (2 Aufrufer) | Outcome-Tracking: Jede Ausfuehrung wird gespeichert (Qwen 21.08.) |
| jack_overmind_client | Bibliothek (3 Aufrufer) | OVERMIND_MIN_INTERVAL = 180  # Sekunden zwischen API-Teacher-Calls |
| jack_patch | Bibliothek (3 Aufrufer) | Sichere SEARCH/REPLACE-Patches. Nie ganze Dateien ueberschreiben. |
| jack_patch_memory | Bibliothek (2 Aufrufer) | JACK Code-Gedaechtnis: merkt sich welche Patches durchkamen und welche nicht. |
| jack_planner | Bibliothek (4 Aufrufer) | import json,os,time,subprocess,sys |
| jack_publish | Bibliothek (8 Aufrufer) | Veroeffentlicht SANITIERTEN JACK-Kontext oeffentlich fuer Claude/andere KIs. |
| jack_publisher_loop | Dienst jack_publisher | Publisher-Loop: context.md alle 3 Min nach jack-context pushen. |
| jack_pyflakes_lauf | ORPHAN | JACK_TUNE_PYFLAKES: nur lesen. pyflakes ueber alle Module, Bericht nach ARBEITSPLATZ/gemei |
| jack_queue | Bibliothek (2 Aufrufer) | JACK Queue: Priority Task Queue fuer autonome Aktionen. |
| jack_queue_gate | Bibliothek (7 Aufrufer) | MODULE_VERSION=1 |
| jack_quota | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_qwen_client | Dienst jack_qwen | Qwen-Client — sammelt periodisch JACK-Daten für externe KI |
| jack_radar | Bibliothek (1 Aufrufer) | JACK Kleinanzeigen Radar |
| jack_read_door | Bibliothek (1 Aufrufer) | JACK_TUNE_READDOOR Graph, dann Memory, dann Identity. Eine Suche. |
| jack_reflexion | Bibliothek (1 Aufrufer) | Echte Proaktivitaet: JACK meldet sich weil ihm was auffaellt. |
| jack_router | Bibliothek (1 Aufrufer) | Entscheidet lokal oder Cloud. Regelbasiert - kein LLM-Call fuer die Entscheidung. |
| jack_sandbox | Bibliothek (1 Aufrufer) | JACK_TUNE_SANDBOX Uebungsplatz. Schreibt und laeuft nur unter jack_sandbox. Kern bleibt zu |
| jack_sanity | Bibliothek (1 Aufrufer) | import os |
| jack_scheduler | Bibliothek (1 Aufrufer) | JACK Scheduler: schwere Jobs nur in Power-Time (08-15h) und bei genuegend RAM. |
| jack_score_avg | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_scout | Bibliothek (2 Aufrufer) | JACK Scout - Faehigkeits-Fingerabdruck des Geraets. |
| jack_screen_mapper | Bibliothek (2 Aufrufer) | Screen-State-Mapping Phase 1: UI-Dump Parser |
| jack_self_audit | Bibliothek (1 Aufrufer) | JACK Meta-Autonomie: generiert SYSTEM_STATE.md fuer KI-Onboarding ohne manuellen Kontext-D |
| jack_self_improve | Bibliothek (1 Aufrufer) | JACK Selbstverbesserung - Stiller Fixmann |
| jack_selfsee | Bibliothek (3 Aufrufer) | import json, os, subprocess, time, re |
| jack_selftest | Bibliothek (6 Aufrufer) | jack_selftest.py — Ein Kommando, kompletter JACK-Systemcheck. |
| jack_semantic_analyzer | Bibliothek (1 Aufrufer) | jack_semantic_analyzer.py — Gemini reviewt Core-Module qualitativ. |
| jack_sensors | Bibliothek (4 Aufrufer) | JACK Sinne: Xiaomi-Sensoren via SSH + Gemini Vision (Augen). |
| jack_skill_builder | Bibliothek (2 Aufrufer) | JACK Skill-Builder: liest den Fingerabdruck, findet Luecken, generiert Skills. |
| jack_skill_lib | Bibliothek (5 Aufrufer) | import sqlite3, json, os, time |
| jack_skill_self_creation | ORPHAN | import sqlite3 |
| jack_skill_trainer | Bibliothek (1 Aufrufer) | Skill-Trainer: fuehrt taeglich bis zu 3 sichere CANDIDATE/TESTING-Skills aus. |
| jack_skills | Bibliothek (15 Aufrufer) | JACK Skill-Bibliothek: erfolgreiche Code-Bausteine speichern + kostenlos wiederverwenden. |
| jack_skills_db | Bibliothek (1 Aufrufer) | Adapter: jack_skills.db Skills ueber gleiche Schnittstelle wie jack_skills.py. |
| jack_snapshot | Bibliothek (1 Aufrufer) | import os, json, subprocess, sqlite3, datetime |
| jack_stand | Bibliothek (1 Aufrufer) | jack_stand.py — misst den Ist-Zustand, schreibt reports/flugschreiber_stand.json. |
| jack_state | Bibliothek (1 Aufrufer) | JACK State Machine: erkennt Schichtstart, Fahrtmodus, Feierabend anhand Zeit+Kontext. |
| jack_stress | Bibliothek (1 Aufrufer) | JACK Stresstest: prueft Sicherheitsgates hart, nicht nur Syntax. |
| jack_subagent | Bibliothek (1 Aufrufer) | import threading, subprocess, datetime, os |
| jack_talk | Bibliothek (9 Aufrufer) | import os |
| jack_talk_contract | Bibliothek (2 Aufrufer) | import json,os,re,sys |
| jack_talk_trainer | Bibliothek (1 Aufrufer) | jack_talk_trainer.py — Automatischer JACK-Lehrer. Liest Samples, fragt Gemini, härtet Pers |
| jack_telegram | Dienst jack_telegram | MODULE_VERSION = 1 |
| jack_telemetry | Bibliothek (1 Aufrufer) | jack_telemetry: kompakte Messwerte von Honor und Xiaomi alle 5 Min. JACK_TUNE_TELEMETRIE |
| jack_thermal | Bibliothek (1 Aufrufer) | JACK Thermal Monitor - zeigt was das Geraet heiss macht. |
| jack_thermal_guard | Bibliothek (1 Aufrufer) | jack_thermal_guard.py — Akku+Temp Check vor schweren Jobs. |
| jack_traceback | Bibliothek (1 Aufrufer) | import re, os, sqlite3, datetime |
| jack_tuev3 | Bibliothek (1 Aufrufer) | JACK TUEV v3 - Vollständiger Funktionstest aller Befehle und Kanäle. |
| jack_tun | Bibliothek (1 Aufrufer) | JACK_TUNE_TUN Intent und Datei vor Tippen. |
| jack_ui | Bibliothek (5 Aufrufer) | Schöne Konsolen-Ausgabe mit ANSI-Farben und Box-Drawing |
| jack_ui_agent | Bibliothek (1 Aufrufer) | import subprocess,os,time,sys |
| jack_ui_elements | Bibliothek (1 Aufrufer) | Element-Agent mit hartem Ziel (AppAgent-Light). |
| jack_ui_nav | Bibliothek (1 Aufrufer) | Xiaomi System-Nav: Back / Home / Recents via keyevent. |
| jack_ui_read | Bibliothek (1 Aufrufer) | Direkt Doku oeffnen, scrollen, Elemente tippen. Kein Google-Drift. |
| jack_ui_session | Bibliothek (3 Aufrufer) | UI-Session: Vordergrund + optional UI-Dump vom Xiaomi. Lesen vor Schreiben. |
| jack_ui_type | Bibliothek (2 Aufrufer) | UI tippen: EditText finden, leeren, Text setzen, Enter. |
| jack_vecdb | Bibliothek (2 Aufrufer) | import os |
| jack_verify_gate | Bibliothek (3 Aufrufer) | Shadow/Verify-Gate: wiederholen bis n OK, sonst kein Erfolg. |
| jack_vinted_radar | ORPHAN | JACK Vinted Radar - Eigenstaendiger Bot |
| jack_vision | Bibliothek (4 Aufrufer) | JACK Vision: Xiaomi-Screen -> Gemini 2.5 Flash via REST (kein genai-Paket). |
| jack_vision_selector | Bibliothek (2 Aufrufer) | jack_vision_selector.py - Text-Tap via uiautomator. Update-immun. Immer frischer Dump. |
| jack_voice | Bibliothek (3 Aufrufer) | import os |
| jack_voice_el | Bibliothek (1 Aufrufer) | Stub fuer jack_voice_el (ElevenLabs Voice). |
| jack_voice_handler | Bibliothek (1 Aufrufer) | MODULE_VERSION = 1 |
| jack_voice_live | Bibliothek (1 Aufrufer) | import asyncio, os, sys, time, wave |
| jack_voice_processor | Bibliothek (2 Aufrufer) | import os |
| jack_voice_router | Bibliothek (2 Aufrufer) | import os |
| jack_voraussetzung | Bibliothek (1 Aufrufer) | Prueft ob eine Aktion ueberhaupt moeglich ist - bevor sie fehlschlaegt. |
| jack_web_ingest | Bibliothek (1 Aufrufer) | import os |
| jack_whisper_async | Bibliothek (1 Aufrufer) | import subprocess |
| jack_whitelist_guard | ORPHAN | JACK_TUNE_WLGUARD - prueft ob beide ALLOWED-Whitelists synchron sind |
| jack_wissen_ernte | Bibliothek (2 Aufrufer) | Erntet Ground-Truth-Systemwissen vom Xiaomi. Kein Raten, keine Vision. |
| jack_wissen_tief | Bibliothek (1 Aufrufer) | Stufe 0: reichert die geernteten Namen mit echten Bedeutungen an. |
| jack_workers | Bibliothek (1 Aufrufer) | Multi-Worker Registry (P11, Qwen 22.08.) |
| jack_write | Bibliothek (4 Aufrufer) | import os, re |
| jack_xiaomi | Bibliothek (8 Aufrufer) | import subprocess |
| jack_xiaomi_inspector | Bibliothek (1 Aufrufer) | import subprocess |
| jack_xiaomi_think | Bibliothek (1 Aufrufer) | import os, re, time, json, subprocess, urllib.request |
| jack_xiaomi_unlock | Bibliothek (7 Aufrufer) | Xiaomi Screen-Unlock vor UI-Befehlen (Qwen 21.08.) |
| jack_xiaomi_web | Bibliothek (1 Aufrufer) | import os, re, time, json, subprocess, urllib.request |
| jack_yt_hybrid | Bibliothek (2 Aufrufer) | JACK_YT_HYBRID — Lock/Home → RVX → Suche → OCR-Check → UI-Dump-Tap |
| jack_yt_sido | Bibliothek (1 Aufrufer) | import sys, time, subprocess |
| kortex_controller | ORPHAN | from kortex_memory import add_memory, search_memory, get_recent |
| kortex_memory | Bibliothek (6 Aufrufer) | import sqlite3, os |
| kortex_profile_updater | Bibliothek (1 Aufrufer) | Analysiert neue learned_facts und schreibt relevante |
| wirkungs_check | Bibliothek (1 Aufrufer) | import subprocess, os, time |
