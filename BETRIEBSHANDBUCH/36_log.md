# 36. jack_log.py

Gelesen 03.10.2026, erste 40 Zeilen. Kein Umbau.

**Zweck:** Gemeinsamer Logger. get_logger(name). Stufen DEBUG, INFO, WARN, ERROR. Datei jack_main.log, Drehung bei 5 MB.

**Aufrufer:** cortex, graph, bridges. Nicht jeder Schreiber nutzt ihn.
