# 293 Telegram-Chatlog fuer Claude (21.10.2026)

Ziel (Dima): Claude soll den Telegram-Chat selbst lesen, statt dass Dima ihn kopiert. Kein UI-Auslesen noetig: JACK IST der Bot, er sieht jede Nachricht ohnehin.

- jack_telegram.py (JACK_TUNE_CHATLOG, Backup .bak_20261021_chatlog): `_chatlog(von, text)` schreibt nach ~/jack/logs/telegram_chat.jsonl ({ts, von, text[:2000]}).
  - eingehend: Anfang von handle(text), von=dima (auch transkribierte Sprache, soweit sie ueber handle laeuft)
  - ausgehend: Anfang von _send_raw(text), von=jack
- Groesse: ab 2 MB wird nach .1 rotiert (eine Generation).
- Privat: in .gitignore eingetragen (logs/telegram_chat.jsonl, .1), git check-ignore bestaetigt. Nie pushen, nie ungefiltert an Gemini.
- Lesen: `tail -n 40 ~/jack/logs/telegram_chat.jsonl`

## Offen
- 8 weitere Module senden mit eigenem sendMessage (jack_autonomous, jack_briefing, jack_cortex, jack_guard, jack_monitor, jack_oracle, jack_radar, jack_vinted_radar). Deren Meldungen (Waechter, Briefing) fehlen noch im Log. Spaeter: gemeinsamer Sende-Helfer.
