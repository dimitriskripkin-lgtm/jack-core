# 272 Cloudflared-Ausfall und kaputter svlogger (10.10.2026)
## Symptom
- Tunnel mcp.jack-mcp-cloudflare.bid: Cloudflare-Fehler 1033/530, JACK-MCP von aussen nicht erreichbar (ab ca. 22:30). cloudflared-Prozess lief seit 2,5 Tagen, hing aber (sv restart: 'got TERM', Prozess blieb).
- sv status: 'down: log: 0s' bei cloudflared, sshd, ssh-agent (und zeitweise crond/mosquitto).
## Ursache (gemessen)
- Die Dienste cloudflared, sshd, ssh-agent haben als log/run einen Symlink auf die gemeinsame Datei /usr/share/termux-services/svlogger. Diese Systemdatei war ueberschrieben worden (vermutlich 22.09.2026 beim Einrichten des cloudflared-Logs: Schreiben auf den Symlink schreibt in die Zieldatei) und lautete 'exec svlogd -tt .../var/log/sv/cloudflared'. Dadurch loggten ALLE Dienste, die svlogger nutzen (sshd, ssh-agent, ueber den Wrapper auch mosquitto und crond), ins cloudflared-Verzeichnis und blockierten dort gegenseitig die Sperre ('svlogd: unable to lock directory ... temporary failure'). cloudflared/current war 0 Byte seit 06.10.
- Folge: Ohne laufenden Log-Dienst wurde die Pipe von cloudflared nicht gelesen; der Dienst hing beim Neustart und baute keine Verbindung auf.
## Fix
- Mein erster Fix schrieb ebenfalls durch den Symlink und veraenderte die Systemdatei erneut (Fehler von mir). Danach: `apt-get install --reinstall termux-services` stellt svlogger wieder her (Original nutzt PWD und $LOGDIR). Kaputte Kopie liegt als ~/svlogger.broken_20261010.
- crond/log/run und mosquitto/log/run (echte Dateien, Wrapper) auf Original zurueck. Alle fuenf Log-Dienste laufen jetzt mit eigenem Verzeichnis (cloudflared, sshd, ssh-agent, mosquitto, crond).
- cloudflared/run: `--protocol http2` ergaenzt (Backup: cloudflared/run.bak). Ob das noetig ist, ist nicht bewiesen.
- Tunnel danach ueber den Dienst (pid 25632) stabil, 4 Verbindungen.
## Regeln
- NIE in service/*/log/run oder andere Symlinks per Redirect schreiben. Vorher `readlink -f` pruefen.
- Bei 'down: log: 0s' sofort `svlogd -tt <logdir> </dev/null` von Hand: Fehlermeldung zeigt die Ursache.
- `pgrep -f '<muster>'` in einem Befehl, dessen eigene Kommandozeile das Muster enthaelt, killt den eigenen Befehl (rc=-15).
## Offen
- ~/svlogger.broken_20261010 spaeter loeschen. Manueller cloudflared-Prozess 22668 beendet sich selbst.
- jack_autolearn: wurde 11:32 und ca. 16:50 gestoppt, wer ist ungeklaert; laeuft seit ca. 22:50 wieder.
