# 233. jack_handbuch_gate.py

Angelegt 07.10.2026 (Marker JACK_TUNE_HBGATE). Ergänzt in jack_mcp_server.py.

**Zweck:** Erzwingt, dass jede KI, die über MCP schreibt, vorher Pflichtzettel und Betriebshandbuch-Kapitel gesehen hat.

**Teile:**
- `INSTRUCTIONS`: kurzer Pflichttext, wird dem MCP-Server als `instructions` mitgegeben (jede KI sieht ihn beim Verbinden).
- Tools im MCP-Server: `start_hier()` (liefert 00_START_HIER.md + Tagesquittung), `handbuch_index(suche)`, `handbuch_kapitel(name)`.
- `gate(act, extra)` in `create_mission`: für Acts mit `freigabe: True` (jack_acts.py) wird ohne gültige `extra.quittung` abgelehnt.
  Bei `py_replace`/`sed_replace` ist der Schlüssel das Kapitel des Zielmoduls (Titelzeile `# NN. modul.py`), sonst START.
- Quittung = sha256("JACKGATE|schluessel|YYYY-MM-DD")[:8]. Steht nur in der Ablehnung (mit Auszügen) oder in den Tool-Antworten.
  Stateless, gilt nur für den Tag, braucht keine Session-Daten.
- Fail-open: Jeder interne Fehler lässt den Aufruf durch, damit der MCP-Kanal nie blockiert.

**Nicht betroffen:** Telegram-Befehle und interne Missions (schreiben direkt in missions/pending), nur der MCP-Weg ist gegated.

**Wartung:** Neue Kapitel müssen mit `# NN. modul.py` beginnen, sonst findet das Gate sie nicht. Zweck-Zeile als `**Zweck:** ...`.
Rücknahme im Notfall: in jack_mcp_server.py den Block `JACK_TUNE_HBGATE` in create_mission entfernen oder Datei jack_handbuch_gate.py umbenennen (Gate ist dann aus, wegen fail-open).

## Nachtrag 19.10.2026 (F13, JACK_TUNE_HBGATE_CLOSED)
Gate ist fail-closed: interner Fehler sperrt alle Acts ausser RESCUE_READS (fact, diag, compile_ok, sv_ok, hb_ok, file_exists, ro_git, ro_scan, ro_log_tail, ro_ps, ro_pyflakes). Gleiches im create_mission-Block des MCP-Servers (Import-Ausfall). git_publish braucht jetzt Quittung (FORCE_GATE_ACTS), obwohl freigabe=False. 8/8 lokal, live: git_publish ohne Quittung abgelehnt, ro_ps ohne Quittung durch, exec mit Quittung durch. Einbau mit 150-s-Auto-Rollback-Waechter. Backups jack_handbuch_gate.py.bak_20261019, jack_mcp_server.py.bak_20261019h. Offen: freigabe-Flag ist kein sicheres Schreibkennzeichen (dashboard_render, was_ist_neu pruefen).
