# 254 Quick-Tunnel-Aera (Entstehungsgeschichte)

Stand 2026-10-09. Gesichert, bevor ~/tunnel.log auf dem Xiaomi geloescht wurde.

- Zeitraum: 2026-06-17 bis 2026-10-09 lief auf dem Xiaomi ein cloudflared Quick-Tunnel (trycloudflare).
- 25 verschiedene Tunnel-Adressen, 182 Registrierungen (jeder Neustart = neue Adresse). Adressen bewusst nicht notiert.
- Rund 99 % des Logs (82 MB, ca. 579000 Zeilen) war quic/tunnel-Fehlerrauschen, kein Inhalt.
- Der Tunnel war Jacks erste Tuer nach aussen: Honor und Xiaomi sprachen darueber, bevor es den festen Cloudflare-Zugang (MCP-Host) gab.
- Der Vorfall (Xiaomi-Port offen, versiegelt, siehe 252) kam aus dieser Aera. Lehre: nichts lauscht auf 0.0.0.0 ohne Wachposten; Zugang nur ueber feste, authentifizierte Wege.
- 2026-10-09: Boot-Skripte deaktiviert (.aus), jack_api.py und jack_dashboard.py nach ~/Attic_20261009 (Xiaomi), tunnel.log geloescht. Neue Oberflaeche wird spaeter sauber gebaut.
- Entscheidungen Dima 09.10.: Titan bleibt, ADB-Autorisierungen widerrufen spaeter, Grok-Fetch (Cloudflare 1010) spaeter.
