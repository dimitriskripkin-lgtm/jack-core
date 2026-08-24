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
