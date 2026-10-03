# JACK — BETRIEBSHANDBUCH (Index)

Angelegt 02.10.2026. Ziel: jedes wirklich verdrahtete Modul verstehen und nachschlagbar machen.
Ein Ordner, eine Datei pro Modul — nicht eine wachsende Monster-Datei (technischer Grund: das
Mission-System hat ein Größenlimit von ~10KB pro Schreibvorgang, siehe Lehre unten).

Methode: von den Dienst-Einstiegspunkten aus nach Zentralität sortiert, nicht alphabetisch.
Waisen (unverdrahtete Module, siehe Modulkarte) bekommen nur einen Einzeiler, keine Tiefenanalyse.

## Kapitel
1. [jack_mission_runner.py](BETRIEBSHANDBUCH/01_mission_runner.md) — Ausführungs-Engine
2. [jack_telegram.py](BETRIEBSHANDBUCH/02_telegram.md) — Haupteinstieg, Befehlsinterpreter
3. [jack_autonomous.py](BETRIEBSHANDBUCH/03_autonomous.md) — Wächter-Logik, 8 interne Threads
4. [jack_talk.py](BETRIEBSHANDBUCH/04_talk.md) — Prompt-Bau, LLM-Anbindung
5. [jack_chat_router.py](BETRIEBSHANDBUCH/05_chat_router.md) — Lane-Klassifikation, "Kiste"
6. [jack_android.py](BETRIEBSHANDBUCH/06_android.md) — UI-Automatisierung, autonomer Vision-Agent
7. [jack_autolearn_loop.py](BETRIEBSHANDBUCH/07_autolearn_loop.md) — Hintergrund-Kognition, Skills, proaktive Beobachtung
8. [jack_intent.py](BETRIEBSHANDBUCH/08_intent.md) — Autonomie-Level-System (numerisches Gate, 6. Freigabe-Variante)
9. [jack_missions.py](BETRIEBSHANDBUCH/09_missions_alt.md) — altes Mission-System, AUFGELOEST: Warteschlange praktisch immer leer
10. [jack_exec.py](BETRIEBSHANDBUCH/10_exec.md) — Freitext-EXEC, Outcomes, Denylist
11. [jack_oracle.py](BETRIEBSHANDBUCH/11_oracle.md) — alter GitHub-Befehlskanal, eigenes Gate
12. [jack_cmd_handler.py](BETRIEBSHANDBUCH/12_cmd_handler.md) — Slash, shadow/pending_approvals
13. [jack_coder.py](BETRIEBSHANDBUCH/13_coder.md) — Werkstatt, HALIZA, kein wartet_freigabe
14. [jack_write.py](BETRIEBSHANDBUCH/14_write.md) — Werkstatt-Schreiben, Critic
15. [jack_planner.py](BETRIEBSHANDBUCH/15_planner.md) — Plan-Schritte Xiaomi
16. [jack_selfsee.py](BETRIEBSHANDBUCH/16_selfsee.md) — DIAG, .selfsee_pending
17. [jack_ui_type.py](BETRIEBSHANDBUCH/17_ui_type.md) — Xiaomi-UI, zwei Tueren
18. [jack_outcome_tracker.py](BETRIEBSHANDBUCH/18_outcome_tracker.md) — jack_outcomes.db
19. [jack_graph.py](BETRIEBSHANDBUCH/19_graph.md) — Graph-Kueche
20. [jack_groq_bridge.py](BETRIEBSHANDBUCH/20_groq_bridge.md) — Groq-Ruf
21. [jack_health.py](BETRIEBSHANDBUCH/21_health.md) — Health, bat_fresh
22. [jack_gemini_bridge.py](BETRIEBSHANDBUCH/22_gemini_bridge.md) — Gemini-Ruf
23. [jack_memory.py](BETRIEBSHANDBUCH/23_memory.md) — Episoden, FTS
24. [jack_vision_selector.py](BETRIEBSHANDBUCH/24_vision_selector.md) — Text-Tap Xiaomi
25. [jack_xiaomi_unlock.py](BETRIEBSHANDBUCH/25_xiaomi_unlock.md) — Wake plus Swipe
26. [jack_mcp_server.py](BETRIEBSHANDBUCH/26_mcp_server.md) — MCP-Tuer, Token fail-open
27. [jack_heat_protection.py](BETRIEBSHANDBUCH/27_heat.md) — 55/65/75
28. [jack_callback_handler.py](BETRIEBSHANDBUCH/28_callback.md) — PENDING_EXEC im RAM
29. [jack_voice_handler.py](BETRIEBSHANDBUCH/29_voice.md) — Telegram-Sprache
30. [jack_overmind_client.py](BETRIEBSHANDBUCH/30_overmind.md) — Whitelist, 180s
31. [jack_react.py](BETRIEBSHANDBUCH/31_react.md) — Fehleranalyse
32. [jack_db_queue.py](BETRIEBSHANDBUCH/32_db_queue.md) — ein Schreiber
33. [jack_focus_monitor.py](BETRIEBSHANDBUCH/33_focus.md) — Vordergrund
34. [jack_cortex.py](BETRIEBSHANDBUCH/34_cortex.md) — Xiaomi-Steuerung
35. [jack_approval.py](BETRIEBSHANDBUCH/35_approval.md) — Pfad-Gatter
36. [jack_log.py](BETRIEBSHANDBUCH/36_log.md) — gemeinsamer Logger
37. [jack_vecdb.py](BETRIEBSHANDBUCH/37_vecdb.md) — Vektor-Suche
38. [jack_screen_mapper.py](BETRIEBSHANDBUCH/38_screen_mapper.md) — UI-Signaturen
39. [jack_budget.py](BETRIEBSHANDBUCH/39_budget.md) — 300/40, 3 Euro
40. [jack_episoden.py](BETRIEBSHANDBUCH/40_episoden.md) — Momente
41. [jack_degraded.py](BETRIEBSHANDBUCH/41_degraded.md) — Xiaomi-Flagge

## Wichtigste Funde bisher, über alle Kapitel hinweg
- **Mindestens fünf unabhängige Freigabe-/Bestätigungs-Mechanismen** im Gesamtsystem (Shadow+pending_approvals,
  Self-Tooling-Proposals, PENDING_EXEC, PENDING_WRITE, selfsee_pending) — kennen sich nicht, nie vereinheitlicht.
- **Zwei unabhängige Wege, Fakten in den Graph zu schreiben** (`_do_save_fakt` im Chat, `graph_add_fact` als Act).
- **Zwei mögliche parallele Mission-Systeme**: `jack_mission_runner.py` (diese Woche, MCP-Acts) und ein
  älteres `jack_missions.py` (deutsche Status-Wörter), Letzteres läuft als interner Thread im Wächter —
  noch nicht live geprüft, ob beide wirklich gleichzeitig aktiv sind. **Wichtigster offener Punkt.**
- Doppelte Codepfade für Xiaomi-App-Steuerung (MCP-Act vs. Freitext-Regex direkt in jack_telegram.py).
- Mögliche doppelte Publisher-Aktivität (`_publisher_loop`-Thread im Wächter vs. `jack_publisher`-Dienst).
- Eine bisher undokumentierte vierte Datenbank: `jack_outcomes.db`.

## Technische Lehre aus dem Bau dieses Handbuchs selbst (02.10.2026)
Das Mission-System hat ein Größenlimit von ca. 10KB pro Schreib-Mission. Eine einzelne wachsende
Datei per `py_replace` mit der kompletten alten Datei als Anker verdoppelt das Paket bei jedem
Schritt und reißt dieses Limit schnell — Fehlschläge wurden dabei lange **nicht ehrlich gemeldet**
(`ok: true` trotz tatsächlich nicht geschriebenem Inhalt). Zusätzlich blähte eine eigene
Werkzeug-Fehler (`json.dumps` ohne `ensure_ascii=False`) deutsche Sonderzeichen auf das Dreifache
auf. Lösung: viele kleine, einzeln verifizierte Dateien statt einer wachsenden großen.
**Für jeden Schreibvorgang gilt ab jetzt: roh gegenlesen, nicht nur `ok: true` vertrauen.**
