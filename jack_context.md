# JACK PROJEKT-KONTEXT (auto-generiert)
Stand: 2026-07-09T13:33:32.880787

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
- Dima hat keinen Hund.
- JACK wurde am 18. Juni gebaut.
- JACK hat über den Chat keinen direkten Shell- oder Dateizugriff.

## Aktive Module (33)
- jack_approval.py
- jack_bug_fixer.py
- jack_code_writer.py
- jack_coder.py
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
- jack_sensors.py
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
- Offene Fehler: 1
- Erinnerungen: 76
- Dienste:
run: jack_cortex: (pid 12225) 10573s
run: jack_telegram: (pid 21720) 5656s
run: jack_autolearn: (pid 12226) 10573s
run: ollama: (pid 12229) 10573s

## Letzte Aenderungen
2093dde JACK hat Augen: Xiaomi-Kamera + Gemini Vision live verifiziert, Sensoren laufen
cb94747 Sensoren: Motion-Sensor gegen Haenger gehaertet (timeout+cleanup)
e16299b JACK bekommt Sinne: jack_sensors.py - Xiaomi GPS/Bewegung/Akku + Kamera->Gemini Vision. Telegram /sehen /standort /akku
892be76 Architektur-Bauanleitung: 7 Schichten, Sicherheitsprinzipien, Roadmap
f01ba1a Programmierer bequemer: /run ohne Dateiname nimmt letzten Code, /werkstatt listet Inhalt
e1bba1e JACK als Programmierer: /code schreibt Werkstatt-Code via Gemini, /run fuehrt ihn gesichert aus (Risiko-Gate, Timeout, Werkstatt-only), 6 Haertetests bestanden
429ea3b Gedaechtnis-Korrektur + Aufraeumen: Widerspruchserkennung, fluechtige Daten raus, alte Modelle entfernt
fdbfec8 Gedaechtnis: fluechtige Systemdaten vom Langzeit-Lernen ausgeschlossen
7283bea Gedaechtnis-Korrektur: Lern-Schleife erkennt Widersprueche und Dementis, Dimas Aussage gewinnt, alte falsche Fakten werden ersetzt
e1a1550 Snapshot: Voll-Test bestanden - Gedaechtnis, Live-Status, Ehrlichkeit, Schreibzugriff, Ausbruchschutz, Bug-Fixer sicher
7c74bef Bug-Fixer entschaerft: SEARCH/REPLACE statt Ganzdatei-Rewrite, keine 2000-Zeichen-Trunkierung, Groessenwaechter + Volldatei-Syntaxcheck, 4 Haertetests bestanden
8235164 Schreibzugriff: echter Zeitstempel statt Platzhalter, saubere Dateinamen
3454f13 Schreibwunsch-Erkennung in handle() verdrahtet
6678697 JACK hat Haende: sicherer Schreibzugriff via Telegram, Zwei-Schritt-Bestaetigung, nur Werkstatt-Ordner, Ausbruch gehaertet
51e595a Sicherer Schreibzugriff Teil 1: jack_write.py, nur Werkstatt-Ordner, Ausbruch-Schutz getestet

## Architektur
Host Honor Magic8 Pro (Termux), Slave Xiaomi 11T (SSH 10.234.166.131:8022).
Gehirn: Gemini 2.5 Flash + llama3.2:3b Fallback + nomic-embed-text.
Gedaechtnis 3-Tier (MemGPT-Muster): Core=identity.json, Recall=Verlauf, Archival=sqlite-vec.
Selbstlernen: jack_learn.py alle 2h. Interfaces: Telegram + Voice.
