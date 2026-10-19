# 224. jack_whitelist_guard.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Zweck:** #!/usr/bin/env python3 # JACK_TUNE_WLGUARD - prueft ob beide ALLOWED-Whitelists 

## Nachtrag 19.10.2026 (F05, JACK_TUNE_WLGUARD2)
Alter Guard fand nach Single-Source-Umbau keine Listen mehr (rc 2). Neu: statische AST-Pruefung, dass jack_acts.ACTS die einzige Quelle ist und Runner + MCP-Server ALLOWED = set(_acts.names()) nutzen. Live OK (64 Acts), Negativtest mit eigener Liste im MCP-Server = FAIL. Nur Verkabelungs-Check, keine Laufzeit-Autorisierung. Backup .bak_20261019. Entwurf ChatGPT, Einbau Claude.
