ROADMAP_GROK_50 - Stand 2026-08-24
Von Claude erstellt, Bedingungen siehe unten.

MARKIERUNG:
MISSION = autonom per Overmind ausfuehrbar
SESSION = braucht Dima + Chat-Session mit Termux-Block, KEIN Autopilot

BLOCK 1 - SOFORT Datenverlust verhindern
1 SESSION Uncommitted Module sichern ui_agent jack_curiosity jack_anomaly jack_nav_learn
2 SESSION Muell-Artefakte =2 und ~/ aus Repo-Root entfernen
3 MISSION git status nach jedem Mission-Batch pruefen
4 SESSION gitignore erweitern heartbeat xiaomi_shot learned_txt

BLOCK 2 - Sicherheit Overmind haerten
5 SESSION allowed_actions Whitelist hart im Code nicht nur JSON
6 SESSION forbidden Liste hardcoded in mission_run.py
7 MISSION Test ohne forbidden Feld - muss fail-closed sein
8 SESSION XAI_API_KEY verifizieren API-Key nicht Chat-Abo
9 SESSION Heat-Skip echten Xiaomi-Temp-Wert testen
10 MISSION auto_fix Skills Quelle finden vor erneutem Loeschen

BLOCK 3 - Stabilitaet
11 SESSION play_sido_youtube_loop Promotion-Bug 0 successes VERIFIED
12 SESSION Einstellungen WLAN Skill PROMOTED bei 0 0 pruefen
13 MISSION Futility-Detector nach Overmind-Umbau aktiv checken
14 SESSION overmind_plan_in.json geloescht - beabsichtigt pruefen
15 MISSION Waechter Heartbeat 120s Akku-Impact nach 24h
16 SESSION circuit_breaker.py Doppelstruktur zu gemini_bridge

BLOCK 4 - Beobachtbarkeit
17 MISSION overmind Telegram Output Lesbarkeit testen
18 SESSION Mission-Steps in missions.db loggen nicht nur JSON
19 SESSION Health-Endpoint bauen Dienste Heartbeat Skills Xiaomi
20 MISSION skills Output nach Bereinigung pruefen

BLOCK 5 - Performance
21 MISSION 180s Throttle zu langsam fuer zeitkritisch pruefen
22 SESSION SSH ControlMaster noch 143ms nach neuen Calls
23 SESSION db_optimizer.py laeuft oder tot

BLOCK 6 - Code-Qualitaet Drift-Check
24 SESSION ui_agent vs jack_exec Ueberschneidung Drift-Regel
25 SESSION ui_elements ui_read vision_once vs vision_selector Redundanz
26 SESSION xiaomi_think xiaomi_web Zweck dokumentieren
27 SESSION read_curl yt_sido archivieren wenn Einmal-Skripte

BLOCK 7 - Mission-System selbst haerten
28 SESSION Timeout-Verhalten Retry-Logik bei haengendem Step
29 SESSION Failed IDs landen in DB fuer Analyse
30 MISSION Zweite Test-Mission mit echtem Nutzen bauen
31 SESSION Teacher-Fallback-Kette dokumentieren
32 SESSION Mission-Prioritaet genutzt oder Deko

BLOCK 8 - ADB Heal
33 MISSION 24h laufen lassen Heal-Haeufigkeit auswerten
34 SESSION Fallback bei unauthorized USB-Debug-Popup bauen

BLOCK 9 - UI-Pipeline
35 SESSION tap_text Erfolgsrate nach einer Woche auswerten
36 SESSION Action-Wort-Whitelist Edge-Cases sammeln

BLOCK 10 - Backlog bekannt offen
37 SESSION takeout_filter.py bauen
38 SESSION FastAPI Webhook auf Xiaomi
39 SESSION Graceful Degradation plus Mission-Pause kombinieren
40 SESSION OBD2 wartet auf Hardware

BLOCK 11 - Dokumentation
41 SESSION MASTER-Dokument um Overmind erweitern
42 MISSION env_now nach jedem Batch neu generieren
43 SESSION diese Roadmap im Repo fuer Overmind-Referenz

BLOCK 12 - Groesser gedacht
44 SESSION Lern-Missionen fuer nachts autonomer Lernloop
45 SESSION Mission-Ergebnisse als RAG in memory.db
46 SESSION Dead Man Switch Overmind still X Stunden Alarm
47 SESSION Multi-Mission-Queue statt eine aktive
48 SESSION LinkedIn-Post posten
49 SESSION LEGACY_ARCHIVE archiv_tot titan_legacy konsolidieren
50 SESSION KI-Exports context_ingest memory.db

BEDINGUNGEN AUTONOME AUSFUEHRUNG
1 Nur MISSION Punkte ohne Dima - SESSION braucht Chat-Session Termux-Block
2 Jede Mission muss forbidden explizit setzen leer heisst Mission laeuft nicht
3 Nach jedem MISSION Batch git status und env_now
4 Grok Teacher nur mit verifiziertem API-Key Punkt 8 zuerst
5 Bei Unsicherheit MISSION oder SESSION - immer SESSION waehlen
