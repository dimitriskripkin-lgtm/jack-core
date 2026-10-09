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

## Port-Inventur Honor (09.10. 04:20, aus dem Code, Sockets sind auf der Honor nicht lesbar)
jack_mcp_server bindet uvicorn an 127.0.0.1:8000 (Zugang von aussen nur ueber den Cloudflare-Tunnel mit Rollen-Token), kortex_controller 127.0.0.1:5005, sshd 8022 (Schluessel). Kein Listener auf 0.0.0.0 im Live-Code gefunden.

## Weitere Xiaomi-Befunde (09.10. 05:05, nur gelesen)
- Magisk 30.7 mit Zygisk + Shamiko. Verified Boot gruen, Bootloader gesperrt (ro.boot.flash.locked=1). Build test-keys (Custom/Zertifiziert egal, ro.debuggable=0, ro.secure=1).
- ADB ueber TCP (service.adb.tcp.port=5555), aber ro.adb.secure=1 (Anmeldung noetig). 8 autorisierte ADB-Schluessel in /data/misc/adb/adb_keys (zuletzt geaendert 07.10.). Empfehlung: in den Entwickleroptionen "USB-Debugging-Autorisierungen widerrufen" und nur die eigenen Geraete neu zulassen.
- Bedienungshilfen aktiv: com.example.magictranslator.service.MyAccessibilityService (App translate.speech.text.translation.voicetranslator, Play-Store, seit 2022, Update 22.09.). Ein Bedienungshilfen-Dienst kann Bildschirminhalte mitlesen (Banking-/Trading-Apps liegen auf dem Geraet). Empfehlung: Dienst ausschalten oder App entfernen, JACK braucht ihn nicht (nutzt Root/ADB).
- WLAN-IP aktuell 172.29.165.131 (DHCP), SSH-Alias xiaomi-jack loest das auf. Zeitzone Europe/Berlin.
- bridge.py (HTTP Port 5000) und sensor_daemon.py (Juni) per cron @reboot vorgesehen, aber crond ist down, Port 5000 nicht offen = inaktiv.
- Termux: 276 Pakete, 32 pip-Pakete, runit nur titan aktiv.

## Wachposten-Idee (Skill-Vorschlag)
Neuer Lese-Act xiaomi_ports: per SSH netstat, Alarm in Telegram, wenn ein Prozess aus {python, node, nc, cloudflared, php} auf 0.0.0.0 lauscht, der nicht auf einer Erlaubnisliste steht (Erlaubnis: sshd 8022, adbd 5555). Als Telemetrie-Erweiterung alle 5 min moeglich. Wuerde den Vorfall oben nach hoechstens 5 min melden. Bau erst nach Dima-Go.

## Lehre
Quick-Tunnel nie auf Dienste mit Shell-Zugriff ohne Anmeldung. Regel: jeder Listener auf 0.0.0.0 braucht Token oder wird auf 127.0.0.1 gebunden. Naechster Schritt: Port-Inventur auch auf der Honor.
