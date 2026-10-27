# 304 Meldestelle: SOFORT / PUFFER / NUR_LOG (26.10.2026)

Gebaut von ChatGPT (Auftrag M/N2, offline), geprueft und eingebaut von Claude, Dima-Go 26.10. 05:39.

**Was:** Jede Meldung ueber jack_tg_send.send (route default) laeuft vor dem Senden durch jack_melderegel.py mit den Regeln in jack_melderegeln.json (17 Regeln, erste passende gewinnt).
- SOFORT: kritisch (Hitze, Dienst tot, Tunnel, Laden/Akku <=15 %, RAM knapp, MCP-Angriff, Heartbeat nicht-Xiaomi). Kritisch = nie Dedupe, nie NUR_LOG.
- PUFFER: Xiaomi weg/wieder da (3 h Dedupe), Akku-Info, Morgenstatus/Briefing (12 h), Radar/Audit. Waehrend der Fahrt in die Fahrt-Queue.
- NUR_LOG: Graceful-Xiaomi, Quota-Warnschwelle, Heartbeat 3x Xiaomi, Wiederholungen im Dedupe-Fenster. Zeile in logs/telegram_nur_log.jsonl, kein Telegram.
- Keine Regel: alte Logik (wichtig=True -> SOFORT, sonst PUFFER). Regeldatei kaputt/fehlt: alte Logik.

**Marker:** JACK_TUNE_MELDEREGELN (jack_tg_send.py). Wrapper autonomous/cortex/monitor/guard/radar akzeptieren Status NUR_LOG ohne Scheinfehler.
**Dedupe-Stempel:** logs/.tg_m2_seen.json, erst nach Telegram-ACK oder Queue-Eintrag (quittiere).
**Claude-Fix beim Einbau:** quelle 'fahrdigest' wird nie neu eingestuft. Gemessen: mit ChatGPTs Original-A1 wurde die Sammelmeldung waehrend TRENNUNG selbst gepuffert (Szenario 10/11, digest GEPUFFERT statt GESENDET), mit Fix 11/11.
**Tests:** M2-Originaltests auf Honor 40/40. Szenario in Temp-Kopie 11/11 (Digest, Hitze/Dienst waehrend Fahrt, Graceful, Xiaomi weg + Wiederholung, Unbekannt wichtig, Telegram-Quelle, Vinted-Route, NUR_LOG-Logdatei kaputt -> Fallback senden). Testgeruest: BUEROS/claude/n2_szen.txt + n2_pairs.json.
**Nicht migriert:** jack_telegram.send/_send_raw, Keyboards, sendVoice, jack_quota, jack_hb_alarm, jack_budget, jack_graceful, Oracle, Vinted (eigener Bot). Die Zentrale ist damit noch nicht vollstaendig.
**Rueckbau:** BUEROS/chatgpt/N2_rueckbau.md; schnell: jack_melderegeln.json ins Attic verschieben -> konfiguration_fehlt -> alte Logik.
**Offen:** Race bei zwei parallelen Prozessen (Dedupe nicht exactly-once), Regeln sind Regex und editierbar: Aenderungen nur mit Test.
