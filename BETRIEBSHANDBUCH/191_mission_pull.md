# 191. jack_mission_pull.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Zweck:** #!/usr/bin/env python3 # JACK_TUNE_BRIDGE import os,json,shutil,subprocess,time

**Nachtrag 26.10.2026 (Claude, K1afix von ChatGPT)**
JACK_TUNE_PULLSAFE: Pull-Allowlist nur lesende Acts (shadow_report/ui_none raus), pull_allowed() verlangt src=git_pull, staged, expect PASS, freigabe False. Abgelehnte Dateien -> missions/fail (PULL_GESPERRT). Achtung: fail nicht leer sperrt halt() und zaehlt fuer queue_gate. Dublettenpfad korrigiert, Symlinks gesperrt. Pull ist weiter AUS (kein .mission_pull_on).
