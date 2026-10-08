# 244 Xiaomi-Gateway: Tuer, Schutzschalter, Inventar (08.10.2026)
## Befund
Die Tuer gibt es schon: jack_xiaomi.run_shell(cmd, as_root, timeout). IP ueber jack_cortex.find_xiaomi (Cache .last_xiaomi_ip, siehe Kap. 239), Timeout, ControlMaster (ControlPersist 120 s), Root per su -c. read_file/write_file/ssh()/lage() liegen darauf.
## Schutzschalter (JACK_TUNE_XIBREAKER)
Zwei Verbindungsfehler in Folge (ssh-Exitcode 255 oder Timeout) -> 30 s lang antwortet run_shell sofort mit success False, stderr 'Xiaomi weg (Schutz 30 s)', returncode -2, ohne find_xiaomi und ohne Wartezeit. Befehlsfehler (anderer Exitcode) zaehlen nicht. Zustand pro Prozess (_BR). Wirkt erst nach Restart der Dienste, die jack_xiaomi importieren (cortex, waechter, telegram wurden am 08.10. neu gestartet).
## Inventar
gemeinsam/gateway_inventar.md: Dateien mit direktem ssh, Zeilennummern, feste IPs, Import-Zaehler. Umbauregel: pro Datei ein Auftrag, ssh-Aufruf durch jack_xiaomi.run_shell ersetzen, feste IP raus, compile_ok, kein Restart in der Nacht.
## Umbau 08.10. (JACK_TUNE_GATEWAY)
wirkungs_check.py und jack_gemini_bridge.py laufen ueber run_shell. jack_talk.py und jack_heartbeat.py: feste Fallback-IP durch jack_config.get_param ersetzt (ssh -G liest nur die Config). Neu gestartet: telegram, cortex, waechter, autolearn.
## Offen
jack_autolearn schreibt seit 14:32 keine Zyklen ins Log (Auftrag A-010, Ursache unbekannt, Stillstand lag vor dem Neustart).
Umbau der Stellen ausserhalb von jack_xiaomi.py. Waisen (imp 0) zuerst ins Attic statt umbauen, vorher mit Dima klaeren. Ein echter Test des Schalters (Xiaomi aus) steht aus.
