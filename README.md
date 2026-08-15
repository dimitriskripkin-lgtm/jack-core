# JACK — Just Autonomous Command Kit

> Autonomes Edge-KI-Betriebssystem auf Android. Offline-first. Keine Cloud. Volle Kontrolle.

Branch: master | Python + Android + Termux | Groq + Gemini + Ollama

---

## Warum JACK?

Nach dem Crash eines Cloud-VPS am 06.06.2026: Nie wieder externe Abhaengigkeit.
JACK laeuft auf zwei gekoppelten Smartphones - kein Server, keine Cloud, keine monatliche Rechnung.
Wenn das Internet ausfaellt, laeuft JACK weiter.

---

## Hardware-Architektur

    Honor Magic8 Pro (Master)    SSH ControlMaster 95ms    Xiaomi 11T Pro (Slave)
    Snapdragon 8 Elite, 11GB    <--------------------->   Root + Magisk, SSH 8022
    Termux nativ, JACK Gehirn                              Executor + Audio + Root

---

## LLM-Routing

| Trigger | Modell | Latenz |
|---------|--------|--------|
| Persoenliche Gespraeche | Groq llama-3.3-70b | ~500ms |
| System, Vision, Reasoning | Gemini 2.5 Flash | ~1.5s |
| Offline / RAM-kritisch | Ollama llama3.2:3b | ~8s |

Circuit Breaker: Nach 3x Gemini-Fehler sofort Ollama.
Graceful Degradation: Bei RAM<1200MB, Akku<15% oder Temp>58C automatisch Ollama.

---

## Autonomie-Level-System

    Level 1  Nur fragen      Keine Aktion ohne Bestaetigung
    Level 2  Lesen           Status, Sensoren, Xiaomi lesen
    Level 3  Schreiben       Dienste, Xiaomi, Dateien
    Level 4  Vollautonome    Handelt selbst, meldet danach

---

## Resilience-Features

| Feature | Detail |
|---------|--------|
| RAM-Guard | Lockfile-Mutex, Schwelle 800MB MemAvailable |
| Circuit Breaker | Gemini nach 3x Fehler sofort Ollama |
| Graceful Degradation | RAM/Akku/Temp-basiertes Modell-Downgrade |
| Shadow-Execution | Patch auf Kopie testen bevor Original ersetzt |
| Dead Man Switch | Autostart via ~/.termux/boot |
| Exponential Backoff | 1s/2s/4s Retry bei Netzfehlern |
| Saga Cleanup | Temp-Dateien nach Pipeline-Abbruch loeschen |
| Delta Transfer | Nur Aenderungen zwischen Honor und Xiaomi |
| Selbst-Reparatur | Ollama Bug-Fixer mit Shadow-Execution |

---

## Performance (live gemessen 2026-08-15)

    SSH ohne ControlMaster:    281ms
    SSH mit ControlMaster:      95ms  (3x schneller)
    RAM-Guard Check:          0.033ms pro Call
    Feature-Flag:            0.0016ms pro Call
    State-Detection:         0.0004ms pro Call
    Groq Latenz:              ~500ms
    System-Rating:             9.4/10

---

## Waechter-Loop (alle 300s, vollautomatisch)

    1. Dienste pruefen und heilen
    2. explore_next() - Xiaomi CPU/RAM/Akku/Temp live abfragen
    3. jack_autofixer_shadow - Bug-Fixer mit Shadow-Execution
    4. jack_self_audit - SYSTEM_STATE.md generieren
    5. Scheduler - Heavy Jobs nur Power-Time 08-15h

---

## Memory (4 Schichten)

    Core      jack_identity.json   Wer JACK ist
    Recall    SQLite FTS5          Gespraechsverlauf
    Archival  sqlite-vec RAG       250+ Embeddings
    Context   jack_context_ingest  Multi-LLM Exports

---

## Tech-Stack

    Python 3 / Termux nativ
    SQLite WAL + sqlite-vec + FTS5
    Groq / Gemini 2.5 Flash / Ollama llama3.2:3b
    nomic-embed-text (Embeddings)
    whisper-cli (STT offline) + ElevenLabs / espeak-ng (TTS)
    Telegram Bot + Inline-Keyboards
    runit/termux-services

---

## Projektgeschichte

    April 2026     Quest 3 VR Overlay - Meta OS zu restriktiv
    April 2026     Titan auf Netcup VPS
    06.06.2026     VPS-Crash - Eisernes Dogma: NIE WIEDER CLOUD
    Juni 2026      JACK auf Android geboren
    August 2026    Multi-LLM, Groq, Autonomie-Level, Shadow-Execution

---

## Ueber den Entwickler

Autodidaktischer Python-Entwickler. Spezialisierung: Android-Internals, Termux, ADB, Shizuku, Mobile Edge Computing.
Entwickelt ausschliesslich auf dem Smartphone - kein PC.
Ziel: KI-Spezialist fuer direkten Einstieg in KI-Unternehmen oder als Technical Founder.

---

Kein simulated environment. Echter Snapdragon, echtes Android, echte Grenzen.
https://github.com/dimitriskripkin-lgtm/jack-core
