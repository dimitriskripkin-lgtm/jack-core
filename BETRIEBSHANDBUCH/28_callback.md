# 28. jack_callback_handler.py

Gelesen 03.10.2026, erste 55 Zeilen. Kein Umbau.

**Zweck:** Telegram-Inline-Klicks. run_exec liest jack_telegram.PENDING_EXEC, ein Dict im Prozess, keine Datei. cancel_exec leert dasselbe Dict.

**Folge:** Nach Erfolg oder Fehler wird PENDING_EXEC.clear() gerufen. Fehleranalyse ueber jack_react, gekuerzt auf 1500.

**Tatsache:** Deshalb gibt es keine Marker-Datei fuer PENDING_EXEC. Ein Restart loescht den offenen Klick.
