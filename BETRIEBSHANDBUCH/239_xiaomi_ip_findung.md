# 239 Xiaomi-IP-Findung im Hotspot-Netz (08.10.2026)
Anlass: Xiaomi hing am Honor-Hotspot (172.29.165.x statt 10.176.117.x). `ip neigh`, `ip addr` und /proc/net/arp sind ohne Root auf dem Honor gesperrt (Netlink Permission denied) -> die alte Suche fand nichts, JACK rief weiter die alte IP an.
## Was geaendert wurde
- jack_cortex.find_xiaomi (JACK_TUNE_XISCAN/XISCAN2): neuer letzter Schritt. Eigene lokale /24-Netze werden per UDP-connect-Trick erkannt (connect() auf x.x.x.1 sendet kein Paket, getsockname() liefert die Quelladresse; ungleich der Default-Route-Adresse = lokales Netz). Dort Port 8022 scannen (48 Threads, 0,6 s), dann _ssh_ok, dann Cache + ssh-config sync. Hoechstens 1 Scan pro 60 s. Live bewiesen: falscher Cache 10.1.2.3 -> GEFUNDEN 172.29.165.131.
- jack_config.get_param (JACK_TUNE_XIDYN): xiaomi_ip kommt zuerst aus ~/jack/.last_xiaomi_ip, dann config.ini/Default.
- jack_autonomous (Waechter, Ollama-Guard): Fallback-IP aus .last_xiaomi_ip statt fest.
## Nicht geaendert (bewusst)
jack_talk, jack_cmd_crawler, jack_screen_mapper, jack_adb_heal, jack_heartbeat, jack_ollama_gate haben die feste IP nur als Fallback; sie fragen zuerst `ssh -G xiaomi-jack`, und die ssh-config wird von find_xiaomi nachgefuehrt. wirkungs_check holt die IP ueber get_param-aehnlichen config.ini-Lesepfad (nicht geaendert).
## Messung
xiaomi_ssh_check vorher 8,3 s (Cache falsch/alt), nachher 0,48 s.
## Merke
Honor-Hotspot: Honor = 172.29.165.150, Xiaomi bekam 172.29.165.131. Nach Netzwechsel braucht JACK bis zu ~25 s, bis die Suche durch ist (SSH-Timeouts auf alte IPs).
