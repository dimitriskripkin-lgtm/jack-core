# 269 ChatGPT Stufe 2b: git_publish (09.10.2026 20:1x, Freigabe Dima)
Grund: H1-H4 und Beweisrunde P1-P6 ohne Verstoss. Dima: 2b jetzt, H5/H6 an echter Arbeit, H7 als laufendes Audit.
## Regel (jack_mcp_auth.py, JACK_TUNE_CHATGPT_S2B, _chatgpt_push_ok)
- git_publish fuer Rolle chatgpt erlaubt. extra braucht msg. dry laeuft immer. Gezaehlt wird nur der Aufruf mit quittung (wie bei sv_restart).
- Push 1 bis 5 nur mit Freigabedatei ~/jack/.chatgpt_push_freigabe (legt Claude nach Diff-Review an, wird beim Push verbraucht). Zaehler ~/jack/.chatgpt_push_n. Ab Push 6 ohne Freigabe, Claude liest Stichproben.
- 2 Minuten Sperre zwischen Pushes. Der Act selbst bleibt: nur master, kein force, Geheimnis-Scan, .git_push_stop sperrt.
- Hinweis: git_publish macht add -A, also auch Aenderungen anderer. Vor Freigabe immer git status pruefen.
## Bedienung (Claude)
Freigabe: touch ~/jack/.chatgpt_push_freigabe. Entziehen: Datei loeschen oder Zaehler/Stop-Datei. Test: reports/t_s2b.py (13 Faelle ok).
## Rueckstufung
Verstoss = zurueck auf 2a: git_publish-Zeilen in check_call entfernen.
