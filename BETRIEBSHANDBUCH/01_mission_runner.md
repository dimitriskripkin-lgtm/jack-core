# JACK — BETRIEBSHANDBUCH

Angelegt 02.10.2026. Ziel: jedes wirklich verdrahtete Modul verstehen und nachschlagbar machen —
Zweck, Abhängigkeiten, Aufrufer, Eigenheiten. Waisen (unverdrahtete Module, siehe Modulkarte)
bekommen nur einen Einzeiler, keine Tiefenanalyse. Wächst Sitzung für Sitzung.

Methode: von den Dienst-Einstiegspunkten aus nach Zentralität sortiert, nicht alphabetisch.
Reihenfolge und Fortschritt: siehe FORTSCHRITT.md im selben Ordner.

---

## 1. jack_mission_runner.py (1227 Zeilen)

**Zweck:** Die Ausführungs-Engine. Nimmt eine Mission (ein JSON mit `act` + Parametern) aus
`missions/pending/`, prüft den Act gegen eine feste Erlaubnisliste, führt ihn aus, schreibt
das Ergebnis weg. Herzstück fast aller Acts, die diese Woche gebaut wurden (Xiaomi-Steuerung,
Self-Tooling, Graph-Schreibzugriff, Diagnose).

**Dienst:** `jack_missions` (via `loop()`, Dauerschleife, Standard-Poll 30s, mit `.mission_boost`
auf 1s beschleunigbar).

**Kernstruktur:**
- `ALLOWED` — feste Menge erlaubter Act-Namen (Stand 02.10.: 39 Acts). Muss synchron mit der
  zweiten Whitelist in `jack_mcp_server.py` gehalten werden (Pruefskript: `jack_whitelist_guard.py`).
- `run_act(m)` — der Dispatcher, eine lange Kette von `if act==...: ... return ok,note,out`.
  Jeder Zweig gibt sofort zurück, kein Fallthrough-Risiko.
- `sed_replace`/`py_replace` — Backup (`.fix.bak`), Ersetzung, bei `.py`-Dateien Pflicht-Kompiliercheck,
  optionaler `verify_act` danach. Jeder Fehlschlag löst automatisches Rollback aus.
- **Zwei parallele Freigabe-Pipelines, gefunden 02.10.:**
  1. **Alt:** `_run_fix_shadow()` — nur aktiv, wenn eine Mission `"staged": true` oder `"shadow": true`
     mitgibt. Schreibt nach `shadow/`, verifiziert, legt `pending_approvals.json` an. Genutzt von
     `jack_cmd_handler.py`, `jack_mission_gen.py`, `jack_mission_pull.py`, `jack_schema.py`, `jack_stand.py`
     (noch nicht einzeln geprüft — eigenes Kapitel folgt).
  2. **Neu (27.-28.09.):** `propose_fix`/`list_proposals`/`preview_proposal`/`approve_proposal` —
     schreibt nach `missions/proposals/pending/`, von Autolearn und Claude genutzt, Telegram-Befehle
     `/vorschlaege`, `/vorschau`, `/freigeben`.
  Beide kennen sich nicht. Nicht als Bug, aber als Klärungspunkt: sollen sie zusammengeführt werden,
  oder bleiben es bewusst zwei verschiedene Zwecke (schnelle Einzel-Freigabe vs. groessere, mehrfach
  verifizierte Patches)? Offene Frage an Dima.
- `one(path)` — verarbeitet genau eine Missionsdatei: Dedup-Check (schon in done/fail?), ruft
  `run_act`, wertet `expect` (PASS/FAIL-Erwartung) aus, schreibt Log nach `missions/logs/`, verschiebt
  nach `done/` oder `fail/`. Bei `fail/` zusätzlich `jack_deadletter.bump()`.
  **Wichtig:** schreibt JEDES Ergebnis zusätzlich als Zeile in `jack_memory.db`
  (`JACK_TUNE_MCPKANAL`) — dadurch kann Claude über `memory_recent`/`memory_search` auch
  Missionsergebnisse lesen, nicht nur über `mission_status`.
- `run_queue(maxn=20)` — verarbeitet Missionen eine nach der anderen. **Historischer Bug, seit
  27.09. gefixt (`JACK_TUNE_QUEUENOFAIL`):** ein Fehlschlag wird gemerkt (`rc=1`), aber die
  Schleife läuft weiter, statt abzubrechen.
- `loop(poll=30, maxn=200)` — die Dauerschleife. Schreibt Herzschlag, prüft `missions/STOP`
  (Kill-Switch, bleibt bewusst offen laut Zettel), lädt **bei jedem Zyklus** `jack_mission_pull.py`
  per `importlib.reload()` neu und ruft `pull()`/`push_status()` — ein eingebautes Dauer-Hot-Reload
  für genau dieses eine Modul, unabhängig vom allgemeinen `reload_module`-Act. Noch nicht geklärt,
  was `jack_mission_pull` genau synchronisiert — eigenes Kapitel.

**Bekannte Eigenheiten/Altlasten:**
- `xiaomi_ollama_restart_v1` und `xiaomi_ollama_stop_v1` sind stillgelegte Vorgänger-Versionen
  (28.09. durch `sv up`/`sv down`-Varianten ersetzt), noch im Code, aber aus `ALLOWED` entfernt —
  toter Code, kein Risiko, aber Aufräumkandidat.
- `sv_restart` auf den eigenen Dienst (`jack_missions`) läuft bewusst verzögert im Hintergrund
  (`JACK_TUNE_SELFRESTART_SAFE`), sonst Deadlock (gefunden 27.09.).

**Offene Fragen für später:** Was macht `jack_mission_pull.py` genau? Was ist `jack_deadletter.py`?
Wie hängen `jack_cmd_handler.py`/`jack_mission_gen.py`/`jack_schema.py`/`jack_stand.py` mit dem
Shadow-Pfad zusammen?
