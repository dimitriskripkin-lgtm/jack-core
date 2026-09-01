# JACK — Just Autonomous Command Kit

> Ein selbstheilendes KI-System. Gebaut auf zwei Smartphones. Von einem LKW-Fahrer. Mit einem Daumen. Ohne Studium.

[![Branch](https://img.shields.io/badge/branch-master-blue.svg)](https://github.com/dimitriskripkin-lgtm/jack-core)
[![Platform](https://img.shields.io/badge/platform-Android%20%7C%20Termux-green.svg)]()
[![Self-Healing](https://img.shields.io/badge/self--healing-active-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/tests-7%2F7%20passing-brightgreen.svg)]()

---

## Was ist JACK?

JACK ist ein autonomes KI-System das auf zwei Consumer-Smartphones läuft — ohne Cloud-Zwang, ohne Abonnement, ohne Root auf dem Hauptgerät.

Es findet eigene Fehler. Es schreibt eigene Fixes. Es fragt bevor es sie anwendet. Wenn ein Fix das System schlechter macht, rollt es automatisch zurück.

Kein Rechenzentrum. Kein Kubernetes. Zwei Handys, Termux.

---

## Die Geschichte dahinter

Ich bin LKW-Fahrer. Nachtschicht 00-08 Uhr. Danach Programmierzeit.

Ich habe nie Informatik studiert. Keine Ausbildung. Angefangen mit Copy-Paste, einem Daumen auf dem Display, und nicht aufgehört.

JACK ist das Ergebnis von Monaten Nachtschichten, falschen Annahmen und dem sturen Weiterdrücken wenn etwas dreimal nicht funktioniert hat.

Mein Beweis: Man braucht keinen Abschluss um ernsthafte Software zu bauen. Man braucht Konsequenz.

---

## Was JACK kann

- **Selbst-Diagnose** — 7-Punkte Selftest, Score in Prozent, JSON-Snapshot
- **Selbst-Repair** — findet Fehler via Regex + Gemini Code-Review, staged Fixes
- **Auto-Rollback** — Score gesunken nach Fix? Automatisch rückgängig via .fix.bak
- **Graph-Memory** — WAL-SQLite Wissensgraph, Keyword-Guard gegen Halluzinationen
- **Voice + Telegram** — Sprachbefehle, Bot-Interface, /approve_all
- **Dependency-Map** — kennt alle 212 eigenen Module und Abhängigkeiten
- **Autonome Dokumentation** — Gemini schreibt fehlende Docstrings automatisch
- **Mission-System** — Tasks als JSON, priorisiert 0-8, mit Sicherheitsnetz
- **Offline-First** — lokaler Ollama-Fallback wenn kein Internet

---

## Hardware

| Rolle | Gerät | Aufgabe |
|---|---|---|
| HOST | Honor Magic8 Pro | Orchestrierung, 7 runit-Dienste, Telegram |
| SLAVE | Xiaomi 11T Pro (Root) | Ollama, SSH-Ausführung, ADB |

SSH ControlMaster zwischen den Geräten, ~143ms Latenz. Kein Cloud-Relay.

---

## KI-Stack

| Modell | Rolle |
|---|---|
| Gemini 2.5 Flash-Lite | Code-Review, Docstrings, Technik |
| Groq gpt-oss-120b | Persönlichkeit / Chat (TALK-only, kein exec) |
| Ollama llama3.2:3b | Offline-Fallback, lokal auf Xiaomi |
| nomic-embed-text | RAG-Embeddings, Vector-Search |

---

## Autonomer Fix-Zyklus

```
Problem gefunden
      ↓
Fix als staged Datei (shadow/*.staged)
      ↓
Telegram-Digest — eine Nachricht, alle Fixes
      ↓
/approve_all
      ↓
Health-Monitor prüft Score (Selftest)
      ↓
Score OK → Commit + Push
Score gesunken → Auto-Rollback via .fix.bak
```

Kein Mensch muss aktiv debuggen. JACK debuggt sich selbst.

---

## Selftest

```bash
python3 jack_selftest.py
```

```
========================================
JACK SELFTEST — Score: 100% (7/7)
========================================
✓ services         6/6 laufen
✓ xiaomi_ssh       SSH-Port erreichbar
✓ ollama           Gate bereit (off by design)
✓ graph            8 Einträge
✓ heartbeats       4/4 frisch
✓ missions         pending=0 done=2245 fail=11
✓ config           vorhanden
========================================
```

---

## Setup (~10 Minuten auf neuem Gerät)

```bash
git clone https://github.com/dimitriskripkin-lgtm/jack-core.git ~/jack
bash ~/jack/jack_setup.sh
```

---

## Tests

```bash
pytest tests/test_core.py -v
# 7 passed in 0.04s
```

---

## Waechter-Loop (alle ~15 Minuten)

```
Code-Analyse → Semantic Review (Gemini) → Autodoc
→ Dependency-Map → Prioritize → Health-Check → Digest
```

Läuft autonom. Rund um die Uhr. Ohne Eingriff.

---

## Roadmap

- [x] Selbst-Diagnose + Score-System
- [x] Autonomer Fix-Zyklus mit Staged Approval
- [x] Gemini Semantic Code-Review
- [x] Import-Graph 212 Module + Zyklen-Detection
- [x] Auto-Rollback bei Score-Drop
- [x] Zentrales Logging (jack_log.py)
- [x] Automatische Docstrings via Gemini
- [x] Pytest Unit-Tests (7/7)
- [x] Setup-Script neues Gerät
- [ ] Context Caching (Gemini Budget-Optimierung)
- [ ] Schema-Validation für Mission-JSONs
- [ ] USB/OTG Zielgeräte-Support
- [ ] OBD2/ELM327 Integration

---

## Kontakt

**Dimitri** — [github.com/dimitriskripkin-lgtm](https://github.com/dimitriskripkin-lgtm)

LKW-Fahrer. Autodidakt. Baut KI-Systeme auf Smartphones.

> *"Kein Studium. Kein Team. Kein Budget. Nur Zeit, Konsequenz und ein Daumen."*

---

*JACK ist Open Source — weil ich will dass jemand der ähnlich tickt das hier findet und weiß: Es geht.*
