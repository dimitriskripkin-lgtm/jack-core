# 42. jack_chains.py

Gelesen 03.10.2026, erste 32 Zeilen. Kein Umbau.

**Zweck:** Feste Ketten in jack_chains.db. xiaomi_reparieren braucht Level 3: ssh_check, bei nicht erreichbar wecken, nochmal ssh_check. system_vollcheck sammelt Dienste, RAM, Temp, Akku.

**Offen:** Ausfuehrung hinter dem Schnitt.

## Nachtrag 19.10.2026 (Doppelte Funktion)
Erste, ueberschriebene Definition von chain_oauth_final entfernt (77 Zeilen). AST-Pruefung: gleiche Funktionsmenge, letzte Definition byte-gleich im AST. Kein Aufrufer im Code. Backup .bak_20261019. jack_skill_builder.speichere_skill bleibt doppelt: die erste wird beim Skriptstart vor der zweiten benutzt (Fund ChatGPT).
