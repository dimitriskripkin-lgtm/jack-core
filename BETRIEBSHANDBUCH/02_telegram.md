## 2. jack_telegram.py (1367 Zeilen, größte Datei)

**Zweck:** Haupteinstieg für Dima. Long-Polling gegen die Telegram-API, Nachrichten entgegennehmen,
interpretieren, antworten. Kein sauberer Router — ein über die Zeit gewachsener Befehlsinterpreter
mit Dutzenden Spezialfällen, der an weit über zehn andere Module delegiert.

**Dienst:** `jack_telegram`.

**Grobstruktur von `handle(text)`** (über 900 Zeilen, Reihenfolge ist Priorität):
1. `/find <ziel>` — Bildschirm-Element suchen (eigener Thread, `jack_vision`+`jack_grid_vision`).
2. `[[PLAN:...]]`-Block im Text → `jack_planner`+`jack_schema` (validiertes Mehrschritt-Vorhaben).
3. `jack_exec.extrahiere(text)` — erkennt eingebettete Shell-Befehle im Nutzertext selbst,
   zeigt Ausführen/Abbrechen-Knopf (`PENDING_EXEC`).
4. Freitext "schreib eine datei..." → `jack_write.propose()`, Bestätigungs-Knopf (`PENDING_WRITE`).
5. Lange Kette fester Slash-Befehle (Tabelle unten).
6. Fällt keiner: Übergabe an `jack_chat_router.classify()`/`dispatch()` — FACT/EXPLAIN/DIAG/NEU-Lanes.
7. Deep-Navigation-Vorschläge (`jack_intent_lookup`), dann `jack_ui_nav`.
8. **Freitext-Heuristiken für Xiaomi-Steuerung** (Maps/YouTube/Spotify/Chrome) — eigene Regex-Treffer,
   rufen `jack_ui_type` **direkt** auf. Siehe Fund unten.
9. `jack_intent_apps.try_app_launch()` — App direkt starten.
10. Letzter Fallback: Gemini/Groq-Aufruf (`jack_chat_router.dispatch` → `jack_talk.talk_to_gemini`),
    mit `[[EXEC:...]]`-Tag-Erkennung in der Antwort → wieder Ausführen/Abbrechen-Knopf.

**Wichtiger Architektur-Fund: drei unabhängige Freigabe-/Bestätigungs-Oberflächen im Gesamtsystem,
die sich nicht kennen:**
1. `shadow/` + `pending_approvals.json` (siehe Kapitel 1, genutzt von `jack_cmd_handler.py` u.a.)
2. `missions/proposals/` (`propose_fix`/`approve_proposal`, diese Woche gebaut, Telegram `/vorschlaege`)
3. **Hier, Kapitel 2:** `PENDING_EXEC`/`PENDING_WRITE` — Inline-Bestätigungsknöpfe direkt im Chat,
   für von der KI selbst vorgeschlagene Shell-Befehle oder Dateischreibvorgänge. Reagiert über
   `handle_callback()` auf Knopfdruck, nicht über die Mission-Warteschlange.
Noch nicht geklärt, ob das bewusst getrennte Zwecke sind oder zusammengeführt werden sollte.

**Zweiter wichtiger Fund: doppelte Codepfade für Xiaomi-App-Steuerung.** Die MCP-Acts
(`chrome_search_xiaomi`, `maps_nav_xiaomi`, `spotify_play_xiaomi`, `youtube_*_xiaomi`, Kapitel 1)
rufen dieselben `jack_ui_type`-Funktionen auf wie die Freitext-Regex-Treffer **hier** in
`jack_telegram.py` (Schritt 8) — nur dass Letztere synchron, direkt, ohne Mission-Queue laufen.
Zwei getrennte Wege zum selben Ziel, nie bewusst vereinheitlicht.

**Vollständige Slash-Befehlsliste** (✅ = echt implementiert, 🚧 = Attrappe/Stub, ↗ = delegiert an eigenes Modul):
| Befehl | Status | Delegiert an / Notiz |
|---|---|---|
| `/find` | ✅ | `jack_vision`, `jack_grid_vision` |
| `/vision` | ✅ | (noch nicht einzeln geprüft) |
| `/harvest` | ✅ | eigener Thread, braucht Chrome im Vordergrund |
| `/agent` | 🚧 | reine Textantwort, kein echter Agent |
| `/auto` | 🚧 | reine Textantwort |
| `/ssh` | ✅ | `jack_ui_agent.run_ssh_agent` |
| `/code` | 🚧 | "braucht jack_coder Integration" |
| `/cc` | ✅ | Alias, piped direkt zu Gemini |
| `/db_trace` | ✅ | **neue DB gefunden:** `jack_outcomes.db`, Tabelle `outcomes` — noch nicht in der
  Drei-Küchen-Übersicht, eigenes Kapitel/Klärung nötig |
| `/rag` | ✅ | `jack_memory.search_similar()` |
| `/verbessere` | 🚧 | "braucht jack_coder Integration" |
| `/lernen` | ✅ | (noch nicht einzeln geprüft) |
| `/vorschlaege`, `/vorschau`, `/freigeben` | ✅ | diese Woche gebaut, Kapitel 1 |
| `/mission` | ✅ | (noch nicht einzeln geprüft) |
| `/budget` | ✅ | `jack_budget.status()` |
| `/appmap` | ✅ | `jack_intent_apps.MAP` |
| `/explore`, `/explore_deep` | ✅ | `jack_explorer(_deep)` |
| alles andere mit `/` | — | "Unbekannter Befehl" |

**Weitere Mechanik:**
- `_einzelinstanz()` — Lock-Datei mit PID-Lebendigkeitsprüfung (`os.kill(pid,0)` + `/proc/<pid>/cmdline`
  enthält "jack_telegram"), verhindert Doppel-Bots sauberer als eine reine Lock-Datei ohne Prüfung.
- `main()`-Schleife: `get_updates()` long-poll → Foto (eigener Thread, Gemini-Vision-Call direkt,
  nicht über die drei Küchen) → Voice (`jack_voice_handler`) → Text → `handle()`.
- Jedes Ergebnis geht zusätzlich in `jack_talk.add_to_window()` — ein Gesprächsfenster, getrennt von
  `jack_memory.db`'s `memory`-Tabelle (Kapitel zu `jack_talk.py` folgt).

**Offene Fragen für später:** Was ist `jack_outcomes.db` genau, und warum existiert es getrennt von
den drei bekannten Speichern? Was tun `jack_exec.py`, `jack_write.py`, `jack_planner.py`,
`jack_screen_mapper.py`, `jack_ui_agent.py`, `jack_intent_lookup.py`, `jack_ui_nav.py`,
`jack_voice_handler.py` im Detail? Sollen die vier Stub-Befehle (`/agent`,`/auto`,`/code`,`/verbessere`)
fertiggebaut oder entfernt werden?
