# 17. jack_ui_type.py

Gelesen 03.10.2026, Grok, erste 250 Zeilen. Kein Umbau.

**Zweck:** Xiaomi-UI ueber SSH. Dump, EditText, Tippen, Chrome, Spotify, Maps, YouTube.

**Funktionen:** _ssh, _dump_xml, find_edittext, clear_and_type, chrome_search, _spotify_score_tap, spotify_play, spotify_surprise, maps_nav, youtube_search.

**Freigabe:** Kein Gate in dieser Datei. Aufrufer sind die MCP-Xiaomi-Acts und die Freitext-Regeln in jack_telegram. Dieselben Funktionen, zwei Tueren.

**Offen:** Ob hinter Zeile 250 noch weitere Acts stehen. read_file-Schnitt bei 250.
