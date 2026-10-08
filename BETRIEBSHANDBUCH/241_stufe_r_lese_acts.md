# 241 Stufe R: feste Lese-Acts (08.10.2026, Dima: "Go r")
Ziel: Claude (und andere KIs) sehen selbst nach, ohne dass Dima Terminal-Output einfuegt. Kein freies exec. Marker JACK_TUNE_RO (jack_mission_runner.py, Acts in jack_acts.py).
## Acts (nur lesen, feste Befehle)
- ro_log_tail(service, n<=150): Log-Ende eines Dienstes (jack_* oder cloudflared). Suchpfade: usr/var/log/sv/<dienst>/current, ~/logs/<dienst>/current u.a. Logs gefunden fuer: cloudflared, jack_publisher, jack_cortex (logs/jack_cortex.log), jack_waechter/telegram/autolearn (~/jack/<name>.log). Ohne Log: jack_missions, jack_focus_monitor.
- ro_git: Branch, geaenderte/neue Dateien (max 40), letzte 5 Commits.
- ro_scan: Geheimnis-Scan ueber neue/geaenderte Dateien (git ls-files -o -m --exclude-standard), gibt NUR Dateinamen aus; ok=false bei Treffer. Muster im Quelltext sind geteilt, damit der Scan sich nicht selbst trifft.
- ro_pyflakes(file): nur ~/jack/<name>.py, Name per Regex begrenzt.
- ro_ps: gefilterte Prozessliste (jack|ssh|ollama|cloudflared|runsv|python), max 30 Zeilen.
## Schutz
Alle Ausgaben laufen durch _scrub (Token/Key-Muster -> [GEHEIM]) und sind gekuerzt. Dienstnamen und Dateinamen nur per Regex. Jeder Aufruf steht in ARBEITSPLATZ/gemeinsam/ro_audit.jsonl (ts, act, Args, ok) - fuer alle KIs lesbar, nicht im Git.
## Bewusst nicht enthalten
Kein Lesen von config.ini/.ssh/Token, kein Schreiben, kein Push/Commit (Stufe S, braucht Dima-Freigabe), keine Shell. Pro-KI-Token und Token-Rotation stehen weiter aus (nur Dima).
## Getestet (live, 08.10.)
ro_git, ro_scan (nach Fix sauber), ro_ps, ro_pyflakes(jack_kanal.py sauber), ro_log_tail cloudflared ok, ungueltiger Dienstname '../etc/passwd' abgelehnt.
