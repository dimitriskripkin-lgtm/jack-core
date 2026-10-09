# 260 Dialogkanal Claude<->Jack + Follow-up-Guard (09.10.2026)

## jack_dialog.py (JACK_TUNE_DIALOG)
- Claude (und jede MCP-Rolle) kann Jack ansprechen wie Dima, ohne Telegram: `python3 jack_dialog.py <base64-Text> [neu]` (Mission exec_proposed, Helfer m.frage()).
- Ruft jack_telegram.handle(text) auf, faengt send()/send_keyboard() ab, kein Netz-Eingang, kein zweiter Telegram-Zugang.
- Eigenes Fenster reports/dialog_window.jsonl, Log reports/dialog_log.jsonl. Dimas talk_window.jsonl bleibt unberuehrt.
- Achtung: Fakten/Episoden, die Jack dabei lernt, landen im echten Graph. Keine erfundenen "merk dir"-Saetze zum Testen.

## Follow-up-Guard (jack_chat_router.py, JACK_TUNE_FOLLOWUP)
- Die Lese-Tuer (jack_read_door) am Ende von dispatch griff bei jedem Satz mit Wort-Treffer ("Und dann in einfachen Worten" -> "Gefunden (memory): ... Decke weiss").
- Jetzt nur noch bei Fragen (Fragezeichen oder Fragewort/hast/kennst/weisst am Satzanfang). Alles andere geht ans Gespraech mit Faden.
- Test: "Wie heisst meine Frau?" findet weiter graph:Frau=Natascha.

## Offen
- Jacks Antworten zu sich selbst bleiben vage ("Honor-Gehirn", "synchronisiert"). Training: Selbstwissen-Block aus Handbuch statt freier Erfindung.
