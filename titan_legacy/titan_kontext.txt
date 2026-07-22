# JACK LIVE-KONTEXT (auto, 2026-07-22T14:26:41.558823)

# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-22T14:26:41.551197

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
- Dima hat auf Xiaomi in Termux sshd eingegeben.
- Dima testet das Gedächtnis.

## Aktive Module (54)
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
- Erinnerungen: 138
- Dienste:
run: jack_cortex: (pid 7336) 100253s
run: jack_telegram: (pid 23523) 19091s
run: jack_autolearn: (pid 7339) 100253s
run: ollama: (pid 7342) 100253s

## Letzte Aenderungen
66d036b titan_legacy: Ordner angelegt, Ingest folgt
a410265 titan_legacy: Ordner vorbereitet fuer Kontext-Ingest
5e7e277 Dima-Profil v1: persoenlicher Kontext fuer JACK und alle KI-Partner
4850d0d Prompt-Fix: JACK kennt jetzt ehrlich seine eigene Architektur (Gemini als Werkzeug)
d1c288e Datum als sprechbarer Text fuer ElevenLabs (kein ISO-Format mehr)
827ef7a Label: Gemini/Lokal/Direkt-Indikator nach jeder Antwort
0d46bc3 voice_processor: whisper-small + robuste Fehlerbehandlung (kein stummer Crash mehr)
aa06f1a Charakter-Patch: JACK redet jetzt wie ein Kumpel, nicht wie ein Helpdesk. Telegram-Limit 3000, whisper-small, memory-save fix
ae39e4f jack_hey: hands-free Sprach-Interaktion (whisper/routen/ElevenLabs), reden + Status-Aktion
c081ad6 chore: runtime files
a7ea6e2 Merge branch 'master' of https://github.com/dimitriskripkin-lgtm/jack-core
3dcb140 fix: /xiaomi handler + telegram fixes
0ed075c feat: Node Alpha Lern-System, Skill-Generator gefixt
340dba9 feat: jack_xiaomi_cmd - Telegram /xiaomi Loop komplett, ADB tap funktioniert
7299e40 feat: jack_node_alpha daemon + ADB tap funktioniert autonom

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.244.147.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.


## Letzte 20 Aktionen (Logbuch)

[2026-07-18 17:06:57] PROFIL-UPDATE | 2 neue Eintraege in kortex_profile.json
[2026-07-19 06:00:00] MEMORY-MAINTENANCE | Gesamt: 33 Eintraege | Stale: 0
[2026-07-19 07:34:58] SELF-IMPROVE | Analyse abgeschlossen, keine Muster gefunden.
[2026-07-19 07:34:58] SELF-IMPROVE | Tagescheck abgeschlossen
[2026-07-19 11:00:00] CONSOLIDATE | Session gespeichert: 10 Logs, 0 Zugriffe
[2026-07-19 19:07:36] PROFIL-UPDATE | 1 neue Eintraege in kortex_profile.json
[2026-07-21 10:35:48] WAECHTER-START | Nacht-Ueberwachung laeuft
[2026-07-21 10:35:57] WAECHTER-AUDIT | woechentlich verschickt
[2026-07-21 10:35:57] SELF-IMPROVE | Analyse abgeschlossen, keine Muster gefunden.
[2026-07-21 10:35:57] SELF-IMPROVE | Tagescheck abgeschlossen
[2026-07-21 11:00:00] CONSOLIDATE | Session gespeichert: 10 Logs, 0 Zugriffe
[2026-07-22 03:55:50] PROFIL-UPDATE | 2 neue Eintraege in kortex_profile.json
[2026-07-22 04:29:53] WAECHTER-START | Nacht-Ueberwachung laeuft
[2026-07-22 04:30:02] WAECHTER-AUDIT | woechentlich verschickt
[2026-07-22 06:00:00] MEMORY-MAINTENANCE | 10 Eintraege als 'stale' markiert | Gesamt: 41 Eintraege | Stale: 10
[2026-07-22 10:01:09] PROFIL-UPDATE | 6 neue Eintraege in kortex_profile.json
[2026-07-22 10:40:42] SELF-IMPROVE | Analyse abgeschlossen, keine Muster gefunden.
[2026-07-22 10:40:42] SELF-IMPROVE | Tagescheck abgeschlossen
[2026-07-22 11:00:00] CONSOLIDATE | Session gespeichert: 10 Logs, 0 Zugriffe
[2026-07-22 12:12:25] PROFIL-UPDATE | 2 neue Eintraege in kortex_profile.json

## Budget heute
Heute: Text 34/300 | Vision 0/40 | Tokens 79169