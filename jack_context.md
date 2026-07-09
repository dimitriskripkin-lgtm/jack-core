# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-09T21:35:15.141909

## Owner / Kern
- Owner: Dimitri
- Hardware: Honor Magic8 Pro (Host/Gehirn) + Xiaomi 11T Pro (Slave via SSH)
- Vision: Lokales autonomes AI-OS, offline-first, JACK als Exit-Vehicle fuer mehr Unabhaengigkeit
- WICHTIG: Dima ist der MENSCH/Nutzer. JACK ist das SYSTEM/die KI. Niemals verwechseln.

## Was JACK ueber Dima gelernt hat
- Dima ist Dimitri, ein Nachtschicht-LKW-Fahrer und Programmierer.
- Dima arbeitet immer Nachtschicht.
- Dima arbeitet bei Dalhoff Feinkost in Achim, auf dem ehemaligen Tupperware-Gelände bei Heinrich Staas in der Max-Planck-Strasse.
- Dima fährt einen Sprinter (Kühlkoffer) bei Dalhoff Feinkost.
- Dimas Lieblings-LKW ist ein Volvo FH16.
- Dima baute zuvor Titan, den Vorgänger von JACK.
- Titan, der Vorgänger von JACK, konnte bereits per Sprachnachricht kommunizieren.
- JACK ist ein autonomes, lokales AI-OS.
- JACKs Ziel ist komplett offline und ohne Cloud-Abhängigkeit, verwendet aber aktuell Gemini 2.5 Flash als Haupt-Denker.
- JACK soll sich selbst lernen und verbessern.
- JACK steht unter Dimas voller Kontrolle.
- JACK läuft auf einem Honor Magic8 Pro Android-Smartphone.
- JACK verwendet Termux als Terminal-Emulator.
- JACK beinhaltet das `jack_math.py`-Modul.
- Das `jack_math.py`-Modul ist eine Python-Funktion, die simple mathematische Operationen aus Text erkennt und ausführt.
- JACK wurde am 18. Juni gebaut.
- JACK hat über den Chat keinen direkten Shell- oder Dateizugriff.

## Aktive Module (40)
- jack_agent.py
- jack_approval.py
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
- jack_health.py
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
- kortex_profiler.py
- kortex_sensor_daemon.py
- quick_bridge.py
- test_jack_approval.py

## System-Status
- Offene Fehler: 0
- Erinnerungen: 92
- Dienste:
run: jack_cortex: (pid 11922) 24700s
run: jack_telegram: (pid 23044) 836s
run: jack_autolearn: (pid 12394) 2875s
run: ollama: (pid 12229) 39476s

## Letzte Aenderungen
3641e51 taskrunner neu gestartet, Waechter-Baseline frisch
c088322 Nacht-Waechter: regelbasierte Selbstueberwachung, meldet nur echte Probleme per Telegram, restartet tote Dienste, erster Lauf nur Baseline (weckt nicht)
60f557c Aufraeumen: jack_learning_loop.py + Backups stillgelegt, CLAUDE.md mit echter Dienstliste - verhindert dass Claude Code aus toten Dateien liest
61694b6 Claude Code Bruecke: /cc im Telegram (Text) + Sprach-Routing (Voice startet mit 'claude'). Read-only Berater kennt die ganze Umgebung, laeuft ueber Abo
ff4ac38 CLAUDE.md Wissensbasis + Publisher pusht ganze Umgebung (Werkstatt/Skills/Logs)
b56a851 Memory: absolute Korrekturen (kein Hund/LKW-Fahrer) verankert, Publish-Scrub praeziser
a98e082 Rate-Limit-Fix: Modellwechsel auf freies Gemini-Modell, Token-Zaehler eingebaut, Agent-Kaskaden-Bug behoben (Fehlermeldung nicht mehr als Code), Runden-Pause
2cc5b3f Gemini-Bridge: Retry+Backoff gegen HTTP 429 (Rate-Limit) - Agent + Chat laufen jetzt drosselfest
58360e2 Autonomer Agent: /auto <ziel> - JACK loest Ziele selbststaendig in der Werkstatt (schreibt+testet+verbessert, max 4 Runden), im Hintergrund-Thread, harte Sandbox-Waende bleiben
b683f1f Skill-Bibliothek: erfolgreiche Code-Bausteine speichern (/skill save) + kostenlos wiederverwenden (/skill <name>) - senkt API-Kosten, macht JACK unabhaengiger
77a3333 Kosten-Bremse: Tageslimits Gemini Text(300)+Vision(40), /budget-Befehl - schuetzt vor Kosten-Explosion bei Bild-/Sensordaten
14fb2a3 Entscheidungs-Logbuch: jede JACK-Aktion nachvollziehbar (jack_log), /log in Telegram - Grundstein fuer sichere Autonomie
b372e98 Selbstverbesserung jack_math.py (JACK-Vorschlag, Dima-Freigabe)
6768994 Fix: doppelte tote GEMINI-Key-Zeile entfernt (401-Ursache), Bot-Loop + propose_improvement gegen Absturz/Crashloop abgesichert
6d9284d Selbstverbesserungs-Kreis: /verbessere <modul> -> Gemini-Patch-Vorschlag -> Freigabe -> Patch mit Auto-Rollback + Commit. Sicherheitsnetze doppelt getestet

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.234.166.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
