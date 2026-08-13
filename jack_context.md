# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-08-13T08:01:07.730277

## Owner / Kern
- Owner: Dimitri
- Hardware: Honor Magic8 Pro (Host/Gehirn) + Xiaomi 11T Pro (Slave via SSH)
- Vision: Lokales autonomes AI-OS, offline-first, JACK als Exit-Vehicle fuer mehr Unabhaengigkeit
- WICHTIG: Dima ist der MENSCH/Nutzer. JACK ist das SYSTEM/die KI. Niemals verwechseln.

## Was JACK ueber Dima gelernt hat
- Dima ist Dimitri.
- Dima ist LKW-Fahrer mit Sprinter Kühlkoffer bei Dalhoff Feinkost in Achim (Nachtschicht).
- Dima ist Hobby-Programmierer und Autodidakt.
- Dima hat mit 28 einen Burnout gehabt und sich selbst daraus gezogen (Stoizismus, Jung, Kiyosaki).
- Dima möchte mit JACK Unabhängigkeit und Freiheit aufbauen.
- JACK ist das Exit-Vehicle für Dimas Freiheit und Unabhängigkeit.
- JACK ist ein autonomes, lokales AI-OS auf Dimas Honor Magic8 Pro.
- JACK nutzt Gemini als Denkwerkzeug über API-Calls.
- JACK steht unter Dimas voller Kontrolle.
- JACK kann das Xiaomi 11T Pro per SSH ansprechen.
- Dima hat KEINEN Hund.
- Dima ist KEIN Fernfahrer.
- JACK hat KEINEN direkten Shell- oder Dateizugriff über den Chat.
- Dima hat die Anweisung gegeben, bei bestimmten Fragen länger zu antworten.
- Dima ist jemand, der nach der Nachtschicht im Sprinter lieber noch Code schreibt als schläft.
- Dima hat einen Joint zum Entspannen genehmigt.
- Das Xiaomi ist oft nicht erreichbar.
- Die SSH-Verbindung zum Xiaomi ist häufig instabil.
- JACK verfügt über Fähigkeiten wie Speichermanagement, Sicherheit und Automatisierung.
- Dima hat Dima als Nutzer und JACK als KI-OS identifiziert.

## Aktive Module (85)
- install_litert.py
- jack_agent.py
- jack_android.py
- jack_approval.py
- jack_audit.py
- jack_autonomous.py
- jack_briefing.py
- jack_budget.py
- jack_bug_fixer.py
- jack_bugfix_loop.py
- jack_calltest.py
- jack_chains.py
- jack_claude.py
- jack_code_writer.py
- jack_coder.py
- jack_config.py
- jack_consolidate.py
- jack_cortex.py
- jack_db_queue.py
- jack_episoden.py
- jack_gedanken.py
- jack_gemini_bridge.py
- jack_haliza.py
- jack_handshake_gen.py
- jack_hey.py
- jack_improve.py
- jack_install.py
- jack_intent.py
- jack_learn.py
- jack_log.py
- jack_logging.py
- jack_math.py
- jack_memory.py
- jack_memory_engine.py
- jack_memory_maintenance.py
- jack_memory_tree.py
- jack_missions.py
- jack_monitor.py
- jack_operator.py
- jack_oracle.py
- jack_patch.py
- jack_patch_memory.py
- jack_personality.py
- jack_publish.py
- jack_radar.py
- jack_reflexion.py
- jack_sanity.py
- jack_scout.py
- jack_screen_tracker.py
- jack_self_improve.py
- jack_selftest.py
- jack_sensors.py
- jack_skill_builder.py
- jack_skills.py
- jack_skills_db.py
- jack_snapshot.py
- jack_talk.py
- jack_telegram.py
- jack_thermal.py
- jack_traceback.py
- jack_ui.py
- jack_v2.py
- jack_vecdb.py
- jack_vinted_radar.py
- jack_voice.py
- jack_voice_ab_test.py
- jack_voice_chat_live.py
- jack_voice_live.py
- jack_voice_live_test.py
- jack_voice_ping.py
- jack_voice_processor.py
- jack_voice_router.py
- jack_voice_stability.py
- jack_voraussetzung.py
- jack_write.py
- jack_xiaomi.py
- jack_xiaomi_cmd.py
- kortex_controller.py
- kortex_memory.py
- kortex_profile_updater.py
- kortex_profiler.py
- kortex_sensor_daemon.py
- litert_watchdog.py
- quick_bridge.py
- test_jack_approval.py

## System-Status
- Offene Fehler: 1
- Erinnerungen: 228
- Dienste:
run: jack_cortex: (pid 24878) 74359s
run: jack_telegram: (pid 10235) 23936s
fail: jack_autolearn: unable to change to service directory: file does not exist
run: ollama: (pid 24888) 74359s

## Letzte Aenderungen
65ae2f5 telegram: lange nachrichten aufteilen, episoden nicht abgehackt
f21b5a3 episoden + gedanken + reflexion: momente statt datenpunkte, echte proaktivitaet, sichtbare gedankenkette
654712b gemini: varianz-zwang und anti-report-stil im system-prompt
6cf5abf gemini: varianz-zwang, anti-wiederholung, report-stil verboten
80d15ea adb: aktive app und cpu-last im live-context, apps in identity gespeichert
d0c1deb talk: syntaxwarning fix, antwort-laenge praeferenz in identity
a1ddac0 talk: situationsbewusstsein - akku, laufzeiten, fehler-historie, muster, memory-stats, anti-wiederholung
3bfc28c talk: _live immer via _status_als_text(), keine keyword-bedingung
8670f03 talk: live-status als natuerliche sprache fuer gemini, muster aus intent-db
b90d0a9 gemini: collect_status schnell ohne xiaomi-ssh, ram+temp+dienste lokal
cd3c71e gemini: collect_status ohne xiaomi-ssh fuer schnellen kontext, live-daten klar im prompt
7510d02 logging: alle restlichen blinden excepts geloggt
fc6e8ef logging: blinde excepts in autonomous/publish/handshake/selftest geloggt
acc2585 menue: /bugfix eingetragen | logging: 5 weitere module geloggt
bef1a9d meilenstein: erster autonomer bugfix deployed - bug 2934 jack_cortex

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.244.147.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
