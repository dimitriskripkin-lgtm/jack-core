# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-16T08:46:19.723882

## Owner / Kern
- Owner: Dimitri
- Hardware: Honor Magic8 Pro (Host/Gehirn) + Xiaomi 11T Pro (Slave via SSH)
- Vision: Lokales autonomes AI-OS, offline-first, JACK als Exit-Vehicle fuer mehr Unabhaengigkeit
- WICHTIG: Dima ist der MENSCH/Nutzer. JACK ist das SYSTEM/die KI. Niemals verwechseln.

## Was JACK ueber Dima gelernt hat
- Dima ist Dimitri.
- Dima ist LKW-Fahrer mit Sprinter Kühlkoffer bei Dalhoff Feinkost in Achim (Nachtschicht).
- Dima ist Hobby-Programmierer.
- Dima nutzt Gemini Plus und Claude.ai.
- JACK ist ein autonomes, lokales AI-OS.
- JACK läuft auf einem Honor Magic8 Pro mit Termux.
- JACK nutzt Gemini 2.5 Flash (Lite) als Hauptdenker.
- JACK soll sich selbst lernen und verbessern.
- JACK steht unter Dimas voller Kontrolle.
- JACK verwendet `jack_learn.py` als Lerner.
- JACK nutzt ein Xiaomi 11T Pro als Slave-Gerät via SSH.
- JACK's kostenlose KI-Modelle haben Tageslimits.
- JACK's Chef-KI 'Claude Code' ist ein read-only Berater.
- JACK hat Fähigkeiten wie Text- und Sprachchat, sicheres Code schreiben, autonomes Handeln und Selbstverbesserung.
- JACK nutzt `jack_waechter` für regelbasierte Überwachung und Neustarts.
- JACK's Konfiguration und Logs werden in einem öffentlichen Repo (`jack-context`) geteilt.
- Dima hat KEINEN Hund.
- JACK hat KEINEN direkten Shell- oder Dateizugriff über den Chat.
- JACK's Entwickler Dima hat das Host-Gerät als Honor Magic8 Pro (nicht Honor 8) korrigiert.
- JACK hat Telegram-Commands aktualisiert, committed und gepusht.

## Aktive Module (49)
- jack_agent.py
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
- jack_improve.py
- jack_learn.py
- jack_log.py
- jack_math.py
- jack_memory.py
- jack_memory_engine.py
- jack_memory_maintenance.py
- jack_operator.py
- jack_patch.py
- jack_personality.py
- jack_publish.py
- jack_radar.py
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
- kortex_controller.py
- kortex_memory.py
- kortex_profile_updater.py
- kortex_profiler.py
- kortex_sensor_daemon.py
- quick_bridge.py
- test_jack_approval.py
- voice_service_v2.py

## System-Status
- Offene Fehler: 1
- Erinnerungen: 121
- Dienste:
run: jack_cortex: (pid 21793) 232876s
run: jack_telegram: (pid 28408) 81715s
run: jack_autolearn: (pid 20689) 459380s
run: ollama: (pid 20694) 459380s

## Letzte Aenderungen
6913a0a feat: Circuit Breaker in jack_agent - Abbruch nach 3x gleichem Fehler
e213119 chore: Karpathy-Guidelines in AGENTS.md integriert
6e0e880 feat: voice_poller.sh + record_trigger.sh - Mikrofon-Trigger fuer Xiaomi
7d10661 feat: voice_service_v2 non-blocking funktioniert - Stabilitaets-Check fuer M4A
37f5dec feat: voice_service_v2 Poller-Ansatz - non-blocking Aufnahme funktioniert
2602703 feat: send_webapp + /radar_ergebnisse Telegram-Button
cf8bb21 feat: WebApp-Routen /radar/webapp und /radar/kleinanzeigen
08306dd fix: Xiaomi IP 10.234->10.244 in jack_config.py
9cfeba1 chore: Xiaomi IP auf 10.244.147.131 aktualisiert
9e6b605 feat: /radar_an /radar_aus /vinted_an /vinted_aus /radar_intervall /vinted_intervall
8459198 chore: Config-Dateien mit Tokens aus Git entfernt
859f8bd feat: jack_vinted_radar.py - Vinted Radar live, 96 Items gefunden
592e323 feat: Radar Parser JSON-LD, 20 Treffer live - vorerst deaktiviert
529f84c feat: jack_radar.py - Kleinanzeigen Radar Grundgeruest
c7a1a38 feat: FTS5 Zeitdaempfung - Score sinkt nach 14 Tagen ohne Abruf

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.244.147.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
