# 264 Log-Rotation + Onboardings (09.10.2026)

## jack_logrot.py (JACK_TUNE_LOGROT)
- Messung: waechter.log 18 MB (ohne Rotation), logs/jack.log 8 MB, logs/jack_cortex.log 6 MB.
- Stuendlich aus jack_telemetry.loop (nach dem Port-Wachposten). Datei > 5 MB: letzte 1 MB nach <name>.old.log (wird ueberschrieben), Original in-place auf 0 gekuerzt, damit offene Append-Handles der Dienste gueltig bleiben. Eintrag LOGROT in decisions.log. Stempel .logrot_stamp (gitignored).
- Live-Test erzwungen: waechter.log, jack_cortex.log, jack.log rotiert, Waechter laeuft.
- Rotiert NICHT: svlogd-Logs unter ~/logs/<dienst> (rotiert selbst), Missions-Logs (52 MB, Ausduennung noch offen).

## Onboardings
- ARBEITSPLATZ/gemeinsam/onboarding_gemini_20261009.md und onboarding_grok_20261009.md (ersetzen die Uebergaben vom 08.10.). Kopiervorlage fuer neue Sessions der jeweiligen KI.
