# JACK — Just Autonomous Command Kit

Ein Lebens-OS auf zwei Android-Handys. Honor denkt, Xiaomi führt aus.
Gebaut von Dima, LKW, ein Daumen, Termux.

GitHub ist der Spiegel. Honor ist die Wahrheit.

## Ist 23.09.2026

Dienste (Honor, via runit sv): jack_telegram, jack_cortex, jack_waechter, jack_autolearn, jack_publisher, jack_focus_monitor, jack_missions, jack_mcp, ollama_local.
Missions: Schreib-Missionen (sed_replace/py_replace) aktiv, mit Backup+Compile-Rollback.
Ollama: hybrid erlaubt (Honor lokal + Xiaomi remote), Hitzeschutz via jack_ollama_guard.py (42°C-Limit).

## Neu: JACK spricht mit externen KIs (MCP)

`jack_mcp_server.py` — Dienst `jack_mcp`, Port 8000, authentifiziert per Bearer-Token.
9 Tools: graph_list_nodes, graph_read_node, graph_search, graph_list_edges, memory_search, memory_recent, read_file, create_mission, describe_system.
Externe KIs koennen selbststaendig lesen, Code lesen, Missionen queuen, Ergebnisse zurücklesen.
Neue KIs fragen describe_system() statt ein Dokument zu lesen.
Mund: Groq (Talk). Gemini: Technik/Code + Fakt-Extraktion, None-Vertrag bei Ausfall + Ollama-Fallback.
Persona-Kern: `jack_persona_kern.md`.
Budget: 300 Text / 40 Vision pro Tag, EUR_WEEK=3.0 als Reißleine.

## Geräte

Honor = Gehirn. Termux, jack_*.py, Telegram, Wahrheit.
Xiaomi = Muskel. SSH-Alias `xiaomi-jack`. Hotspot-IP wechselt. Alias schlägt feste Zahl.

## Was JACK wirklich tut

Telegram nimmt den Satz. Router sortiert Werkzeug oder Talk.
Talk geht an Groq. Xiaomi führt aus, denkt nicht.
Wächter prüft Pulse, kennt geplanten Schlaf (sleep_until/is_sleeping).
Missions-Pipeline: pending/ automatisch verarbeitet, Ergebnis im Rückkanal.

## Was JACK nicht tut

Kein lokaler Chat-Server auf dem Honor.
Kein `pkill -f`.
Kein neues `jack_*.py` ohne Dimas Satz.
Wächter nicht neu starten ohne Drain: pending 0, fail 0, runner 0, stop 1.
GitHub nicht als Wahrheit lesen.

## Selftest

```
python3 /data/data/com.termux/files/home/jack/jack_selftest.py
```

Aktuell: services 4/4, Xiaomi + Cortex je nach Netzwerk.

## Eisen

P0 Temperatur.
Backup vor Patch.
Attic statt rm.
Eine Prüfung, eine Frage.
Kompiliert heißt nicht läuft.
Datei ist nicht Prozess.
