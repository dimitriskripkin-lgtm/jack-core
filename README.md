# JACK (Just Another Cognitive Kernel)
> **Autonomous Edge AI Operating System for Android/Termux Environment**

---

## 🏛 System Architecture & Node Topology

JACK operates as a distributed cluster over persistent SSH tunnels with automated service supervision via `runit`:

```
+-------------------------------------------------------------------+
| Honor Magic8 Pro (Master Node / Termux / 11GB RAM)                 |
| - Core Engine, Telegram Bridge, State Machine, Priority Queue     |
| - 90+ Modular Python Services & Runit Supervision Daemon          |
| - Storage: SQLite (WAL Mode, busy_timeout=5000) + sqlite-vec      |
+-------------------------------------------------------------------+
                                  |
                      SSH ControlMaster (95ms)
                                  v
+-------------------------------------------------------------------+
| Xiaomi 11T Pro (Slave Node / Termux / IP: 10.58.220.131)          |
| - Execution Engine: Offline Local Ollama (Llama 3.2 3B)           |
| - Background Jobs: Autonomous Exploration & Task Processing       |
+-------------------------------------------------------------------+
```

---

## ⚙ Core Engineering Highlights

### 1. Offline Shadow-Execution AutoFixer (`jack_autofixer_shadow.py`)
Autonomous bug correction without risking live production crashes:
- **Sandbox Isolation**: Unresolved errors in `jack_errors.db` trigger local LLM patches generated in `$PREFIX/tmp`.
- **Verification**: Syntax and integrity are verified via `py_compile` inside the shadow environment.
- **Atomic Rollback**: Source files are replaced only after 100% successful compilation, backed by automatic pre-patch backups.

### 2. RAM-Aware Priority Task Queue (`jack_queue.py`)
To prevent Android LMK process termination, background tasks are dynamically managed based on live memory pressure (`MemAvailable >= 800MB` threshold).
- **Prio 1 (Real-Time)**: Telegram messaging, critical system guards, voice loop.
- **Prio 2 (State & Optimization)**: Sensor polling, WAL checkpoints, DB optimizations.
- **Prio 3 (Background)**: Shadow fixes, autonomous exploration (`explore_next`). Prio 3 tasks are automatically suspended if RAM dips below limit.

### 3. Verified RAG & Ingestion Pipeline (`jack_context_ingest.py`)
- **Sanitizing & Deduplication**: Cleans HTML, normalizes spaces, and filters noise (<80 chars).
- **MD5 Deduplication**: Prevents duplicate insertions into `jack_memory.db` via deterministic hashing.
- **Dual-Stack Resilience**: Primary reasoning via Gemini 2.5 Flash API with local Ollama fallback on 3 consecutive network failures.

---

## 📊 Live Metrics & System Profile

| Metric / Component | Status / Value | Design Note |
| :--- | :--- | :--- |
| **System Codebase** | **90+ Specialized Python Modules** | Modular micro-architecture in `~/jack` |
| **Master Node Memory** | ~3.4 GB Available | Monitored by `jack_guard.py` (0.033ms lookup) |
| **Active Services** | `jack_cortex`, `jack_telegram`, `ollama` | Managed by `runit` supervision |
| **Inter-Node SSH Latency**| **95 ms** | Optimized via SSH ControlMaster sockets |
| **Vector Search & RAG** | Native `sqlite-vec` + FTS5 | Zero Heavy-Framework (No ChromaDB) |

---

## 👨‍💻 Author & Philosophy

Engineered by **Dimitri (Dima)** — Self-Taught Systems Developer & Professional Truck Driver.

> *"JACK was engineered under real-world conditions during night shifts—built entirely on mobile devices without desktop reliance. It proves that resilience, performance, and distributed AI architecture can be achieved on edge hardware with strict engineering constraints."*

---
*Branch: `master` | Repository: [dimitriskripkin-lgtm/jack-core](https://github.com/dimitriskripkin-lgtm/jack-core)*
