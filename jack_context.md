# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-23T05:10:46.562515

## Owner / Kern
- Owner: Dimitri
- Hardware: Honor Magic8 Pro (Host/Gehirn) + Xiaomi 11T Pro (Slave via SSH)
- Vision: Lokales autonomes AI-OS, offline-first, JACK als Exit-Vehicle fuer mehr Unabhaengigkeit
- WICHTIG: Dima ist der MENSCH/Nutzer. JACK ist das SYSTEM/die KI. Niemals verwechseln.

## Was JACK ueber Dima gelernt hat
- Dima ist Dimitri.
- Dima ist LKW-Fahrer mit Sprinter Kühlkoffer bei Dalhoff Feinkost in Achim (Nachtschicht).
- Dima ist Hobby-Programmierer.
- Dima ist aus Russland nach Deutschland migriert, Baujahr ca. 1996.
- Dima ist Einzelkind.
- JACK ist ein autonomes, lokales AI-OS auf Dimas Honor Magic8 Pro.
- JACK nutzt Gemini als Gehirn (API-Calls).
- JACK hat ein lokales Gedächtnis in SQLite.
- JACK soll sich selbst lernen und verbessern.
- JACK steht unter Dimas voller Kontrolle.
- JACK speichert alle Fragen und Antworten mit Zeitstempel im Gedächtnis.
- Dima hat KEINEN Hund (Rex war nur ein Test).
- JACK hat KEINEN direkten Shell- oder Dateizugriff über den Chat.
- Dima testet das Gedächtnis.
- Dima hat auf Xiaomi in Termux sshd eingegeben.
- Dima hat eine autobiographische Information hochgeladen, die JACK durchsuchen soll.
- Dima hat den Befehl gegeben, ins Verzeichnis `~/jack/titan_legacy` zu wechseln und eine Datei von GitHub zu laden.

## Aktive Module (55)
- jack_agent.py
- jack_android.py
- jack_approval.py
- jack_audit.py
- jack_autonomous.py
- jack_briefing.py
- jack_budget.py
- jack_bug_fixer.py
- jack_claude.py
- jack_code_writer.py
- jack_coder.py
- jack_config.py
- jack_consolidate.py
- jack_cortex.py
- jack_gemini_bridge.py
- jack_handshake_gen.py
- jack_hey.py
- jack_improve.py
- jack_learn.py
- jack_log.py
- jack_math.py
- jack_memory.py
- jack_memory_engine.py
- jack_memory_maintenance.py
- jack_node_alpha.py
- jack_operator.py
- jack_oracle.py
- jack_patch.py
- jack_personality.py
- jack_publish.py
- jack_radar.py
- jack_screen_tracker.py
- jack_self_improve.py
- jack_sensors.py
- jack_skills.py
- jack_snapshot.py
- jack_talk.py
- jack_telegram.py
- jack_v2.py
- jack_vecdb.py
- jack_vinted_radar.py
- jack_voice.py
- jack_voice_el.py
- jack_voice_processor.py
- jack_write.py
- jack_xiaomi.py
- jack_xiaomi_cmd.py
- kortex_controller.py
- kortex_memory.py
- kortex_profile_updater.py
- kortex_profiler.py
- kortex_sensor_daemon.py
- quick_bridge.py
- test_jack_approval.py
- voice_service_v2.py

## System-Status
- Offene Fehler: 4
- Erinnerungen: 143
- Dienste:
run: jack_cortex: (pid 19393) 2709s
run: jack_telegram: (pid 20543) 5785s
run: jack_autolearn: (pid 7339) 153298s
run: ollama: (pid 7342) 153298s

## Letzte Aenderungen
2f8ddf9 Xiaomi statische IP 10.58.220.131 dokumentiert
2fcd4fc Telegram: Inline-Buttons fuer /befehle, Callback-Handler
16c72d3 Telegram: /befehle Uebersicht fix
9ec19c7 Telegram: /befehle Uebersicht
f3d1cdd Oracle: deutsche Aliase + Ergebnis-Stack (letzte 5)
2e72523 oracle_result bugfix: json import
b494b09 oracle bugfix: import vor json.dumps gezogen
dcbaff7 oracle bugfix: json import im block
bc451eb Telegram: /oracle + /oracle_result
f5c4768 Security: Flask von 0.0.0.0 auf 127.0.0.1 (kein offener Endpoint mehr)
e374319 7 Dienste: jack_oracle live, Meilenstein 2026-07-22
9de06fc jack_oracle: bidirektionaler Claude<->JACK Kanal via GitHub, Live-Test erfolgreich (free -h)
0955315 Prompt: Titan-Lektionen still integriert
8e20a4e titan_legacy: falsche context.md entfernt, Ordner bleibt leer bis bewusste Entscheidung
ab0073f titan_legacy: Kern-DNA gesichert (Persona+Anchor+Evolution)

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.244.147.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
