# 253 Selbstmodell: Jack weiss, was sich geaendert hat (09.10.2026)

Anlass: Auf "Was hat sich in den letzten 24 Stunden an dir veraendert?" nannte Jack nur Missionszahlen und Fakten und erfand den Rest (Honor denkt, Xiaomi fuehrt aus).

## Umsetzung (klein, nur lesen)
- Neu: jack_selbstmodell.py, aenderungen(stunden) -> Satz aus `git log --since` (Commit-Betreffs, max 3) und den geaenderten BETRIEBSHANDBUCH/*.md (Kapitelnummern). Timeout 10 s, alles in try/except. Test auf der Honor: "Code/Doku: 17 Commits, zuletzt: ..., Handbuch neu/geaendert: 247 ... 252".
- Eingehaengt in jack_chat_router.neu_report() (Marker JACK_TUNE_SELBSTMODELL), erscheint in der "Letzte N Std"-Antwort. Wirkt erst nach dem naechsten Neustart von jack_telegram (nachts bewusst nicht neu gestartet, sonst Telegram-Meldung "JACK online").
- Rueckgaengig: die 6 Zeilen mit JACK_TUNE_SELBSTMODELL in neu_report entfernen.

## Naechste Ausbaustufen (Ideen)
1. Aktueller Architekturtext aus MODULKARTE.md/ONBOARDING.md als Antwort auf "Wie bist du aufgebaut?" (statt Raten).
2. Dienste-Status und Rollen (jack_mcp_auth) als Teil der Selbstauskunft.
3. Telemetrie-Tagesprofil (sobald genug Daten) als "So laeuft dein Tag".
