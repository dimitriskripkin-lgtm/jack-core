# JACK — Just Autonomous Command Kit

Ein Lebens-OS auf zwei Android-Handys. Honor denkt und speichert, Xiaomi führt aus.
Gebaut von Dima, LKW-Fahrer, ein Daumen, Termux — kein Studium, keine Ausbildung dafür.

GitHub ist der Spiegel. Honor ist die Wahrheit.

## Hinweis zur Repo-Struktur

Das hier ist ein laufendes, produktives Ein-Personen-System, kein aufgeräumtes Lehrbuch-Repo.
Einstiegspunkte: `jack_mcp_server.py` (MCP für externe KIs), `jack_mission_runner.py` (Ausführung
benannter Acts), `jack_autonomous.py` (Wächter), `jack_chat_router.py` (Gespräch). CI läuft bei
jedem Push. Wer die Architektur wirklich verstehen will: `BETRIEBSHANDBUCH.md` ist der Einstieg —
Alle 197 jack_*.py-Module sind erfasst (230 Kapitel), Stand 03.10.2026.

## Stand 03.10.2026

Dienste: `jack_telegram`, `jack_cortex`, `jack_waechter`, `jack_autolearn`, `jack_publisher`,
`jack_focus_monitor`, `jack_missions`, `jack_mcp`, `cloudflared`.

## MCP

`jack_mcp_server.py`, Dienst `jack_mcp`, Bearer-Token (nie in Git), Cloudflare Tunnel
`mcp.jack-mcp-cloudflare.bid`. **49 Mission-Acts**, zwei synchron gehaltene Whitelists
(`jack_mission_runner.py` + `jack_mcp_server.py`), Prüfskript `jack_whitelist_guard.py`.

Wichtigste Kategorien: Lese-/Prüf-Acts, Schreib-Acts mit Backup+Rollback, `batch`, Xiaomi-Steuerung
(Chrome/Spotify/Maps/YouTube, alle live bewiesen), `graph_add_fact`/`graph_remove_fact`,
`propose_fix`/`approve_proposal` (Self-Tooling mit Freigabestufe), `was_ist_neu`.

## Freigabe-Wege — gewachsen, nicht geplant

Sechs unterschiedliche Mechanismen fragen JACK um Erlaubnis, bevor er etwas Riskanteres tut:
die Shadow-Pipeline, die Self-Tooling-Vorschläge, zwei Inline-Knöpfe in Telegram, ein eigener Weg
für Diagnose-Vorschläge und ein numerisches Autonomie-Level. Sie kennen sich nicht gegenseitig.
Eine Entscheidung, ob das zusammengeführt wird, steht noch aus.

## Geräte

Honor = Gehirn. Xiaomi = Muskel, SSH-Alias `xiaomi-jack`, nur benannte Acts.

## Drei Küchen

`jack_graph.db` (Fakten, gewinnt bei Widersprüchen), `jack_memory.db` (Episoden+Volltextsuche),
`jack_identity.json` (statischer Prompt-Kern, kein Faktenspeicher).

## Ollama-Politik (28.09.2026)

Standard aus. Honor komplett aus. Xiaomi nur pro Sitzung mit Auto-Aus-Timer.
Details: `ZETTEL_20260928_OLLAMA.md`. Der Honor-Hybrid (`jack_ollama_guard.py`) ist seit 03.10.2026 komplett entfernt, nicht nur deaktiviert.

## Was JACK nicht tut

Kein generischer Shell-Zugriff. Kein `git add -A` ohne `git status`. Kein `pkill -f`.
Kein neues `jack_*.py` ohne Dimas Wort. Ollama auf dem Honor bleibt verboten.

## Selftest

```
python3 jack_selftest.py
python3 jack_whitelist_guard.py
```

## Wie hier gearbeitet wird

Ein paar Dinge haben sich über die Zeit als wichtig erwiesen. Die Temperatur geht immer vor — ein
Patch kann warten, ein überhitztes Handy nicht. Vor jeder Änderung steht ein Backup, nicht weil man
es müsste, sondern weil man es später zu schätzen weiß, wenn etwas schiefgeht. Gelöschtes landet im
Attic, nicht im Nichts. Und wenn eine Prüfung eine klare Antwort geben kann, fragt man einmal,
bekommt sie, und macht weiter — statt zu raten oder dasselbe dreimal zu probieren.

Das Gleiche gilt für die Werkzeuge selbst: lieber eng benannt und auf einen Zweck zugeschnitten als
generisch und mächtig. Ein Act, der genau eine Sache tut und das beweisen kann, ist mehr wert als
einer, der vieles könnte und am Ende niemand mehr sicher weiß, was er wirklich tut.
