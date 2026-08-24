# JACK — Just Autonomous Command Kit

> **Distributed Bare-Metal Edge AI OS on Android.**
> Zero Cloud. Zero Subscription. Total Infrastructure Sovereignty.

[![Branch](https://img.shields.io/badge/branch-master-blue.svg)](https://github.com/dimitriskripkin-lgtm/jack-core)
[![Platform](https://img.shields.io/badge/platform-Android%20%7C%20Termux-green.svg)]()
[![Architecture](https://img.shields.io/badge/architecture-Host--Worker%20%7C%20De-centralized-orange.svg)]()

---

## Executive Summary

JACK is a distributed AI operating system engineered to run natively on un-emulated Android hardware. Built to overcome the vulnerabilities of cloud dependencies, JACK orchestrates system-level tasks, dynamic UI navigation, and LLM execution directly on two consumer smartphones via a resilient Host-Worker architecture.

> **Status:** Active development on two personal devices (Honor Magic8 Pro + Xiaomi 11T Pro). Built and maintained entirely on a smartphone. Not a simulation, not a lab setup — real hardware, real constraints.

---

## Architecture Overview

```text
+------------------------------------------+          SSH ControlMaster          +------------------------------------------+
|        HONOR MAGIC8 PRO (HOST)           |             (~143ms latency)         |        XIAOMI 11T PRO (WORKER)           |
|  Snapdragon 8 Elite | 11GB RAM | Termux  | <---------------------------------> |   Magisk Root | 8GB RAM | Termux Native  |
+------------------------------------------+                                     +------------------------------------------+
| - Telegram & Voice Orchestrator          |                                     | - Ollama (llama3.2:3b / nomic-embed)     |
| - runit Process Daemon (sv)              |                                     | - Model Context Protocol (MCP) Server    |
| - Intent-Based UI Gateways               |                                     | - uiautomator & Screen Analysis Engine   |
| - Asynchronous SQLite Job Queue          |                                     | - Root Execution / Shell Automation      |
+------------------------------------------+                                     +------------------------------------------+
```

---

## Key Innovations & Technical Highlights

### 1. Process Supervision & Self-Healing (`runit`)
Unlike primitive background scripts, all core services (`jack_telegram`, `jack_cortex`, `jack_waechter`, `jack_autolearn`) are managed via native Termux `runit` daemons (`sv`).
* **Automated Recovery:** Crashed processes are revived in milliseconds without human intervention.
* **Health Watchdogs:** Continuous heartbeat tracking triggers hard service resets if execution loops stall.

### 2. Zero-Shot Intent-Based Navigation
Deprecating fragile X/Y macro coordinates, JACK utilizes a **Zero-Shot UI Architecture**:
* **Direct App Launching:** Bypasses launcher layouts via Android `am start` intents in under 200ms.
* **Semantic XML Pruning:** `uiautomator` dumps are stripped of layout bloat, passing only clickable nodes to LLM reasoning engines.
* **Dynamic Action Translation:** IDs are mapped to bounding boxes on the fly, rendering system navigation completely update-immune.

### 3. Hardened Security & Isolation
* **Operator Whitelist:** Strict execution gating prevents unverified command execution.
* **Approval Sandbox:** Autonomous file operations are constrained to an isolated workspace (`~/jack_werkstatt`).
* **Target Whitelisting:** SSH operations within the autonomous learning loop are locked exclusively to the designated worker node (`xiaomi-jack`).

### 4. Resilient Multi-Tier Memory
* **Core:** In-memory configuration & identity (`jack_identity.json`).
* **Recall:** High-performance conversation history indexed via **SQLite WAL + FTS5**.
* **Archival:** Local RAG vector search powered by `sqlite-vec`.

---

## Tech Stack & Tooling

| Component | Technology / Framework |
| :--- | :--- |
| **Runtime Environment** | Python 3.11+, Termux Native, Android Subsystem |
| **Process Daemon** | `runit` / `termux-services` |
| **Database & Search** | SQLite3 (WAL mode) + `FTS5` + `sqlite-vec` |
| **Worker Protocols** | OpenSSH (ControlMaster multiplexing), MCP (Model Context Protocol) |
| **AI / Speech Infrastructure** | Whisper CLI (Offline STT), Groq API, Gemini Flash, Ollama (Local Fallback) |

---

## Multi-LLM Routing & Circuit Breaker

JACK routes requests dynamically based on system state, battery levels, thermal load, and network availability:

```text
Incoming Task ---> Intent Handler Gate
                        |
                        +---> UI / System Task ---> Direct Android Intent / MCP
                        |
                        +---> Complex Reasoning ---> Primary LLM (Groq / Gemini)
                                                        |
                                             (Circuit Breaker Triggered)
                                                        |
                                                        v
                                              Local Fallback (Ollama 3B)
```

---

## Origin

> On 06.06.2026, a cloud VPS failure wiped a running AI system with no recovery path.
> The lesson was immediate: **never again depend on infrastructure you do not own.**

JACK was engineered from scratch on Android — the only hardware available — as a direct response.
No server. No subscription. No single point of failure outside physical hardware.

---

## Developer & System Author

**Dimitri** — Mobile Edge Computing & Automation Engineer from Bremen, Germany.
* **Specialization:** Android Internals, Termux Subsystems, Shizuku/ADB Automation, Distributed Local AI Infrastructure.
* **Engineering Philosophy:** Built 100% on bare-metal mobile devices. No cloud crutches. Total system ownership.
* **Constraint:** Developed entirely on a smartphone. No PC. No lab. No budget. JACK is proof that edge AI works with consumer hardware.

---

*Repository:* [github.com/dimitriskripkin-lgtm/jack-core](https://github.com/dimitriskripkin-lgtm/jack-core)
