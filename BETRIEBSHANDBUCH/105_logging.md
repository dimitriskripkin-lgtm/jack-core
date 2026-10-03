# 105. jack_logging.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Zweck:** Zweites Log-Modul neben jack_log.py. Kopf sagt: Fehler sichtbar machen statt verschlucken.

**Gemessen 03.10. 15:28:** jack_log.py schreibt jack_main.log, rotiert bei 5 MB. jack_logging.py schreibt logs/jack.log. logs/ hat 13 Dateien, darunter jack.log, cortex, publisher, deadman, vinted, voice. Wer wen importiert, nicht gezaehlt. Nicht zusammengelegt.
