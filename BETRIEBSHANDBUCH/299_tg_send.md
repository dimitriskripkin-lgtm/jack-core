# 299 Zentraler Telegram-Sende-Helfer, Stufe 1 (21.10.2026)

Gebaut von ChatGPT (Auftrag 20b/20c), Review und Einbau Claude. Tests auf dem Honor: 35/35.
- ~/jack/jack_tg_send.py (JACK_TUNE_TGSEND20B): send(text, wichtig, quelle, route). Liest ~/.jack_secrets im echten Format `export KEY="..."`. Status GESENDET nur nach Telegram-ACK, TEILWEISE/FEHLER ehrlich. Schreibt in logs/telegram_chat.jsonl mit {ts, von, quelle, wichtig, text}. Vinted behaelt eigenen Bot (route='vinted').
- PUFFER_AKTIV = False: unwichtige Meldungen werden NICHT zurueckgehalten (Stufe 2 = Puffer an + 60-s-Takt fuer jack_fahrt_digest.tick, braucht eigenes Go).
- Umgestellt (Backups *.bak_20261021_tgsend): jack_autonomous (Waechter), jack_briefing, jack_cortex, jack_guard, jack_monitor, jack_oracle, jack_radar, jack_vinted_radar, jack_telegram._chatlog (gemeinsamer Lock/Rotation).
- Wichtig=True: Waechter-Warnungen, Akku/Temperatur/RAM kritisch, Dienste tot, Xiaomi 15 min weg, Oracle, Guard-RAM. Wichtig=False: Briefing, Morgengruss, Audit, Skill-Builder, Radar, Vinted, Xiaomi wieder da.
- jack_fahrt_digest.py liegt bereit, ist aber AUS (tick() meldet AUS solange PUFFER_AKTIV False).
- .gitignore: Queue, State, Locks ergaenzt (check-ignore OK).
- Live-Beleg 09:39: Testnachricht ueber den Helfer GESENDET, im Chatlog mit quelle=claude_test. Dienste jack_waechter, jack_cortex, jack_telegram neu gestartet, laufen.

## Stufe 2 LIVE (21.10. 09:50, Dima: Takt alle 5 Min)
- jack_tg_send.PUFFER_AKTIV = True (Backup .bak_20261021_puffer).
- Takt: Thread fahrdigest in jack_autonomous (Waechter), alle 300 s jack_fahrt_digest.tick(), Statuswechsel in jack_log FAHRDIGEST (Backup .bak_20261021_digest). Cron verworfen: rish (Shizuku) laeuft in der Cron-Umgebung nicht (app_process stumm), im runit-Dienst schon.
- Ablauf: LKW-Bluetooth -> FAHRT, Unwichtiges in logs/telegram_fahrt_queue.jsonl. Trennung -> TRENNUNG, nach >=120 s beim naechsten Takt eine Sammelmeldung (nur Anzahlen), Queue quittiert. Verzoegerung nach dem Aussteigen also 5-10 Min.
- Bug gefunden und behoben: tick() nahm now VOR der Messung, Messzeit lag manchmal 1 s danach -> immer UNSICHER. Jetzt Toleranz -5 s (Backup .bak_20261021_zeit). Tests 35/35 auch mit Puffer an.
- Offen: erste echte Fahrt beobachten (jack_log FAHRDIGEST, Queue).

**Nachtrag 26.10.2026 (Claude)**
Meldestelle davor geschaltet: Kap 304 (JACK_TUNE_MELDEREGELN, Klassen SOFORT/PUFFER/NUR_LOG). quelle fahrdigest bleibt ausgenommen.
