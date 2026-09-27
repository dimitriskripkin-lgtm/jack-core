# JACK — Just Autonomous Command Kit

Ein Lebens-OS auf zwei Android-Handys. Honor denkt und speichert, Xiaomi führt aus.
Gebaut von Dima, LKW-Fahrer, ein Daumen, Termux — kein Studium, keine Ausbildung dafür.

GitHub ist der Spiegel. Honor ist die Wahrheit.

## Stand 27.09.2026

Dienste (Honor, via runit `sv`): `jack_telegram`, `jack_cortex`, `jack_waechter`, `jack_autolearn`, `jack_publisher`, `jack_focus_monitor`, `jack_missions`, `jack_mcp`, `cloudflared`.

## MCP: JACK spricht mit externen KIs

`jack_mcp_server.py` — Dienst `jack_mcp`, authentifiziert per Bearer-Token (rotiert bei Bedarf, **nie** in Git).
Erreichbar über festen Cloudflare Named Tunnel: `mcp.jack-mcp-cloudflare.bid` (Dienst `cloudflared`, keine wechselnde Quick-Tunnel-URL).

Tools: `graph_list_nodes`, `graph_read_node`, `graph_search`, `graph_list_edges`, `memory_search`, `memory_recent`, `read_file` (bis 5000 Zeilen), `list_files` (bis 5000 Einträge), `create_mission` (mit optionalem `wait_seconds` — wartet server-seitig auf das Ergebnis statt Polling), `mission_status`, `describe_system`.

**31 Mission-Acts**, in ZWEI getrennten Whitelists (`jack_mission_runner.py` + `jack_mcp_server.py`) — beide müssen bei jedem neuen Act synchron gehalten werden. Prüfskript: `python3 ~/jack/jack_whitelist_guard.py`.

Kategorien:
- Lese-/Prüf-Acts (grep_count, file_exists, compile_ok, ...)
- Schreib-Acts mit Backup+Rollback (sed_replace, py_replace, file_create, file_delete)
- `batch` — mehrere Schritte in einer Anfrage
- **Xiaomi-App-Steuerung** (alle 7 live bewiesen): `open_url_xiaomi`, `xiaomi_battery`, `xiaomi_ollama_restart`, `xiaomi_ssh_check`, `chrome_search_xiaomi`, `spotify_play_xiaomi`, `maps_nav_xiaomi`, `maps_open_xiaomi`, `youtube_search_xiaomi`, `youtube_play_xiaomi` — alle nutzen `jack_xiaomi_unlock.ensure_unlocked()` zuerst und `jack_verify_gate` zur Nachprüfung
- `create_demo_file` — Downloads-Schreibzugriff, eng auf `jack_demo_*.txt` begrenzt
- `sv_restart` — Dienst-Neustart über feste Whitelist der 8 echten JACK-Dienste, mit Selbstschutz gegen Deadlock bei Selbst-Neustart
- `reload_module` — Hot-Reload einzelner Module (`jack_ui_type`, `jack_verify_gate`, `jack_xiaomi_unlock`, `jack_yt_hybrid`, `jack_chat_router`, `jack_ui_session`) ohne Dienst-Neustart, live zweistufig bewiesen
- `dashboard_render` — erzeugt ein statisches HTML-Dashboard (Akku, Missions-Status, Verbindungen, letzte Entscheidung), erreichbar über lokalen `python3 -m http.server` (Chrome kann weder `content://` noch `file://` für App-Sandbox-Pfade lesen — Android-Sperre)
- `propose_fix` / `list_proposals` / `approve_proposal` — Self-Tooling mit Freigabestufe: JACK (oder Autolearn selbst) kann einen konkreten Fix vorschlagen, der erst nach Freigabe über dieselben geprüften Acts angewendet wird

## Geräte

Honor = Gehirn. Termux, `jack_*.py`, Telegram, Wahrheit.
Xiaomi = Muskel. SSH-Alias `xiaomi-jack`. Nur benannte Acts, kein freier Shell-Zugriff.

## Drei Küchen, keine vierte

- `jack_graph.db` — Fakten (Knoten+Kanten, WAL). Gewinnt bei Widersprüchen.
- `jack_memory.db` — Episoden + FTS5-Volltextsuche.
- `jack_identity.json` — Statischer Prompt-Kern, KEIN Faktenspeicher.

## Hintergrund-Kognition

`jack_autolearn_loop.py` prüft alle 5-10 Minuten: Skill-Kandidaten, Fehler-zu-Regel-Generierung, UND (neu) proaktiv Xiaomi-Akku/Fehlerrate/SSH-Status — meldet sich selbst per Telegram, generiert bei einer echten Fehlerrate-Spitze automatisch einen Vorschlag über `propose_fix`.

## Was JACK nicht tut

- Kein generischer Remote-Shell-Zugriff, auch nicht auf dem Xiaomi — nur benannte, geprüfte Acts
- Kein `git add -A` ohne vorher `git status` zu prüfen — Secrets landen sonst im Klartext im öffentlichen Repo (ist zweimal passiert, beide Male sofort rotiert/behoben)
- Kein `pkill -f`
- Kein neues `jack_*.py` ohne Dimas Wort
- Ollama auf dem Honor bleibt hart verboten

## Wichtigste Lehren dieser Woche

1. **Zwei getrennte Erlaubnislisten** für Mission-Acts — beide patchen, beide Dienste neu starten, sonst blockiert die eine, was die andere schon erlaubt.
2. **Importierte Python-Module werden gecacht** — Datei-Edits wirken erst nach Dienst-Neustart ODER `reload_module()`.
3. **`sv_restart` auf den eigenen ausführenden Dienst** (`jack_missions`) muss verzögert im Hintergrund laufen, sonst hängt die ganze Warteschlange (zweimal live reproduziert, jetzt strukturell gefixt).
4. **Der uralte `run_queue()`-Abbruch-Bug** (aus den allerersten Übergabeprotokollen) ist endlich gefixt — ein Fehlschlag überspringt jetzt nur die eine Mission, nicht die ganze Schleife.

## Selftest

```
python3 /data/data/com.termux/files/home/jack/jack_selftest.py
python3 /data/data/com.termux/files/home/jack/jack_whitelist_guard.py
```

## Eisen

P0 Temperatur. Backup vor Patch. Attic statt `rm`. Eine Prüfung, eine Frage. Enge, benannte Acts statt generischer Zugriffe — immer.
