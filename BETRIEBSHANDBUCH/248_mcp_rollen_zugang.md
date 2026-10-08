# 248 MCP-Rollen-Zugang (JACK_TUNE_MCPROLES, 08.10.2026)

Warum: Ein einziger Token fuer alle KIs. Wer ihn hat, kann alles, und im Log sieht man nicht wer. Jetzt ein Token pro Rolle, Rechte pro Rolle, Audit-Log.

Bausteine:
- jack_mcp_auth.py: reine ASGI-Middleware (Auth, Rollen-Check, Audit). Eingehaengt am Ende von jack_mcp_server.py mit try/except: fehlt das Modul oder existiert die Datei ~/jack/.mcp_roles_off, gilt der alte Einzel-Token-Check (Notausschalter).
- Token-Datei ~/jack/.jack_mcp_tokens (Zeilen ROLLE=token, chmod 600, in .gitignore). Der alte Token (.jack_mcp_token) gilt als Rolle 'legacy' mit allen Rechten, bis er entfernt wird.
- Audit: logs/mcp_audit.jsonl (Zeit, Rolle, Tool, Act, ja/NEIN). Keine Inhalte, keine Token.
- Fehlversuche: 10 pro Minute und IP, dann 429.

Rollen:
- claude: alles wie bisher (Gate bleibt).
- nachtlauf: wie claude, aber nicht sv_restart, reload_module, git_publish, file_delete, batch, und keine Acts, die jack_acts/mission_runner/mcp_server/handbuch_gate/kanal/arbeitsplatz/mcp_auth nennen.
- grok, gemini: nur lesende Acts (ro_*, diag, file_exists, compile_ok, sv_ok). ap_* nur mit eigenem wer.

CLI (Termux, Honor): python3 jack_mcp_auth.py rotate|show|list|drop ROLLE. rotate zeigt den Token NICHT an, show nur auf dem Handybildschirm.

Ablauf Rotation: Rollen-Token erzeugen, je Client eintragen, im Audit pruefen dass die Rolle benutzt wird, am Ende 'legacy' entfernen (rm ~/jack/.jack_mcp_token, sv restart jack_mcp).
Notfall: touch ~/jack/.mcp_roles_off und sv restart jack_mcp.
Stand 08.10.2026 abends: Rolle nachtlauf live (Token als Netzwerk-Secret in der Umgebung JACK-Nacht, im Audit bestaetigt). Rollen claude/gemini/grok sind angelegt, aber noch nicht verteilt: der interaktive Claude (Chat, kein Netzwerk-Secret moeglich) nutzt weiter den alten Einzel-Token (Rolle legacy), Gemini/Grok scheitern an Cloudflare 1010 (Browser Integrity Check). Entscheidung Dima: alter Token bleibt, wird von Zeit zu Zeit rotiert (Datei ~/jack/.jack_mcp_token neu setzen, sv restart jack_mcp). jack_qwen_client ruft den MCP ohne Token auf (alle 5 Min 401 im Audit, Snapshot veraltet, kann abgeschaltet werden).
Getestet: lokal 14 Faelle (Rollen, wer-Pruefung, Rate-Limit, Token nicht im Audit), live: Restart ok, Zugriff als 'legacy' im Audit.
