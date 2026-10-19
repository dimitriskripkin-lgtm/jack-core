# 38. jack_screen_mapper.py

Gelesen 03.10.2026, erste 36 Zeilen. Kein Umbau.

**Zweck:** UI-Dump vom Xiaomi, Signaturen in jack_screen_states.db.

**Weg:** ssh -G xiaomi-jack fuer Host und Port. Fallback im Code noch 10.229.239.131 und Port 8022. get_foreground ist der Einstieg.

**Offen:** Parser hinter dem Schnitt.

## Nachtrag 19.10.2026 (JACK_TUNE_UIFRESH)
dump_ui loescht /sdcard/ui.xml vor dem Dump, als EIN gequoteter su-Befehl (ssh fuegt Argumente zusammen, ein ; ausserhalb der Quotes laeuft sonst ohne su). Test: Datei mit ALT vorbelegt, dump_ui liefert frische 6467 Byte. Die MIUI-Meldung theme_compatibility.xml FileNotFound ist harmlos. Backup .bak_20261019.
