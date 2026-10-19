# 186. jack_live_bridge.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Zweck:** Bruecke live. Ziel hinter dem Schnitt.

## Nachtrag 19.10.2026 (JACK_TUNE_PULLGATE, Fund ChatGPT)
pull() aus dem Repo jack-missions kopierte JSON-Missionen direkt nach missions/pending, ohne MCP-Rollen, EXTRAGUARD und Handbuch-Gate. Die OK-Liste enthielt ui_none (Geraeteaktion) und shadow_report (schreibt). Nur ruhig, weil halt() bei nicht leerem missions/fail (609 Dateien) abbricht, beim Aufraeumen waere der Pfad scharf geworden. Jetzt gesperrt, Freischalten nur mit ~/jack/.mission_pull_on. push_status laeuft weiter. Runner laedt das Modul pro Poll neu, kein Neustart noetig. Backup .bak_20261019.
