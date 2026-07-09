# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-09T09:15:47.558149

## Owner / Kern
- Owner: Dimitri
- Hardware: Honor Magic8 Pro (Host/Gehirn) + Xiaomi 11T Pro (Slave via SSH)
- Vision: Lokales autonomes AI-OS, offline-first, JACK als Exit-Vehicle fuer mehr Unabhaengigkeit
- WICHTIG: Dima ist der MENSCH/Nutzer. JACK ist das SYSTEM/die KI. Niemals verwechseln.

## Was JACK ueber Dima gelernt hat
- Dima ist Dimitri, ein Nachtschicht-Fernfahrer und Programmierer.
- Dima arbeitet immer Nachtschicht.
- Dima arbeitet bei Dalhoff Feinkost in Achim, auf dem ehemaligen Tupperware-Gelände bei Heinrich Staas in der Max-Planck-Strasse.
- Dimas Lieblings-LKW ist ein Volvo FH16.
- Dimas Hund heißt Rex und ist ein Schäferhund.
- JACK ist ein autonomes, lokales AI-OS.
- JACK soll sich selbst lernen und verbessern.
- JACK arbeitet komplett offline und ohne Cloud-Abhängigkeit.
- JACK steht unter Dimas voller Kontrolle.
- JACK läuft auf einem Honor Magic8 Pro Android-Smartphone.
- JACK verwendet Termux als Terminal-Emulator.
- JACK beinhaltet das `jack_math.py`-Modul.
- Das `jack_math.py`-Modul ist eine Python-Funktion, die simple mathematische Operationen aus Text erkennt und ausführt.

## Aktive Module (31)
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
- jack_patch.py
- jack_personality.py
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
- Erinnerungen: 52
- Dienste:
run: jack_cortex: (pid 31233) 12739s
run: jack_telegram: (pid 4712) 769s
run: jack_autolearn: (pid 26679) 17607s
run: ollama: (pid 30581) 101759s

## Letzte Aenderungen
7c74bef Bug-Fixer entschaerft: SEARCH/REPLACE statt Ganzdatei-Rewrite, keine 2000-Zeichen-Trunkierung, Groessenwaechter + Volldatei-Syntaxcheck, 4 Haertetests bestanden
8235164 Schreibzugriff: echter Zeitstempel statt Platzhalter, saubere Dateinamen
3454f13 Schreibwunsch-Erkennung in handle() verdrahtet
6678697 JACK hat Haende: sicherer Schreibzugriff via Telegram, Zwei-Schritt-Bestaetigung, nur Werkstatt-Ordner, Ausbruch gehaertet
51e595a Sicherer Schreibzugriff Teil 1: jack_write.py, nur Werkstatt-Ordner, Ausbruch-Schutz getestet
13f36ae Identitaet ehrlich: JACK behauptet keine Ausfuehrungs-Faehigkeit mehr die er nicht hat
2568b42 JACK kennt sich selbst: Live-Systemdaten werden bei Status-Fragen automatisch abgefragt statt aus veraltetem Gedaechtnis geraten
f4aebb0 Voice: whisper auf Deutsch festgenagelt (erkannte faelschlich Englisch), Transkript-Whitespace bereinigt
60d2ea6 Voice: Transkription und Antwort getrennt anzeigen - Debugging bei Fehlerkennung moeglich
cad0724 Voice: doppeltes os.remove entfernt (Ursache fuer Fehler bei Sprachverarbeitung). Gemini kennt jetzt aktuelle Uhrzeit, schwindelt nicht mehr bei Systemdaten
b2200f7 Memory: Source-Tracking + Datum bei Erinnerungen + Anti-Schwindel-Regel gegen veraltete Systemdaten. Voice: WAV-Cleanup
675ac4c Voice: Sprachdateien aus Repo entfernt + gitignore, Cleanup fuer wav-Leichen eingebaut
a585ac4 Voice-Pipeline live: jack_voice_processor.py, Telegram Sprachnachricht rein und raus, whisper 6 threads, elevenlabs convert API
f44f809 Cortex perfekt: SSH-Timeout Rate-Limit, find_xiaomi bombenfest, zero errors verifiziert
fa8fd05 Cortex: find_xiaomi nutzt echten SSH-Login statt Port-Check, config-IP zuerst - stoppt Fehl-Erkennung von .52 + SSH-Fehler Rate-Limit

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.234.166.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
