# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-09T04:51:09.389230

## Owner / Kern
- Owner: Dimitri
- Hardware: Honor Magic8 Pro (Host/Gehirn) + Xiaomi 11T Pro (Slave via SSH)
- Vision: Lokales autonomes AI-OS, offline-first, JACK als Exit-Vehicle fuer mehr Unabhaengigkeit
- WICHTIG: Dima ist der MENSCH/Nutzer. JACK ist das SYSTEM/die KI. Niemals verwechseln.

## Was JACK ueber Dima gelernt hat
- Dima ist Dimitri, ein Nachtschicht-Fernfahrer und Programmierer.
- Dima ist Nachtschichtfahrer bei Dalhoff Feinkost in Achim.
- Dima arbeitet auf dem ehemaligen Tupperware-Gelände bei Heinrich Staas in der Max-Planck-Strasse.
- Dima arbeitet immer Nachtschicht.
- Dima programmiert nebenbei.
- Dimas Lieblings-LKW ist ein Volvo FH16.
- JACK ist ein autonomes, lokales AI-OS.
- JACK soll ein sich selbst lernendes und verbesserndes System werden.
- JACK arbeitet komplett offline und ohne Cloud-Abhängigkeit.
- JACK steht unter Dimas voller Kontrolle.
- JACK läuft auf einem Honor Magic8 Pro Android-Smartphone.
- JACK verwendet Termux als Terminal-Emulator.
- JACK beinhaltet ein `jack_math.py`-Modul.
- Das `jack_math.py`-Modul ist eine Python-Funktion.
- Das `jack_math.py`-Modul erkennt und führt simple mathematische Operationen aus Text aus.

## Aktive Module (28)
- jack_approval.py
- jack_bug_fixer.py
- jack_code_writer.py
- jack_config.py
- jack_cortex.py
- jack_gemini_bridge.py
- jack_handshake_gen.py
- jack_health.py
- jack_learn.py
- jack_learning_loop.py
- jack_math.py
- jack_memory.py
- jack_memory_engine.py
- jack_operator.py
- jack_personality.py
- jack_snapshot.py
- jack_talk.py
- jack_telegram.py
- jack_v2.py
- jack_vecdb.py
- jack_voice.py
- jack_voice_el.py
- jack_xiaomi.py
- kortex_controller.py
- kortex_profiler.py
- kortex_sensor_daemon.py
- quick_bridge.py
- test_jack_approval.py

## System-Status
- Offene Fehler: 642
- Erinnerungen: 33
- Dienste:
run: jack_cortex: (pid 29754) 78433s
run: jack_telegram: (pid 26433) 1742s
run: jack_autolearn: (pid 26679) 1729s
run: ollama: (pid 30581) 85881s

## Letzte Aenderungen
f47891b identity: device_host Name korrigiert
8034be2 Auto-learning: Telegram speichert Gespraeche, jack_learn dedupliziert via Gemini, autolearn-Dienst alle 2h
efe20e2 Self-learning live: neue Fakten (Job/Ort) via Lernschleife ins Core-Memory, Honor8-String gefixt
8b48565 Core-Memory: identity.json als Grundwahrheit mit Vorrang, Telegram nutzt jetzt Gedaechtnis-Denker
36edfad Talk-Loop: Gemini als Denker mit RAG-Erinnerungen + Gespraechsverlauf als Kontext, Ollama-Fallback
6d855da Memory: sharpen retrieval prompt (model-side limitation bleibt, 3B zu schwach fuer Kontext-Anerkennung)
6df5f72 Memory FIX komplett: integer-rowid storage + search_mem retrieval im talk-loop, alle memories re-embedded
2f9c710 Security: disable /shell until auth, retire learning loop service
acf5baa gitignore: learning loop runtime files
2ac1d09 gitignore: learning loop runtime files
1476f1e gitignore: add learning loop runtime files
0dfd466 Telegram: fix parse_mode Markdown crash
ecb3f12 Add Telegram bot: status/errors/shell/Gemini bridge via @JackDimaChat_bot
bab1b48 Add autonomous learning loop: Gemini API → embed → auto-fix with heartbeat
74ca498 Operator: remove last ADB/TITAN remnants, fix DB reference

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.234.166.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
