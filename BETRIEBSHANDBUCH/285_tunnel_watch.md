# 285. jack_tunnel_watch.py - Tunnel-Waechter (15.10.2026)

## Zweck
Der bestehende Dienst `jack_waechter` prueft ueber `jack_autonomous.cycle()` den oeffentlichen JACK-MCP-Tunnel in festen Abstaenden. Marker: `JACK_TUNE_TUNNELWATCH`.

Gesundheitsvertrag:
- **HEALTHY**: oeffentliche Tunnel-URL liefert ohne Token HTTP 401.
- **DEAD-Kandidat**: HTTP 502/530, Cloudflare-Text 1033 oder Timeout/Verbindungsfehler.
- Andere HTTP-Codes sind **UNKNOWN** und loesen keinen Neustart aus.
- Der Prozessstatus von cloudflared allein gilt nie als Gesundheitsbeweis.

## Leitung / zweiter Host
Bevor ein DEAD-Kandidat einen Neustart ausloest, prueft der Waechter einen unabhaengigen zweiten Host (`https://example.com/`).
- Zweiter Host nicht erreichbar -> `NETWORK_DOWN`, **kein Neustart**.
- Zweiter Host erreichbar -> Tunnel-spezifischer Fehler darf behandelt werden.

Der Waechter fasst nur den Dienst `cloudflared` an. Nie WLAN, Mobilfunk, Hotspot, Flugmodus, Debugging, andere Dienste oder Geraeteneustart.

## Takt und Grenzen
- Intervall: 120 s.
- Cooldown zwischen Neustartversuchen: 600 s.
- Maximal 3 Neustartversuche pro rollender Stunde.
- Abschaltschalter: `~/jack/.tunnel_watch_off`.
- Statusdatei: `~/jack/.tunnel_watch_state.json`.
- Statusdatei enthaelt nur Zeit, Status, HTTP-Code, kurze Ursache und Restart-Zeitstempel; keine Tokens/Secrets.

## Neustart und Nachweis
Bei erlaubtem Restart:
1. `sv restart cloudflared`.
2. 20 s warten.
3. Tunnel erneut ohne Token pruefen.
4. Nur HTTP 401 ergibt `RECOVERED`.
5. Fehlt der 401-Nachweis, Status = `UNKNOWN`, niemals "repariert".

Meldungen und `TUNNEL-WATCH`-Logeintraege erfolgen nur bei Zustandswechsel bzw. Restart-Ergebnis. Die normale HEALTHY-Pruefung spammt weder Telegram noch Log.

## Einbau
`jack_autonomous.py`, Marker `JACK_TUNE_TUNNELWATCH`: ein eigener Daemon-Thread `_tunnel_loop()` prueft alle 120 s, damit der Takt nicht von der langen Haupt-Queue abhaengt. Es gibt bewusst nur diesen einen aktiven Aufrufer, damit zwei Threads nicht gleichzeitig denselben Restart-Pfad betreten. Bei Meldung nutzt der bestehende Waechter `notify()`.

## Backup
Vor dem Einbau erstellt:
`~/jack/backups/jack_autonomous.py.bak_tunnelwatch_20261015`

SHA256 des Live-`jack_autonomous.py` vor dem Patch:
`46709c7693c61011b8636cc974346e1d10277c2bd13bdd62f8a04f25e5aa44b3`

SHA256 `jack_tunnel_watch.py` bei Erstellung:
`e937f4f587df5f3cc05a7e8035e1403d620e6c729d0dea3edc215e8c1078f862`

## Tests / Grenzen
Pflicht nach Einbau:
- beide Python-Dateien kompilieren,
- `jack_waechter` neu starten,
- `sv_ok` pruefen,
- Statusdatei lesen und HTTP-401-Nachweis kontrollieren.

Nicht absichtlich fuer den Test erzeugen:
- kein echter 1033/530 durch Kappen des Tunnels,
- kein WLAN-/Netzausfall,
- kein Restart-Haemmern.

Der echte Fehlerpfad bleibt deshalb bis zu einem natuerlichen Ausfall bzw. einem spaeteren injizierten Offline-Test unbewiesen.

## Offene Punkte
- 1033/530/502- und NETWORK_DOWN-Pfade noch nicht live provoziert.
- Spaeter optional deterministische Injection-Tests fuer Probe/Restart ohne reale Leitung zu stoeren.
- Falls der externe zweite Host dauerhaft ungeeignet wird, muss er gegen einen anderen unabhaengigen stabilen Host getauscht und neu dokumentiert werden.

## Nachtrag 17.10.2026 (Claude): JACK_TUNE_ORIGINCHECK
Befund: Am 17.10. 11:45 hat der Waechter cloudflared neu gestartet, nur weil jack_mcp gerade neu startete (Cloudflare 502, Origin weg). Fix: Vor einem Neustart wird der lokale MCP (http://127.0.0.1:8000/mcp) geprueft. Antwortet er nicht, gilt der Status ORIGIN_DOWN und es gibt keinen Neustart (runit startet jack_mcp selbst neu). Injektionstest 4/4 (gesund, Origin weg, Tunnel tot mit Neustart, Netz weg).

Nachtrag 31.10.2026 17:02 (Claude, JACK_TUNE_TUNNELGRACE): Befund 31.10.: Tunnel fiel ca. 12:25 aus, Waechter startete cloudflared 12:30 neu, 12:34 wieder HTTP 401 (Meldung war korrekt). cloudflared beendet sich bei TERM erst nach seiner Grace-Period (Standard 30 s), runit-sv wartet nur 7 s -> "timeout", rc!=0 -> Waechter meldete UNKNOWN trotz gelungenem Neustart (z. B. 30.10. 10:25). Fix: sv -w 45 restart, subprocess-timeout 60 s. Nicht geaendert: cloudflared-run (ein --grace-period haette Tunnel-Neustart gebraucht). Claude-Chat verlor die MCP-Verbindung 12:28 und baute sie erst 17:00 neu auf; das lag an der Chat-Sitzung, nicht am Tunnel. Neustart jack_waechter 17:02.
