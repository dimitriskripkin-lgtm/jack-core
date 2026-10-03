# 38. jack_screen_mapper.py

Gelesen 03.10.2026, erste 36 Zeilen. Kein Umbau.

**Zweck:** UI-Dump vom Xiaomi, Signaturen in jack_screen_states.db.

**Weg:** ssh -G xiaomi-jack fuer Host und Port. Fallback im Code noch 10.229.239.131 und Port 8022. get_foreground ist der Einstieg.

**Offen:** Parser hinter dem Schnitt.
