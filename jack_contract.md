# JACK Kontrakt (25.08.2026)

## Allein erlaubt (ohne Knopf)
- Messen: fact_report, health, sv status, mtime, classify
- Missionen aus pending mit Acts in ALLOWED
- Logs nach missions/logs schreiben
- Selfsee-Scan / recheck ohne Schreibzugriff

## Nur mit Bestaetigung (Telegram-Knopf / Dima)
- commit_write / Dateien aendern ausserhalb missions/
- SSH/ADB Aktionen auf Xiaomi die etwas verändern
- sv restart (ausser bereits erlaubte Dienst-Heals)
- Overmind-Refresh wenn er haengt und Dima es will
- Git pull/push Missions-Repo (Hahn erst nach Freigabe)

## Verboten
- Platzhalter BEFEHL ausfuehren
- Chrome/UI aus TALK/DIAG-Saetzen (nur eng Allowlist)
- Git-Push jack-core / jack-context
- Autonomie-Level erfinden
- Temp/RAM/Akku ungefragt nennen
- Needle-Patches an jack_telegram.py als Standardweg

## Beweis
Neue Faehigkeit = Act + Mission. FAIL unerwartet stoppt Queue.
Device is the truth.

## Missionen
- expect PASS: ok muss true sein, sonst fail/ und Queue-Stop
- expect FAIL: Treffer/Schuld ist Erfolg -> done/ (raw_ok false, ok true)
- Doppelte ID in done/fail: SKIP-DEDUP, pending wird entfernt
- ALLOWED ist die einzige Act-Liste (roadmap_allowed.json spiegelt sie)

## Heartbeats
- Pfad: /data/data/com.termux/files/home/.heartbeat_jack_<dienst>
- jack_missions schreibt Beat in loop und once
- Frische per mtime_fresh Mission pruefbar

## Seal
Nach jeder Aenderung: python3 /data/data/com.termux/files/home/jack/jack_seal.py
Exit 0 und fail [] = gruen. Seal-IDs werden vor dem Lauf aus done/fail geloescht und neu gemessen.

## Telegram-Reihenfolge (handle)
1. Slash/Datei/SSH/Agent Sonderpfade
2. Chatgate: FACT EXPLAIN DIAG -> dispatch (vor Deep-Nav)
3. Deep-Nav / App-Launch
4. dispatch erneut, sonst talk_to_gemini (+ apply_lane)
Voice: talk_to_gemini -> dispatch zuerst
