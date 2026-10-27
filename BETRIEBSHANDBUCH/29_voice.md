# 29. jack_voice_handler.py

Gelesen 03.10.2026, erste 55 Zeilen. Kein Umbau.

**Zweck:** Telegram-Sprachnachricht. get_voice holt die Datei, send_voice schickt Ogg zurueck. handle_voice ist der Einstieg.

**Speicher:** _voice_mem schreibt nach jack_memory, Intent voice_episode, Quelle telegram_voice. cmd 500, result 1500.

**Offen:** Transkription hinter dem Schnitt.

**Nachtrag 27.10.2026:** Transkript geht zuerst an jack_spotify_s1 (JACK_TUNE_SPOTIFY_S1_VOICE), siehe Kap 306.
