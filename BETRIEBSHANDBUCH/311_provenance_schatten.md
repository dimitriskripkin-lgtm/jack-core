# 311 Provenance-Schattenmodus (W4, 31.10.2026, JACK_TUNE_PROVENANCE_SHADOW)

Entwurf ChatGPT (runde8_provenance_schatten_teil1/2 + helper + test), Review/Einbau Claude.
- jack_mcp_auth.RoleMiddleware setzt die authentifizierte Rolle in eine ContextVar (_MCP_AUTH_ROLE, reset im finally). request_role() liest sie.
- jack_mcp_server.create_mission: "_provenance" ist in extra reserviert (Client darf es nicht setzen). Nach mission.update haengt jack_provenance_shadow.attach() einen HMAC-SHA256-Umschlag an (v, issuer jack-mcp, aud jack-mission-runner, kid shadow-20261029, role, issued_at, nonce, payload_sha256 ueber die ganze Mission ohne _provenance, sig). Fehler -> Mission unveraendert.
- jack_mission_runner.one(): nach load() prueft shadow_check_path() eine separate strikte Lesekopie (Doppelkeys, NaN) und schreibt NUR ein Audit. run_act, rec.ok, Dedup, Freigaben unveraendert.
- Codes: SHADOW_OK, LEGACY_UNSIGNED (Telegram/Git/Cron, erwartet), KEY_UNAVAILABLE, ROLE_CONTEXT_MISSING, BAD_SIG, BAD_PAYLOAD_HASH, UNKNOWN_KID, WRONG_AUDIENCE, BAD_META, CLOCK_SKEW (>1h alt / >2min Zukunft), UNSUPPORTED_TYPE, CHECK_EXCEPTION.
- Audit: logs/provenance_shadow.jsonl (0600, nur ts/code/id/act/role/kid, stoppt bei 5 MB). Schluessel: ~/.jack_provenance_shadow.key (32 Zufallsbytes, 0600, AUSSERHALB des Repos, nie ausgeben, nicht der MCP-Bearer).
- Tests Honor 31.10.: Helper-Suite 16/16, alle 5 OLD-Hunks genau 1x und Hashes = ChatGPT-Diff, Stichprobe attach/verify SHADOW_OK, Manipulation act -> BAD_PAYLOAD_HASH. Backups *.bak_20261031_w4.
- Wirksam erst nach Neustart jack_missions + jack_mcp (nur Dima).
- Grenzen: nur Beobachtung, kein Gate. Keine Replay-Sperre (Nonce wird nur protokolliert). Gleiche Android-UID = keine echte Prozessisolation. Loest I04 (freier Shellpfad) NICHT. ContextVar-Weitergabe ASGI -> synchrones Tool live noch unbewiesen: falls ROLE_CONTEXT_MISSING im Audit, Rollenweitergabe nachbessern, nie Rolle raten.
- Vor scharfem Modus: alle Autoren erfassen, Batch/Approval-Kinder, persistentes Nonce-Journal, I04-Verengung.

Livebeleg 31.10.2026 17:41: Neustart jack_missions 17:38, jack_mcp 17:41 (alter Prozess ignorierte TERM, sv kill + kill -9 noetig). Erste MCP-Mission m_exec_proposed_20261031_174133: MCP attach SHADOW_OK role=claude, Runner verify SHADOW_OK. ContextVar-Weitergabe damit live belegt.
