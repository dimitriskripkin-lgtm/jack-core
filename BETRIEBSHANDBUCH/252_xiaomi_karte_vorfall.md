# 252 Xiaomi-Karte und Vorfall offene Root-API (09.10.2026)

Stand 09.10.2026 04:20, gelesen per SSH (nur lesend, bis auf die unten genannten Abdichtungen).

## Geraet
Xiaomi 11T Pro (2107113SG), Android 13, Kernel 5.4.233, Magisk-Root (su = u:r:magisk:s0). 7,2 GB RAM (3,8 GB belegt), Swap 6 GB (2,5 GB belegt), Load ca. 4 (Termux-intern, 8 Kerne). Temperatur 38 Grad, Akku 88 Prozent laedt. Uptime 3,6 Tage. 130 Fremd-Apps, darunter Banking-, Trading- und Krypto-Apps - Root auf diesem Geraet ist hochsensibel.

## Termux-Home (20 GB)
Altlasten: Titan_* (TITAN_SYSTEM 2,0 GB, TITAN_BACKUPS 1,7 GB), dimitri*, jack.py/jack_v2.py, sonde.py, sensory_link.py u.a. Cron @reboot: sensor_daemon.py, bridge.py (nicht geprueft, nicht aktiv).
runit (Termux): nur "titan" laeuft (Heartbeat-Loop, siehe unten). crond, sshd, ollama, ssh-agent, jack_alpha down seit Boot, mosquitto runsv fehlt. sshd laeuft ueber ~/.termux/boot/start_sshd.sh.
SSH: authorized_keys unveraendert seit 09.07., zwei Schluessel (Xiaomi-lokal, Honor).

## VORFALL: unauthentifizierte Root-API (gefunden und abgedichtet 09.10. 04:15)
- jack_api.py (Port 8081, POST /api/run fuehrte "su -c <cmd>" aus) und jack_dashboard.py (Port 8080, /run mit shell=True), beide 0.0.0.0, ohne jede Anmeldung.
- Zwei cloudflared Quick-Tunnel (start_tunnel.sh und jack_start.sh in ~/.termux/boot) machten beide Ports ueber zufaellige trycloudflare.com-URLs oeffentlich. Lief seit dem letzten Boot (3,6 Tage), Skripte stammen von Juni.
- Kein JACK-Modul nutzt diese Ports.
- Massnahme: beide Python-Prozesse und beide cloudflared beendet; jack_start.sh und start_tunnel.sh nach .aus umbenannt (Rueckgaengig: Umbenennen). Ports 8080/8081 zu, 0 cloudflared.
- Spurensuche (nur lesen): authorized_keys unveraendert, keine neuen Dateien in den letzten 3 Tagen im Termux-Home und in /data/local/tmp. Kein Beleg fuer Missbrauch, aber auch nicht auszuschliessen (Tunnel-Log ~/tunnel.log, 82 MB, protokolliert keine Requests).
- Offen fuer Dima: tunnel.log loeschen (Quick-Tunnel-URLs stehen darin), alte Skripte jack_api.py/jack_dashboard.py entfernen oder mit Token absichern.

## Titan-Heartbeat (laeuft noch)
Dienst "titan" (run-Skript "TITAN ALPHA CORE"): alle 60 s termux-location und termux-battery-status, Senden "NODE_ALPHA|BATT|LOC-Provider" per nc unverschluesselt an 152.53.229.148:8888 ("OMEGA"). Antwort heute: HTTP 400. Kostet Akku (GPS-Abfrage jede Minute) und sendet Daten an eine externe IP. Entscheidung Dima: abschalten oder behalten.

## Lehre
Quick-Tunnel nie auf Dienste mit Shell-Zugriff ohne Anmeldung. Regel: jeder Listener auf 0.0.0.0 braucht Token oder wird auf 127.0.0.1 gebunden. Naechster Schritt: Port-Inventur auch auf der Honor.
