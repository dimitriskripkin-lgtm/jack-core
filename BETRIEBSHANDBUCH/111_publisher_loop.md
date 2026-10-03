# 111. Publisher-Loop

Gelesen 03.10.2026, ganze Datei 16 Zeilen. Kein Umbau.

**Zweck:** alle 180 Sekunden jack_publish.push(), dann Heartbeat jack_publisher. Fehler nur print.

**Grenze:** Ob der Waechter zusaetzlich einen Publisher-Thread hat, hinter Zeile 95 nicht gelesen.
