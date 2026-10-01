# JACK — Just Autonomous Command Kit

Ein Lebens-OS auf zwei Android-Handys. Honor denkt und speichert, Xiaomi fuehrt aus.
Gebaut von Dima, LKW-Fahrer, ein Daumen, Termux — kein Studium, keine Ausbildung dafuer.

GitHub ist der Spiegel. Honor ist die Wahrheit.

## Hinweis zur Repo-Struktur

Das hier ist ein laufendes, produktives Ein-Personen-System, kein aufgeraeumtes Lehrbuch-Repo.
Die vielen `jack_*.py`-Dateien im Wurzelverzeichnis sind einzelne, eng benannte Dienste und Werkzeuge,
kein einzelnes grosses Programm. Einstiegspunkte: `jack_mcp_server.py` (MCP-Schnittstelle fuer externe KIs),
`jack_mission_runner.py` (Ausfuehrung benannter, geprueft Aktionen), `jack_autonomous.py` (Waechter-Logik),
`jack_chat_router.py` (Gespraechs-Logik). CI unter `.github/workflows/tests.yml` laeuft bei jedem Push.

## Stand 01.10.2026

Dienste (Honor, via runit `sv`): `jack_telegram`, `jack_cortex`, `jack_waechter`, `jack_autolearn`,
`jack_publisher`, `jack_focus_monitor`, `jack_missions`, `jack_mcp`, `cloudflared`.

## MCP: JACK spricht mit externen KIs

`jack_mcp_server.py` — Dienst `jack_mcp`, authentifiziert per Bearer-Token (rotiert bei Bedarf, **nie** in Git).
Erreichbar ueber festen Cloudflare Named Tunnel: `mcp.jack-mcp-cloudflare.bid`.

Tools: `graph_list_nodes`, `graph_read_node`, `graph_search`, `graph_list_edges`, `memory_search`, `memory_recent`,
`read_file`, `list_files`, `create_mission` (mit optionalem `wait_seconds`), `mission_status`, `describe_system`.

**36 Mission-Acts**, in ZWEI getrennten Whitelists (`jack_mission_runner.py` + `jack_mcp_server.py`) — beide
muessen bei jedem neuen Act synchron gehalten werden. Pruefskript: `python3 jack_whitelist_guard.py`.

Kategorien:
- Lese-/Pruef-Acts (grep_count, file_exists, compile_ok, honor_heat_report, xiaomi_ollama_status, was_ist_neu, ...)
- Schreib-Acts mit Backup+Rollback (sed_replace, py_replace, file_create, file_delete)
- `batch` — mehrere Schritte in einer Anfrage
- **Graph-Schreibzugriff fuer Claude**: `graph_add_fact`/`graph_remove_fact` — Vorschau-Standard, Backup vor jedem
  Schreiben, Geheimnis-Filter, nur eigene Eintraege loeschbar
- **Xiaomi-Steuerung** (alle live bewiesen): App-Steuerung (Chrome/Spotify/Maps/YouTube), `close_app_xiaomi`,
  `xiaomi_ollama_restart`/`xiaomi_ollama_stop` (Sitzung mit Auto-Aus-Timer), `xiaomi_ssh_check`
- `honor_ollama_disable` — Honor-Ollama-Hybrid abschaltbar (aktuell: aus, Entscheidung 28.09.)
- `sv_restart` / `reload_module` — Dienst-Neustart bzw. Hot-Reload einzelner Module ohne Unterbrechung
- `dashboard_render` — statisches HTML-Dashboard
- `propose_fix`/`list_proposals`/`preview_proposal`/`approve_proposal` — Self-Tooling mit Freigabestufe:
  JACK (oder Autolearn selbst) schlaegt vor, zeigt den Diff, wendet erst nach Freigabe an
- `was_ist_neu` — fasst Missionen/Fakten/Episoden der letzten N Stunden zusammen (auch live im Chat ueber
  eine eigene Gespraechs-Lane, synchron, ohne Warteschlangen-Umweg)

## Geraete

Honor = Gehirn. Termux, `jack_*.py`, Telegram, Wahrheit.
Xiaomi = Muskel. SSH-Alias `xiaomi-jack`. Nur benannte Acts, kein freier Shell-Zugriff.

## Drei Kuechen, keine vierte

- `jack_graph.db` — Fakten (Knoten+Kanten, WAL). Gewinnt bei Widerspruechen.
- `jack_memory.db` — Episoden + FTS5-Volltextsuche.
- `jack_identity.json` — Statischer Prompt-Kern, KEIN Faktenspeicher.

## Hintergrund-Kognition

`jack_autolearn_loop.py` prueft alle 5-10 Minuten: Skill-Kandidaten, Fehler-zu-Regel-Generierung, proaktiv
Xiaomi-Akku/Fehlerrate/SSH-Status UND (neu) Honor-Temperatur (Alarm ab 45C, Entwarnung unter 42C) — meldet
sich selbst per Telegram, generiert bei einer echten Fehlerrate-Spitze automatisch einen Vorschlag.

## Ollama-Politik (Entscheidung Dima, 28.09.2026)

Standard aus. Honor: komplett aus (frueherer Hybrid bewusst abgeschaltet). Xiaomi: nur pro Sitzung mit
Auto-Aus-Timer (`xiaomi_ollama_restart`/`xiaomi_ollama_stop`). Details: `ZETTEL_20260928_OLLAMA.md`.

## Was JACK nicht tut

- Kein generischer Remote-Shell-Zugriff, auch nicht auf dem Xiaomi — nur benannte, geprueft Acts
- Kein `git add -A` ohne vorher `git status` zu pruefen
- Kein `pkill -f` (toetet den eigenen Supervisor mit) — `pkill -x` oder `sv`
- Kein neues `jack_*.py` ohne Dimas Wort
- Ollama auf dem Honor bleibt hart verboten

## Wichtigste Lehren

1. Zwei getrennte Erlaubnislisten fuer Mission-Acts — immer beide patchen, beide Dienste neu starten.
2. Importierte Python-Module werden gecacht — Datei-Edits wirken erst nach Neustart ODER `reload_module()`.
3. `sv_restart` auf den eigenen ausfuehrenden Dienst muss verzoegert im Hintergrund laufen.
4. Auf dem Xiaomi existiert `sv`/runit nur ausserhalb der Root-Shell — `su -c "sv ..."`, nie `pkill -f`.
5. `.gitignore` wirkt nicht rueckwirkend — bereits eingecheckte Laufzeitdaten muessen per
   `git rm --cached` explizit entfernt werden.

## Selftest

```
python3 jack_selftest.py
python3 jack_whitelist_guard.py
```

## Eisen

P0 Temperatur. Backup vor Patch. Attic statt `rm`. Eine Pruefung, eine Frage. Enge, benannte Acts statt
generischer Zugriffe — immer.
