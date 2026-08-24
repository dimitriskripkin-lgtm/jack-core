# JACK SYSTEM STATE — 2026-08-24 14:44

## Services
- jack_cortex: UP
- jack_telegram: UP
- jack_autolearn: UP
- ollama: DOWN

## Resources
- RAM verfuegbar: 3347MB
- Aktives Modell: gemini-2.5-flash
- Memory-Eintraege: 2758
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
2026-08-24 14:42:20 | INFO    | jack.legacy_wrapper  | PUBLISHER-PUSH | OK
2026-08-24 14:42:21 | INFO    | jack.legacy_wrapper  | PUBLISHER-PUSH | OK
2026-08-24 14:42:23 | INFO    | jack.legacy_wrapper  | EXPLORE | Xiaomi: CPU=unbekannt RAM=unbekannt Akku=unbekannt Temp=unbekanntC
2026-08-24 14:42:23 | INFO    | jack.legacy_wrapper  | SHADOW-FIXER | Keine offenen Fehler
2026-08-24 14:42:23 | INFO    | jack.legacy_wrapper  | SHADOW-FIXER | Keine offenen Fehler


*Generiert: 2026-08-24 14:44*
## UI-Pfad Drift-Regel (BLOCK6)
- Produktion: jack_exec.handle_ui_intent + tap_text
- Experiment: ui_agent/ (step_guard, cortex, replay)
- Regel: step_guard in jack_exec verdrahten, ui_agent NICHT weiter aufblasen
- Stand 24.08.: step_guard.py vorhanden, noch NICHT in jack_exec importiert
