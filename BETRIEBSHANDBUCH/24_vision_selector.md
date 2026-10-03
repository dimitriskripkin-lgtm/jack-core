# 24. jack_vision_selector.py

Gelesen 03.10.2026, erste 70 Zeilen. Kein Umbau.

**Zweck:** Text-Tap auf dem Xiaomi. Frischer uiautomator-Dump nach /sdcard/screen.xml, dann cat per SSH.

**Funktionen:** dump_screen, find_element, tap, tap_text. SSH-Alias xiaomi-jack, su. Aufrufer ist jack_exec.tap_text.

**Offen:** Score und Fehlpfad hinter Zeile 70.
