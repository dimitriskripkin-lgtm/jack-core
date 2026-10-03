# 22. jack_gemini_bridge.py

Gelesen 03.10.2026, erste 70 Zeilen. Kein Umbau.

**Zweck:** Gemini-Ruf plus Status sammeln. Schluessel aus der Secrets-Datei, Name GEMINI_API_KEY.

**Funktionen:** load_api_key, collect_status. Circuit-Breaker im RAM: _CB_FAILS, _CB_OPEN. Fehler landen in jack_errors.db.

**Grenze:** Kein Groq-Ersatz in dieser Datei. Aufrufer sind coder und write.

**Offen:** ask_gemini selbst hinter dem Schnitt.
