# 266 OAuth-Anbindung fuer ChatGPT (Rolle chatgpt)
Stand 09.10.2026. Modul: `jack_mcp_oauth.py` (JACK_TUNE_OAUTH). Rollenrechte unveraendert (nur lesen, Secrets/DBs gesperrt).

## Warum
ChatGPT-Connectoren verlangen OAuth (Authorization Code + PKCE), ein statischer Bearer-Token geht dort nicht. Die statischen Rollen-Tokens (claude, gemini, grok, nachtlauf, legacy) bleiben wie sie sind.

## Aufbau
- Routen (ueber MCP-SDK 2.2.0): `/.well-known/oauth-authorization-server`, `/.well-known/oauth-protected-resource/mcp`, `/register` (DCR), `/authorize`, `/token`, `/oauth/consent`. `/revoke` ist aus (SDK verlangt client_secret).
- Eingehaengt in `jack_mcp_server.py` direkt nach `streamable_http_app`; `RoleMiddleware` laesst nur diese Pfade ohne Bearer durch (`is_public`), `role_for` kennt OAuth-Access-Tokens als Rolle chatgpt, 401 traegt `WWW-Authenticate` mit resource_metadata.
- Nur PKCE S256. Redirect-URIs nur https auf chatgpt.com / chat.openai.com / platform.openai.com, exakt gespeichert. Max 5 Clients, DCR 10/h, Authorize 6/h.
- Freigabe nie anonym: `/authorize` schickt per Telegram eine 6-stellige PIN an Dima (10 Min, 3 Versuche). Ohne Telegram-Zustellung wird abgelehnt (fail-closed). Die PIN gibt man auf `/oauth/consent` ein.
- Code 5 Min und einmalig. Access-Token 1 h, Refresh 30 Tage mit Rotation. Alles nur als SHA-256 in `.jack_oauth.json` (chmod 600).

## Bedienung (HONOR, Termux)
- Status: `python3 ~/jack/jack_mcp_oauth.py list`
- Alle OAuth-Tokens widerrufen: `python3 ~/jack/jack_mcp_oauth.py drop` (mit `alles` auch Clients)
- Notaus: Datei `~/jack/.oauth_off` anlegen. Sofort: Routen 401, Tokens tot. Wieder an: Datei weg (Routen brauchen nach Notaus beim Start MCP-Neustart, wenn die Datei schon beim Start da war).

## Getestet
Sandbox 24/24 (falscher Redirect, http-Redirect, falsche PIN, 3-Fehler-Sperre, falscher Verifier, Code-Wiederverwendung, Refresh-Rotation, Dateirechte, kein Klartext-Token, drop, Notaus). Live: ohne Token 401+Metadaten, evil-Redirect 400, uebrige Pfade 401.

## Fehler 09.10. 18:19 (behoben)
ChatGPT registriert sich mit client_secret_post. Erste Version loeschte beim Registrieren das Client-Secret, der Token-Tausch scheiterte mit invalid_client (kein gespeichertes Secret). Fix: Secret bleibt gespeichert (Datei chmod 600, gitignore). Test vorher nur mit auth_method none, jetzt Fall client_secret_post abgedeckt. Der Server loggt keine Zugriffe (uvicorn log_level warning), Diagnose lief ueber Audit-Log + Nachstellen in der Sandbox.

## Offen
Echter Durchlauf mit ChatGPT steht aus (Dimas Test). Issuer-URL hat Schrägstrich am Ende (SDK-Normalisierung), falls ChatGPT mault. Auth-Rate-Limit pro IP fehlt (global genuegt vorerst).
