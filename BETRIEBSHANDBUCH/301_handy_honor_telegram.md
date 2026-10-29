# 301 Timer und Musik auf dem Honor, per Telegram (22.10.2026)

Warum: Im LKW laeuft Spotify auf dem Honor (BT -> MBUX). jack_handy (Kap 298) wirkte nur auf dem Xiaomi.
Datei ~/jack/jack_handy.py neu (JACK_TUNE_HANDYHONOR, sha ad8f3b26...), alte Fassung in Attic/jack_handy.py_20261022_014717 und *.bak_20261022_honor.
- geraet='honor' ist Standard: Shizuku/rish ueber jack_lagebild._rish (Datei-Ausgabe, rish-stdout verliert Daten). Laeuft in Diensten/Missionen, NICHT in Cron. geraet='xiaomi' wie bisher (root, entsperren).
- Honor-Uhr: com.hihonor.deskclock nimmt SET_TIMER an (HandleSetAlarm, braucht SET_ALARM; Shell hat granted=true, gemessen).
- Honor-Medien-Format: state=PlaybackState {state=PAUSED(2)} statt state=2 (Xiaomi). Parser ordnet Zustand der zuletzt gesehenen package-Zeile zu, ueberspringt com.android.server.*.
- Beleg Timer: neue Uhr-Benachrichtigung (Vorher/Nachher-Vergleich). Lief schon ein Timer, kann der Beleg fehlen -> ehrlich NICHT bestaetigt.
- medien('status') nur lesen. play/pause ok nur bei passendem Zustand, weiter/zurueck ok nur wenn danach etwas spielt.
Telegram (JACK_TUNE_HANDYCMD in jack_telegram.handle vor /lage): /timer 10 [Text] (Minuten), /timer 90s, /timer 1h, /musik pause|play|weiter|zurueck|status; Wort 'xiaomi' im Befehl -> Xiaomi. Aliase stop/an/los/next/skip/naechster.
Tests: 21/21 offline (Parser, beide Zustandsformate, Routing). Live 22.10. 01:47: '/musik status' -> 'spielt (com.spotify.music)'. Timer und Musik-Aktionen live NICHT von Claude getestet (haetten Dimas Musik gestoppt / geklingelt), Test durch Dima per Telegram.
Neustart jack_telegram 01:48, Backup jack_telegram.py.bak_20261022_handy.
Offen: Freitext ohne Slash ('Timer 10 Minuten') noch nicht, erst nach Praxistest. Timer abbrechen weiter nur per UI.

Nachtrag 22.10. 02:01 (v2, sha a036f36d, Backup .bak_20261022_jacktimer):
- Praxistest Dima 01:50-01:51: Honor-Uhr IGNORIERT SET_TIMER-Laenge (oeffnet Timer-Seite 00:00:00, Screenshot). Deshalb Honor-Timer = JACK-Timer (JACK_TUNE_JACKTIMER): eigener Prozess sleep N -> jack_handy.py klingeln -> Telegram wichtig (nie gepuffert) + termux-vibrate + termux-tts-speak. Log logs/handy_timer.jsonl. Ueberlebt Neustart von jack_telegram (neue Sitzung), nicht einen Honor-Neustart.
- Musik: Medientaste geht an die Media button session (gemessen: com.anthropic.claude/TTSPlayback = Claude-Vorlesen). Dann erreicht pause Spotify nicht. Kein Android-Befehl adressiert eine einzelne App. _lage() liest App, Zustand und Tasten-App in einem Aufruf; bei Fehlschlag nennt JACK die Tasten-App. Feste 1,2 s Wartezeit ersetzt durch Pollen 0,3/0,5/0,7 s (JACK_TUNE_HANDYFAST).
- Ziel fuer 100 %%: Tasker auf dem Honor, Media Control direkt an Spotify (Auftrag an ChatGPT).
- Tests 29/29 offline. Neustart jack_telegram 02:01.

Nachtrag 22.10. 02:42: am broadcast ueber rish scheitert auf dem HONOR immer (Failed transaction 2147483646), am start ueber rish geht. am broadcast aus Termux selbst geht. Tasker-Weg deshalb ueber Profil Intent Received (Action jack.honor.MEDIA, Extra cmd), gesendet aus Termux, nicht ACTION_TASK. Auftrag 21b an ChatGPT. Spotify-Bevorzugung (JACK_TUNE_MUSIKAPP) live 02:13, 31/31 Tests.

Nachtrag 22.10. 03:13 (JACK_TUNE_RISHTMP, Backup jack_lagebild.py.bak_20261022_rishtmp): am broadcast/appops ueber rish meldeten Failed transaction, weil der cmd-Dienst nicht direkt in die /sdcard-Datei schreiben darf. _rish schreibt jetzt erst nach /data/local/tmp/<name> (stdin </dev/null), kopiert nach /sdcard/Download/.jack_rish_<pid>.txt und loescht. Gemessen: Broadcast completed result=0, appops liest, Fahrmodus 5/5 stabil. Neustart jack_telegram + jack_waechter 03:13. Damit ist ACTION_TASK an Tasker auch auf dem Honor moeglich.

Nachtrag 29.10.2026 16:46 (Claude, JACK_TUNE_MUSIKVORNE + JACK_TUNE_MUSIKFREI, Backups *.bak_20261029_musikvorne / _musikfrei):
- Fehler: "Mach Spotify play" ging in den TALK-Lane, das Modell antwortete "Spiele jetzt Spotify." ohne Aktion (erfundene Tat).
- Gemessen: Media button session lag bei app.morphe.android.youtube (STOPPED), Spotify PAUSED. Taste ging an YouTube.
- Fix 1 jack_handy.medien: play auf Honor und Tasten-App != Musik-App -> monkey startet Musik-App nach vorn, 1,5 s, input keyevent 126. Live gemessen PAUSED -> PLAYING. Sonst wie bisher cmd media_session dispatch. Beleg bleibt PlaybackState.
- Fix 2 jack_telegram.handle vor HANDYCMD: Freitext "(jack) (mach) (mal) (die) spotify|musik play|an|los|weiter|pause|aus|stop" -> /musik play|pause. "spiel X" (S1) unberuehrt.
- pyflakes sauber, Neustart jack_telegram 16:46. Offen: TALK erfindet weiter Taten (S2 fing "Spiele jetzt" nicht) -> Z1b/S2 nachziehen.
