# 234. jack_arbeitsplatz.py

Angelegt 07.10.2026 (Marker JACK_TUNE_ARBEITSPLATZ).

**Zweck:** Gemeinsamer Arbeitsplatz für alle KIs: ein Ordner ARBEITSPLATZ/ auf der Honor mit gemeinsamen Daten und je einem Büro für Claude und Grok (gleiche Daten, getrennte Notizen).

**Struktur:** ARBEITSPLATZ/gemeinsam/ (00_LIES_MICH, roadmap, entscheidungen, bugs, archiv/, audit.jsonl) und ARBEITSPLATZ/BUEROS/<claude|grok|gemini|dima>/ (00_BUERO, offen, notizen, eingang, journal.jsonl).

**MCP-Tools (jack_mcp_server.py):** `start_hier(wer="")` hängt die Büro-Zusammenfassung an, `buero(wer)`, `ap_notiz(wer, pfad, text, modus)`, `ap_journal(wer, text)`.

**Regeln:** Eigenes Büro frei beschreibbar. Fremdes Büro nur anhängen an eingang.md. In gemeinsam/ sind entscheidungen* und 00_* nur anhängbar. Ersetzen legt Backup in gemeinsam/archiv/ an. Nur md/jsonl/json/txt, max 200000 Byte Datei, 8000 Zeichen pro Aufruf. Jede Aktion landet in audit.jsonl. Keine Geheimnisse.

**Test-Umgebung:** Env JACK_HB_HOME überschreibt das Basisverzeichnis.
