# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-13T05:03:00.382793

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
- JACK wurde am 18. Juni gebaut.
- JACK verwendet `jack_learn.py` als Lerner.
- JACK nutzt ein Xiaomi 11T Pro als Slave-Gerät via SSH.
- JACK's kostenlose KI-Modelle haben Tageslimits.
- JACK's Chef-KI 'Claude Code' ist ein read-only Berater.
- JACK hat Fähigkeiten wie Text- und Sprachchat, sicheres Code schreiben, autonomes Handeln und Selbstverbesserung.
- JACK nutzt `jack_waechter` für regelbasierte Überwachung und Neustarts.
- JACK's Konfiguration und Logs werden in einem öffentlichen Repo (`jack-context`) geteilt.
- Dima hat KEINEN Hund.
- JACK hat KEINEN direkten Shell- oder Dateizugriff über den Chat.
- Dima ist LKW-Fahrer mit Sprinter Kuehlkoffer, KEIN Fernfahrer

## Aktive Module (41)
- jack_agent.py
- jack_approval.py
- jack_audit.py
- jack_autonomous.py
- jack_budget.py
- jack_bug_fixer.py
- jack_claude.py
- jack_code_writer.py
- jack_coder.py
- jack_config.py
- jack_cortex.py
- jack_gemini_bridge.py
- jack_handshake_gen.py
- jack_improve.py
- jack_learn.py
- jack_log.py
- jack_math.py
- jack_memory.py
- jack_memory_engine.py
- jack_operator.py
- jack_patch.py
- jack_personality.py
- jack_publish.py
- jack_sensors.py
- jack_skills.py
- jack_snapshot.py
- jack_talk.py
- jack_telegram.py
- jack_v2.py
- jack_vecdb.py
- jack_voice.py
- jack_voice_el.py
- jack_voice_processor.py
- jack_write.py
- jack_xiaomi.py
- kortex_controller.py
- kortex_memory.py
- kortex_profiler.py
- kortex_sensor_daemon.py
- quick_bridge.py
- test_jack_approval.py

## System-Status
- Offene Fehler: 0
- Erinnerungen: 104
- Dienste:
run: jack_cortex: (pid 20695) 186781s
run: jack_telegram: (pid 30438) 159s
run: jack_autolearn: (pid 20689) 186781s
run: ollama: (pid 20694) 186781s

## Letzte Aenderungen
1528de5 fix: letzte Silent Fails geloggt, alle except:pass im Repo eliminiert
8d5848b fix: restliche 4 Silent Fails geloggt (jack_publish/bug_fixer/sensors/gemini)
4e2ae04 fix: Silent Fails ausgeraeumt - alle except:pass loggen jetzt nach jack_decisions.log
dcc487f feat: kortex_bridge runit-Service, Bridge startet automatisch nach Reboot
c883aae feat: /merke /suche /gedaechtnis - Gedaechtnis per Telegram live
e5138fe feat: kortex_profile.json v2.0 - strukturiertes Wissen, Profiler schreibt nur sensoren-Block
94b1dcd fix: Shebang-Position + psutil aus Setup entfernt
7fc9e3c feat: kortex_memory.py - semantisches Gedaechtnis mit FTS5, 3 Flask-Routen live
98e2044 Fix: _sec() Token-Parse auf Bot-Logik angeglichen, notify() funktioniert wieder
a35bb6e jack_audit: Gesundheits+Sicherheits-Check (Dienste/Secrets/Scrubber/Gate); verwaistes jack_health nach LEGACY_ARCHIVE
aebe902 Skill-Gate (Weg 1): assess_skill_risk - subprocess via Whitelist erlaubt, Killer-Muster hart geblockt, /code-Gate unberuehrt
f724f96 ARCHITEKTUR.md: auf Live-Stand - erledigte Baustellen (Keys/SSH/Log/Augen/Selbstverbesserung) raus, neue Schichten+Befehle rein, ehrliche OFFEN-Liste
b55f1d6 CLAUDE.md: auf Live-Stand konsolidiert - jack_waechter->jack_autonomous Mapping, alle 6 Dienste, DB-Schemas, erledigte Baustellen raus
60a9c28 Fix: jack_taskrunner-Gespenst entfernt (nie gebaut), Waechter + CLAUDE.md sauber. Notiz: Xiaomi-Status pushen + Claude-Schreibrechte Xiaomi = spaeter
3641e51 taskrunner neu gestartet, Waechter-Baseline frisch

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.234.166.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
