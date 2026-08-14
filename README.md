# JACK — Just Autonomous Command Kit
> Autonomes Edge-KI-Betriebssystem auf Android-Hardware. Offline-first. Keine Cloud. Volle Kontrolle.

## Warum JACK?
Nach dem Crash eines Cloud-VPS am 06.06.2026 ein klares Dogma: **Nie wieder externe Abhängigkeit.**
JACK läuft vollständig auf eigener Hardware — zwei gekoppelte Smartphones als verteiltes Edge-KI-OS.

---

## Hardware-Architektur

| Node | Gerät | Rolle | Specs |
|------|-------|-------|-------|
| **Master** | Honor Magic8 Pro | Gehirn / Host | Snapdragon 8 Elite, 11GB RAM, Termux nativ |
| **Slave** | Xiaomi 11T Pro | Executor / Sensors | Rooted, SSH Port 8022, ControlMaster (95ms) |

---

## Tech-Stack & Multi-LLM Routing

- **Personal Conversations:** Groq llama-3.3-70b-versatile (~500ms Latenz)
- **System Calls / Reasoning / Vision:** Gemini 2.5 Flash
- **Offline Fallback:** Ollama llama3.2:3b (lokal)
- **Memory & RAG:** SQLite WAL + sqlite-vec (nomic-embed-text) + FTS5 Pre-Filter
- **Voice Stack:** ElevenLabs TTS / espeak-ng Fallback + whisper-cli STT
- **Interface:** Telegram Bot (@JackDimaChat_bot) mit Inline-Keyboards
- **Service Management:** runit / termux-services + Termux:Boot Autostart

---

## Resilience & Autonomie

| Feature | Details |
|---------|---------|
| **RAM-Guard** | Lockfile-Mutex vor Whisper/Vision, Schwelle 800MB |
| **Circuit Breaker** | Nach 3x Cloud-Fehler -> sofortiger Fallback auf Ollama |
| **Graceful Degradation** | RAM < 1200MB, Akku < 15% oder Temp > 58°C -> Auto-Downgrade |
| **Shadow-Execution** | Patches erst in Schatten-Kopie testen (py_compile) vor Apply |
| **Dead Mans Switch** | jack_watchdog.sh prüft und heilt abgestürzte Dienste |
| **SSH ControlMaster** | Tunnelswitch von 281ms auf 95ms Latenz gedrückt |

---

## Autonomie-Levelsystem

Level 1: Nur fragen - keine Aktion ohne Bestätigung
Level 2: Lesen erlaubt - Status, Sensoren, Xiaomi lesen
Level 3: Schreiben erlaubt - Dienste neustarten, Xiaomi steuern, Dateien schreiben
Level 4: Vollautonom - handelt selbst im Schatten-Workspace, meldet danach

---

## Live Performance Benchmarks

SSH Latenz (ControlMaster): 95 ms
Groq API Response Time: ~500 ms
State Detection Overhead: 0.0004 ms / Call
RAM Guard Check: 0.033 ms / Call
Feature Flag Evaluation: 0.0016 ms / Call
Memory Vector RAG: Sub-5 ms

---

*GitHub: https://github.com/dimitriskripkin-lgtm/jack-core*
*Owner: Dimitri (Dima) | Built on Termux / Android Edge Devices*
