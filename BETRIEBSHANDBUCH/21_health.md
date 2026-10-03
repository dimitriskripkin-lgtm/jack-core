# 21. jack_health.py

Gelesen 03.10.2026, erste 90 Zeilen. Kein Umbau.

**Zweck:** Kurzbild Dienste, SSH, Heartbeats. Schreibt jack_health_now.json.

**bat_fresh:** liest Akku aus health_now. None wenn Datei fehlt, aelter als 900s, oder pct fehlt. Kein stiller 100er.

**main:** sv status jack_*, SSH echo OK, Heartbeat-Alter. down-Datei oder Alter ueber 3600s gilt als stale.

**Offen:** Rest hinter dem Tune-Block nicht zitiert.
