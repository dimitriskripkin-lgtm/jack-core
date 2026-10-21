# 298 Alltags-Skills Timer und Medien (21.10.2026)

Datei ~/jack/jack_handy.py (JACK_TUNE_HANDY), nach Kap 291 ohne Tasker und ohne UI:
- timer(sekunden, text): entsperrt (jack_xiaomi_unlock), Intent android.intent.action.SET_TIMER mit SKIP_UI. Beleg: Benachrichtigung der Uhr-App "Der Timer stoppt bei HH:MM". Gemessen: 60 s und 10 s gesetzt, Beleg vorhanden.
  - ACHTUNG: DISMISS_TIMER-Intent beendet einen laufenden Timer auf MIUI NICHT (Benachrichtigung blieb "Der Timer laeuft"). Abbrechen bisher nur per UI.
- medien(aktion): play, pause, umschalten, weiter, zurueck per cmd media_session dispatch. Beleg: PlaybackState der aktiven Sitzung. ok nur, wenn der gemessene Zustand passt.
  - Gemessen: ohne aktive Medien-App ehrlich "keine aktive Medien-App". Spotify frisch gestartet: Sitzung da, Zustand 0 (nichts geladen), play wirkt nicht -> ok:false. Erst mit laufender Wiedergabe sinnvoll.
Aufruf: python3 jack_handy.py timer 300 Nudeln | python3 jack_handy.py medien pause
Offen: als Act/Telegram-Befehl verdrahten ("Stell Timer 5 Minuten"), Timer abbrechen per UI-Weg.
