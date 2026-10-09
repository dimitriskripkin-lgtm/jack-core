# 251 Dienst-Logs und Log-Prozesse (09.10.2026)

## Befund
jack_autolearn und jack_mcp zeigten "down: log: 1s": im Verzeichnis service/<name>/log fehlte die Datei run (Stempel 06.10. 12:43, Ursache unbekannt). runsv startete den Log-Prozess jede Sekunde neu, die Ausgabe der Dienste hatte keinen Leser (Pipe ohne Reader, kann irgendwann den Dienst beim Schreiben blockieren).

## Fix (04:10, per Runner-Shell)
log/run angelegt (chmod 700): `exec svlogd -tt /data/data/com.termux/files/home/logs/<name>` fuer jack_autolearn und jack_mcp. Logs liegen jetzt in ~/logs/jack_autolearn/current und ~/logs/jack_mcp/current (ausserhalb des Repos). Danach "run: log: pid ..." bei beiden.
Rueckgaengig: Datei log/run loeschen.

## Weiterhin ohne Log-Prozess (kein log-Ordner)
jack_telegram, jack_cortex, jack_waechter, jack_missions, jack_focus_monitor: stdout/stderr gehen ins Leere (Module schreiben teils eigene Logs). Ein log-Ordner wirkt erst nach Neustart von runsv (sv exit) - nur mit Dima-Go, am besten tagsueber.
jack_publisher und cloudflared haben funktionierende Log-Prozesse (Vorbild: log/run mit svlogd).
