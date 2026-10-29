# 244 Xiaomi-Gateway: Tuer, Schutzschalter, Inventar (08.10.2026)
## Befund
Die Tuer gibt es schon: jack_xiaomi.run_shell(cmd, as_root, timeout). IP ueber jack_cortex.find_xiaomi (Cache .last_xiaomi_ip, siehe Kap. 239), Timeout, ControlMaster (ControlPersist 120 s), Root per su -c. read_file/write_file/ssh()/lage() liegen darauf.
## Schutzschalter (JACK_TUNE_XIBREAKER)
Zwei Verbindungsfehler in Folge (ssh-Exitcode 255 oder Timeout) -> 30 s lang antwortet run_shell sofort mit success False, stderr 'Xiaomi weg (Schutz 30 s)', returncode -2, ohne find_xiaomi und ohne Wartezeit. Befehlsfehler (anderer Exitcode) zaehlen nicht. Zustand pro Prozess (_BR). Wirkt erst nach Restart der Dienste, die jack_xiaomi importieren (cortex, waechter, telegram wurden am 08.10. neu gestartet).
## Inventar
gemeinsam/gateway_inventar.md: Dateien mit direktem ssh, Zeilennummern, feste IPs, Import-Zaehler. Umbauregel: pro Datei ein Auftrag, ssh-Aufruf durch jack_xiaomi.run_shell ersetzen, feste IP raus, compile_ok, kein Restart in der Nacht.
## Umbau 08.10. (JACK_TUNE_GATEWAY)
wirkungs_check.py und jack_gemini_bridge.py laufen ueber run_shell. jack_talk.py und jack_heartbeat.py: feste Fallback-IP durch jack_config.get_param ersetzt (ssh -G liest nur die Config). Neu gestartet: telegram, cortex, waechter, autolearn.
## Schnellpfad (JACK_TUNE_XIQUICK, 08.10. 16:30, live und getestet)
run_shell nutzt zuerst die gecachte IP (jack_config.get_param liefert .last_xiaomi_ip zuerst) ohne Vorab-Check. Nur bei ssh-Exitcode 255 ruft es find_xiaomi, und nur wenn dort eine ANDERE IP herauskommt, wird einmal wiederholt. Der Schutzschalter zaehlt danach.
Test: Normalfall xiaomi_lage 2,5 s, xiaomi_ssh_check 0,18 s. Fehlerpfad: Cache-Datei ins Attic verschoben, naechster Aufruf 36,4 s (Suche), Xiaomi gefunden, Cache wieder da, danach 2,5 s. Neu gestartet: telegram, cortex, waechter, autolearn, missions.
Test Xiaomi WLAN aus (08.10. 16:17): xiaomi_lage 1. Aufruf 26 s (Suche plus Timeout), 2. Aufruf 2,8 s, 3. Aufruf 1,5 s, xiaomi_ssh_check 1,5 s, alle mit 'Xiaomi weg (Schutz 30 s)'. Schutzschalter greift wie geplant. Erholung (16:21): WLAN wieder an, sofort wieder Akku/WLAN/Speicher in 2,6-2,9 s, xiaomi_ssh_check 0,28 s. Kein Neustart noetig. Kleinigkeit: xiaomi_lage meldet bei 'weg' trotzdem ok=True (nur im Text sichtbar).
## Entscheidung Hitzeschutz (08.10.)
jack_heat_protection.py bleibt bewusst bei eigenem ssh: alle Aufrufe (get_temp, xiaomi_erreichbar, dienst_da) haben ConnectTimeout 5-6 s und subprocess-Timeout 5-10 s, die Alias-Config wird von jack_cortex synchron gehalten. run_shell wuerde vorher find_xiaomi rufen, das bei fehlendem Xiaomi bis ca. 40 s dauern kann (zwei ssh-Checks, Subnetz-Scan, einmal pro 60 s). Das waere im Sicherheitspfad ein Rueckschritt.
Vorschlag (noch nicht gebaut): Schnellpfad in run_shell. Erst die gecachte IP aus .last_xiaomi_ip direkt nutzen, find_xiaomi nur nach einem Verbindungsfehler und dann einmal wiederholen. Spart im Normalfall einen SSH-Handshake pro Aufruf und begrenzt den Fehlerfall.
A-010 geklaert: jack_autolearn ist per _d2_rate_ok() absichtlich auf ca. 6 h begrenzt, kein Haenger.
## Offen
jack_autolearn: nur noch der Log-Prozess startet staendig neu (Ursache unbekannt). seit 14:32 keine Zyklen ins Log (Auftrag A-010, Ursache unbekannt, Stillstand lag vor dem Neustart).
Umbau der Stellen ausserhalb von jack_xiaomi.py. Waisen (imp 0) zuerst ins Attic statt umbauen, vorher mit Dima klaeren. Ein echter Test des Schalters (Xiaomi aus) steht aus.

**Nachtrag 26.10.2026 (Claude, K1b-Nachzug von ChatGPT)**
JACK_TUNE_XIPATHSAFE: read_file quotet den Pfad (cat -- + shlex.quote). JACK_TUNE_XIWRITEGATE: write_file laeuft ueber run_shell (Breaker, IP-Wechsel) mit stdin (run_shell/_ssh_ein input_data optional). Live: normal, Leerzeichen und Semikolon im Namen geschrieben und gelesen, kein Befehl ausgefuehrt. Quoting ist kein Zugriffsschutz, Aufrufer pruefen Pfade.

**Nachtrag 29.10.2026 (Claude, Inventur I23, Entwurf ChatGPT Runde 5) JACK_TUNE_I23_PIN**
Xiaomi-Hostkey gepinnt: Dima hat 04:09 runde5_i23_pin.py.txt install auf dem HONOR ausgefuehrt (Fingerprint per bestehender SSH im eigenen Netz geholt = trust on first use). Pin-Datei known_hosts_xiaomi, HostKeyAlias xiaomi-jack, StrictHostKeyChecking=yes, nur ssh-ed25519, CheckHostIP=no (IP-Wechsel bricht nicht), neue Socket-Zone xi23. Alias-Block in der SSH-config vorangestellt (Cortex-HostName-Sync greift weiter). jack_xiaomi.SSH_OPTS umgestellt; Live: Termux uid 10069 + root uid 0 ok, ohne Pin rc 255 Host key verification failed. Dienste waechter/telegram/cortex/focus_monitor/autolearn neu 04:10; jack_missions + jack_mcp nur Dima. OFFEN: 6 Altwege mit /dev/null (jack_karte, jack_lerner, jack_mission_runner xiaomi_ssh_check, jack_sensors StrictHostKeyChecking=no, jack_wissen_ernte, jack_wissen_tief). Rueckweg: pin.py rollback mit Sicherungsordner i23-backup-20261029T030907Z-4cf587.

**Nachtrag 29.10.2026 05:56 (Claude, Entwurf ChatGPT Runde 6) JACK_TUNE_I23B_PIN:** jack_karte, jack_lerner, jack_sensors, jack_wissen_ernte, jack_wissen_tief und jack_mission_runner xiaomi_ssh_check nutzen jetzt jack_xiaomi.SSH_OPTS (gepinnt). Live: alle 5 Module uid 10069 ueber Pin. Runner-Teil wirkt nach jack_missions-Neustart (Dima). Ausnahme bleibt jack_heat_protection (Notfallpfad, Kap 244).

**Nachtrag 29.10.2026 07:01 (Claude, Entwurf ChatGPT Runde 7) JACK_TUNE_I23C_PIN:** jack_cmd_crawler, jack_intent, jack_scout, jack_screen_mapper, jack_voraussetzung auf jack_xiaomi.SSH_OPTS. Live: crawler/mapper uid 10069, intent ok, voraussetzung erreichbar, scout importiert. Nachgrep: KEIN jack_*.py mehr mit UserKnownHostsFile=/dev/null oder StrictHostKeyChecking=no|accept-new (jack_heat_protection nutzt den Alias). Waechter+Telegram neu 07:01. Offen (Nebenbefund ChatGPT): jack_scout._check verlangt stdout, ssh true liefert keins -> scan_ssh_verbindungen kann faelschlich nicht_erreichbar melden.
