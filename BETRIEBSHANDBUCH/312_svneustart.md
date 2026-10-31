# 312 jack_svneustart.py – Dienste sicher neu starten (31.10.2026, JACK_TUNE_SVNEUSTART)

Anlass 31.10.: cloudflared und jack_mcp ignorierten TERM laenger als sv wartet (7 s); sv restart meldete timeout, der alte Prozess lief weiter, Dima musste per kill -9 nachhelfen.
- neustart(dienst, warte_s=45): alte PID merken, sv -w 45 restart, laeuft danach noch DIESELBE PID: sv kill + kill -9 genau dieser PID + sv up. Erfolg (ok=True) nur, wenn danach eine NEUE PID laeuft; sonst ok=False mit Grund.
- Kerndienste jack_missions/jack_mcp verweigert er ohne erlaubt_kern=True (CLI --kern), weil nur Dima die neu startet. Dienstname per Regex geprueft.
- CLI: python3 ~/jack/jack_svneustart.py <dienst> [--kern]. Fuer Dima: bei haengendem jack_mcp: python3 ~/jack/jack_svneustart.py jack_mcp --kern
- Eingebaut in jack_tunnel_watch._restart_cloudflared (Kap 285).
- Tests: 6/6 offline (normal, haengend->kill, kommt nicht hoch, Kerndienst, boeser Name, war down). Live 31.10.: jack_focus_monitor 18380->32717, jack_waechter neu gestartet.
- Offen: Missions-Act sv_restart (jack_mission_runner) nutzt noch plain sv restart; Umstellung braucht Runner-Neustart (Dima).
