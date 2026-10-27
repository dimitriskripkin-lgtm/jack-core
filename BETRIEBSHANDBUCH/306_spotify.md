# 306 Spotify (Medien M1, 26.10.2026)

**Was:** jack_spotify_oauth.py (PKCE-Anmeldung, Token ~/jack/.spotify_token 600, gitignored) und jack_spotify.py: playlists(), items(id), sortiere(id, titel|kuenstler|album|hinzugefuegt|dauer|zufall, absteigend, bestaetigt=True), zurueck(id, bestaetigt=True), verlauf_holen(). Marker JACK_TUNE_SPOTIFY, _SPOTIFYEXPORT (client_id liest export-Format), _SPOTIFYOPEN (Login oeffnet Browser per termux-open-url).
**Herkunft:** ChatGPT M1 (Tests 10/10 auf Honor), Claude-Fixes beim Einbau. Spotify-Dev-App JACK, Development mode, Redirect http://127.0.0.1:8765/callback, Premium noetig, Refresh-Token 180 Tage.
**Live 26.10. 11:32:** Anmeldung durch Dima, 40 Playlisten lesbar, recently-played liefert 50 Eintraege -> logs/spotify_verlauf.jsonl. Cron 7,37 * * * * sammelt Verlauf (Backup crontab logs/crontab_vor_spotify_20261026.txt).
**Sortieren:** nur eigene/kollaborative Playlisten. Vor jedem Sortieren Sicherung logs/spotify_backup/<id>_<zeit>.json, zurueck() stellt her. Je verschobener Titel ein API-Aufruf.
**Offen:** Telegram-Befehle (M1_telegram_diff, braucht Absender-Pruefung + Bestaetigung), Erinnerung vor Ablauf 180 Tage.

**Nachtrag 27.10.2026 (Claude) JACK_TUNE_SPOTIFYTOP / SPOTIFYPLAY**
- Scopes + user-library-read, user-top-read (Neuanmeldung 26.10. erfolgt).
- jack_spotify_top.py: herz() (537 Herz-Songs), top(zeitraum) je 100, tagessicherung() -> logs/spotify_snapshot/<datum>.json (0600, gitignored), lieblinge_playlist() = Playlist "JACK - Lieblinge nach Hoerdauer": Herz-Songs nach Spotify-Topliste (kurz x2.0 > mittel x1.5 > lang x1.0, bester Rang), Rest nach eigenem Verlauf, dann Datum. Spotify liefert keine Abspielzahlen.
- Cron 15 4 * * * tagessicherung + lieblinge_playlist -> logs/spotify_tag.log. Verlauf bleibt 7,37 * * * * (recently-played nur 50).
- jack_spotify_play.py: spiele(suche) = /search -> termux-open-url <uri>:play -> rish input keyevent 126. LIVE: PlaybackState PLAYING mit richtigem Titel, Dima bestaetigt. Braucht laufendes Shizuku.
- Offen: Telegram-/Sprachbefehl (Auftrag S1 an ChatGPT 27.10.).

**Nachtrag 27.10.2026 04:15 (Claude, S1 von ChatGPT) JACK_TUNE_SPOTIFY_S1**
- Telegram: "spiel X" / "JACK, spiel X" / "/spiel X", /pause, /weiter (sofort); /lieblinge, /sortiere <playlist> <titel|kuenstler|album|hinzugefuegt|dauer|zufall> [ab], /zurueck <playlist> nur mit Knopf-Bestaetigung (Nonce 128 Bit, 10 Min, einmalig, Snapshot+URI-Hash muss gleich sein).
- Nur Dimas Privatchat: chat.id == from.id == CHAT_ID, auch bei Knoepfen. Alte/fremde Knoepfe wirkungslos (live getestet). Freigaben gehen beim Neustart verloren (gewollt).
- jack_spotify_s1_play.py: Sperrliste (jack_app_sperre) + rish-Bereitschaft vor Start; Erfolg nur bei PlaybackState PLAYING(3) im Spotify-Abschnitt von dumpsys media_session, sonst ehrlich "NICHT unabhaengig bestaetigt". Format auf Honor live kalibriert.
- Tests offline 21/21 (18 ChatGPT + 3 Claude). Backup vor Patch: logs/jack_telegram_vor_S1_20261027.py.
- Bekannt: "spiel ..." am Satzanfang geht immer an Spotify. Vorschau fuer /lieblinge und /sortiere laeuft synchron (einige Sekunden).

**Nachtrag 27.10.2026 04:31 (Claude, Feldtest-Fixes)**
- JACK_TUNE_S1PARSE2: "Spiel, X" mit Satzzeichen erkannt; Zusatz "auf dem Honor/am Handy" wird aus der Suche entfernt (Feldtest: "spiel ride or die auf dem honor" fand falschen Song); "auf dem Xiaomi" geht absichtlich an den alten Xiaomi-Weg (jack_ui_type).
- JACK_TUNE_SPOTIFY_S1_VOICE: jack_voice_handler schickt das Transkript zuerst an jack_spotify_s1 (Sprachnachrichten liefen vorher am S1-Weg vorbei in TALK).
- JACK_TUNE_S1LOG: Dimas S1-Befehle stehen jetzt im Chatverlauf.
- Feldtest-Befund offen: TALK behauptete auf "Und jetzt dasselbe auf dem honor" eine nie passierte Aktion (Halluzinationstyp 3). Zwei Spotify-Wege (Honor S1 / Xiaomi jack_ui_type) noch nicht zusammengelegt.
