# JACK SYSTEM STATE — 2026-08-24 14:57

## Services
- jack_cortex: UP
- jack_telegram: UP
- jack_autolearn: UP
- ollama: DOWN

## Resources
- RAM verfuegbar: 3384MB
- Aktives Modell: gemini-2.5-flash
- Memory-Eintraege: 2763
- Offene Fehler: 0

## Config
- Xiaomi IP: 10.58.220.131
- SSH Port: 8022

## Features
- elevenlabs: AN
- gemini_vision: AN
- xiaomi_ssh: AN
- voice_pipeline: AN
- autolearn: AN

## Letzte Log-Eintraege
2026-08-24 14:54:53 | INFO    | jack.legacy_wrapper  | SCHEDULER | Power-Time aktiv - schwere Jobs erlaubt
2026-08-24 14:55:24 | INFO    | jack.legacy_wrapper  | EXPLORE | Xiaomi: CPU=unbekannt RAM=unbekannt Akku=unbekannt Temp=unbekanntC
2026-08-24 14:55:24 | INFO    | jack.legacy_wrapper  | SHADOW-FIXER | Keine offenen Fehler
2026-08-24 14:55:24 | INFO    | jack.legacy_wrapper  | SHADOW-FIXER | Keine offenen Fehler
2026-08-24 14:57:28 | INFO    | jack.legacy_wrapper  | PUBLISHER-PUSH | OK


*Generiert: 2026-08-24 14:57*
## 2026-08-24 Abend
- jack_net_discover.py: Xiaomi-IP im Hotspot finden
- jack_deadman.py + boot loop 30min
- jack_mission_queue.py + Telegram /mission next
- jack_graceful.py: Xiaomi offline → Mission pausieren
- adb_heal: Zähler + unauthorized
- step_guard in tap_text aktiv

## Overmind / Mission (Referenz 24.08.2026)

### Komponenten
- jack_overmind_state.py – Lagebild (git, ssh, adb, heartbeats)
- jack_overmind_client.py – Teacher (mock|file|api) → nur ALLOWED_ACTIONS
- ALLOWED: status, ssh_check, adb_heal, sv_status, skills_list
- FORBIDDEN: core_patch, rm_rf, read_secrets, shell, eval, exec
- fail-closed: Mission ohne forbidden-Feld wird nicht ausgeführt
- Heat-Skip ab 65°C Honor; API-Throttle 180s
- jack_mission_run.py – active JSON → plan → client → result + DB
- jack_mission_queue.py – Queue; Telegram /mission next
- jack_graceful.py – Xiaomi offline → Mission pausieren (Wächter ruft auf)
- jack_deadman.py – still >3h → Telegram
- jack_health.py – Snapshot Dienste/SSH/Heartbeats
- jack_net_discover.py – Xiaomi-IP nach Hotspot-Wechsel finden
- jack_adb_heal.py – ADB-TCP reconnect + Zähler

### Telegram
- /overmind – Health + Overmind-Lauf
- /mission next – nächste Queue-Mission aktiv + run
- /skills – Skill-Liste

### UI
- Produktion: jack_exec (handle_ui_intent, tap_text + step_guard)
- ui_agent/ = Experiment (außer step_guard)
