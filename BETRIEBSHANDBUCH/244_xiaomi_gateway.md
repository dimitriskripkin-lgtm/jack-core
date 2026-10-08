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
Noch nicht getestet: Xiaomi wirklich aus (Schutzschalter nach 2 Fehlern, 30 s Sperre). Dafuer WLAN am Xiaomi kurz aus, dann xiaomi_lage zweimal hintereinander.
## Entscheidung Hitzeschutz (08.10.)
jack_heat_protection.py bleibt bewusst bei eigenem ssh: alle Aufrufe (get_temp, xiaomi_erreichbar, dienst_da) haben ConnectTimeout 5-6 s und subprocess-Timeout 5-10 s, die Alias-Config wird von jack_cortex synchron gehalten. run_shell wuerde vorher find_xiaomi rufen, das bei fehlendem Xiaomi bis ca. 40 s dauern kann (zwei ssh-Checks, Subnetz-Scan, einmal pro 60 s). Das waere im Sicherheitspfad ein Rueckschritt.
Vorschlag (noch nicht gebaut): Schnellpfad in run_shell. Erst die gecachte IP aus .last_xiaomi_ip direkt nutzen, find_xiaomi nur nach einem Verbindungsfehler und dann einmal wiederholen. Spart im Normalfall einen SSH-Handshake pro Aufruf und begrenzt den Fehlerfall.
A-010 geklaert: jack_autolearn ist per _d2_rate_ok() absichtlich auf ca. 6 h begrenzt, kein Haenger.
## Offen
jack_autolearn: nur noch der Log-Prozess startet staendig neu (Ursache unbekannt). seit 14:32 keine Zyklen ins Log (Auftrag A-010, Ursache unbekannt, Stillstand lag vor dem Neustart).
Umbau der Stellen ausserhalb von jack_xiaomi.py. Waisen (imp 0) zuerst ins Attic statt umbauen, vorher mit Dima klaeren. Ein echter Test des Schalters (Xiaomi aus) steht aus.
