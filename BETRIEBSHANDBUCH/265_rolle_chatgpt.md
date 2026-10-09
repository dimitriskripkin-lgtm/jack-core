# 265 Rolle chatgpt (09.10.2026)

- Neue MCP-Rolle `chatgpt` (JACK_TUNE_CHATGPT): jack_mcp_auth.py (ROLES, WER_OK, nur lesende Acts wie grok/gemini), jack_arbeitsplatz.py (WER), jack_kanal.py (Meldung). MCP neu gestartet.
- Extra-Sperren nur fuer chatgpt: Tools graph_* und memory_* (persoenliche Fakten) und read_file auf *.db/*.sqlite. Dima kann das spaeter freigeben (CHATGPT_DENY bzw. Zeile in _path_check).
- Alle Rollen: Geheimnis-Dateien gesperrt, wer-Pruefung (keine Fremdrolle), Nicht-Voll-Rollen nur JACK_HOME.
- Test offline (9 Faelle) und Rollenliste live: Rolle hat noch KEINEN Token. Token erzeugt Dima selbst: `python3 ~/jack/jack_mcp_auth.py rotate chatgpt`, anzeigen mit `show chatgpt`. Nie in Chat/Repo.
- Buero ARBEITSPLATZ/BUEROS/chatgpt/ (00_BUERO.md, offen.md, eingang.md) und gemeinsam/einrichtung_chatgpt_20261009.md, onboarding_chatgpt_20261009.md.
- Offen: ChatGPT-Weboberflaeche kennt evtl. nur OAuth/Keine (Quellen widersprechen sich). Bei fehlender Token-Option: nicht den Token in die URL, mit Claude besprechen.
