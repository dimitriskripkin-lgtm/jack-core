# JACK (Just Autonomous Command Kit)

> Autonomes KI-Betriebssystem für mobile Edge-Geräte. 100% Offline-First. 0% Cloud-Abhängigkeit im Core.

## 🎯 Executive Summary
JACK ist kein Skript. Es ist ein resilientes, selbstheilendes KI-OS, das ausschließlich auf Android/Termux-Hardware (Honor Magic8 Pro + Xiaomi 11T Pro) läuft. Es beweist Produktionsreife unter extremen Constraints: begrenzter RAM, instabile Netzverbindungen und strikte Mobile-First-Architektur. 

## 🏗 Architektur-Highlights
- **Resilience & Self-Healing**: Circuit Breaker (Gemini 2.5 Flash → lokales Ollama Fallback), Shadow-Execution für autonome Patches, 3x-Fail-Eskalation.
- **Ressourcen-Guard**: Priorisierte Task-Queue. Hintergrundjobs (Prio 3) werden bei `MemAvailable < 800MB` stillgelegt, um OOM-Crashes zu verhindern.
- **Datenpersistenz**: `sqlite-vec` (Vektor-RAG) + FTS5. Strikter WAL-Mode mit `busy_timeout=5000` und automatischem Checkpointing. **Kein ChromaDB** (ARM-Inkompatibilität umgangen).
- **Performance**: SSH ControlMaster optimiert (281ms → 95ms Latenz). RAM-Checks in 0.033ms, Feature-Flags in 0.0016ms.

## 📊 Live System-Status (Stand: August 2026)
| Metrik | Wert | Status |
| :--- | :--- | :--- |
| **System Rating** | **9.3 / 10** | 🟢 Stabil |
| **Master RAM** | ~3.2 GB verfügbar | 🟢 Optimal |
| **Slave (Xiaomi)** | 2.2 GB frei, 93% Akku, 34°C | 🟢 Optimal |
| **SSH Latenz** | 95 ms | 🟢 Optimiert |
| **Circuit Breaker** | Closed (Gemini erreichbar) | 🟢 Aktiv |
| **Autonomie-Loop** | 300s (Cycle, Audit, Explore, AutoFix) | 🟢 Aktiv |

## 🚀 Die Mission: Exit Vehicle
JACK ist das technische Fundament für finanzielle und zeitliche Autarkie. 
1. **Kurzfristig**: System stabilisieren, passives Einkommen generieren.
2. **Mittelfristig**: JACK als Portfolio für CTO-Outreach und Freelance-Architektur-Rollen nutzen.
3. **Langfristig**: Ortsunabhängigkeit. Ein Werkzeug, das überall funktioniert, ohne an einen Desktop-PC gebunden zu sein.

## 👨‍💻 Entwickler
**Dimitri (Dima)** | Autodidaktischer System-Architekt & Mobile Edge Computing Spezialist  
*Entwickelt unter Produktionsbedingungen (Nachtschicht, 100% Mobile-First, Zero-Compromise).*

---
*Branch: `master` | Handshake: v14.1 | GitHub: [dimitriskripkin-lgtm/jack-core](https://github.com/dimitriskripkin-lgtm/jack-core)*
