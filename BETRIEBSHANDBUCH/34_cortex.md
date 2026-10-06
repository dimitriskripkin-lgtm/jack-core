# 34. jack_cortex.py

Gelesen 03.10.2026, erste 40 Zeilen. Kein Umbau.

**Zweck:** Muskel-Steuerung. Xiaomi-IP aus config.ini, SSH-Port 8022.

**Log:** logs/jack_cortex.log plus jack_log. Fehler zusaetzlich in jack_errors.db, nur wenn die Datei schon da ist.

**Update 06.10.2026** (`JACK_TUNE_SSHSYNC`, live gemessen): `find_xiaomi()` kennt drei Quellen
fuer die Xiaomi-IP (config.ini `known`, Cache-Datei, `ip neigh`-Scan), aber schrieb `~/.ssh/config`
NUR im arp-scan-Zweig neu - und genau der kann auf diesem Root-freien Honor nie laufen
(`ip neigh` -> "Cannot bind netlink socket: Permission denied", dreifach bestaetigt ueber drei
verschiedene Wege). Dadurch blieben alle rohen `ssh xiaomi-jack`-Aufrufe (ca. 60 Stellen im Code)
nach jedem Xiaomi-Neustart mit neuer DHCP-IP tot, selbst wenn `jack_xiaomi.py`s eigener Weg
(direkter root@ip-Aufruf, kein Alias) schon wieder funktionierte. Fix: `_sync_ssh_config(ip)`
als eigene Funktion, jetzt in allen drei Erfolgszweigen aufgerufen. Backup:
`Attic/jack_cortex.py.bak_20261006_sshsync`.

**Offen:** die eigentliche Befehlsschleife hinter dem Schnitt.
