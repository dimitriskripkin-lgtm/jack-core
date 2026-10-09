# 255 Wachposten xiaomi_ports

Modul jack_xiaomi_ports.py (JACK_TUNE_XPORTS). Wird aus jack_telemetry.loop() alle 5 Min aufgerufen.
- Liest per jack_xiaomi.run_shell 'netstat -tlnp' (root) auf dem Xiaomi.
- Meldet (Telegram + decisions.log 'XPORTS'), wenn python/python3/node/nc/ncat/cloudflared/php/ruby/socat auf 0.0.0.0, :: oder * lauscht.
- Erlaubt: sshd 8022, adbd 5555. Alles auf 127.0.0.1 und andere Prozessnamen werden ignoriert.
- Gleiche Meldung hoechstens alle 6 h (Zustand .xiaomi_ports_state.json). Aendert nichts am Xiaomi.
- Live-Test 09.10.: 64 netstat-Zeilen, nur sshd:8022 auf Wildcard -> sauber.
- Abschalten: Import-Block in jack_telemetry.loop entfernen.
Offen: Telegram-Zustellung nicht live ausgeloest (kein Fehlalarm erzeugt).
