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

**Neu seit 06.10.2026, Skill-Werkstatt und Diagnose:**
- `plan_try`/`skill_confirm` (`JACK_TUNE_PLANTRY`) - fuehrt einen UI-Plan auf dem Xiaomi aus
  (erlaubte Schritte: open_app, intent, find_and_tap, ui_check, ui_text, input_text, keyevent,
  wait, home, back, unlock - bewusst OHNE exec und rohe tap-Koordinaten). Speichert einen Skill
  erst nach Dimas Bestaetigung (`skill_confirm`, nicht automatisch bei `jack_outcome`), ueber
  `jack_skill_lib` mit Stufen CANDIDATE -> TESTING (1 Erfolg) -> VERIFIED (3 Erfolge). `unlock`-Schritt
  nutzt `jack_xiaomi_unlock.ensure_unlocked()` (kein PIN).
- `xiaomi_screenshot` (`JACK_TUNE_VISION`) - echter Screenshot via `jack_vision.get_screen_b64()`,
  als Base64-Text in `skills_try/last_screen.b64` geschrieben, dann per `read_file` geholt und
  lokal dekodiert - Claude sieht den Bildschirm wirklich, nicht nur den `ui_text`-Baum. Kein
  Gemini-Call, kein Budget-Verbrauch.
- `honor_net_scan` (`JACK_TUNE_NETSCAN`) - read-only Netzdiagnose auf dem Honor selbst. **Wichtiger
  Fund:** `ip neigh`, `/proc/net/arp` und `getprop` sind auf diesem Root-freien Honor alle drei
  mit "Permission denied" verboten - das ist eine harte Geraetegrenze, kein Bug.
- `xiaomi_ssh_check` nimmt optional `ip` entgegen, um eine konkrete Kandidaten-IP gezielt zu testen,
  unabhaengig vom Cache (JACK_TUNE_IPOVERRIDE).

**Update 06.10.2026, Abend — drei echte Bugs in der Skill-Werkstatt gefunden und behoben:**
1. `skill_confirm` (`JACK_TUNE_SKILLFIX`) speicherte den Plan nur beim ALLERERSTEN Mal fuer einen
   Skillnamen. Bei Block-Bestaetigungen mehrerer Skills nacheinander (mehrere `plan_try` dann
   mehrere `skill_confirm` in Folge) hing jede Bestaetigung am zuletzt gelaufenen Plan - eine
   geteilte Cache-Datei (`last_plan.json`) ohne Namensbezug. Ergebnis: Skills konnten unter ihrem
   Namen einen komplett anderen Plan gespeichert haben. Fix: pro-Name-Cache-Datei
   (`skills_try/last_plan__<name>.json`), Plan wird bei jeder Bestaetigung neu geprueft und nur bei
   echter Aenderung neu gespeichert (sonst zaehlt record_run einfach weiter hoch,
   `JACK_TUNE_SKILLFIX2` - ein erster Versuch des Fixes hatte den Zaehler bei JEDER Bestaetigung
   faelschlich auf 0 zurueckgesetzt, selbst ohne Planaenderung - sofort gefunden und korrigiert).
2. `skill_run` (Stufe-2-Act, `JACK_TUNE_AUTONOMIE_1`) fehlte der `su`-Rueckfallweg fuer `intent`-
   Schritte. **Wichtiger Fund:** `jack_tun.intent()` OHNE `su`-Wrapper schlaegt auf diesem Geraet
   fuer System-Settings-Intents zuverlaessig fehl (Android wirft
   `java.lang.reflect.InvocationTargetException`), OBWOHL die SSH-Verbindung schon als root laeuft.
   `plan_try` hat das die ganze Zeit durch einen eingebauten Fallback (`su -c 'am start ...'`)
   verdeckt - jeder vermeintliche `jack_tun.intent()`-Erfolg lief in Wahrheit ueber diesen
   Fallback. **Jede Stelle im Code, die `jack_tun.intent()` ohne diesen Fallback direkt aufruft,
   hat wahrscheinlich dasselbe Problem.** Fix: `JACK_TUNE_SKILLRUN_SUFIX` - identischer Fallback
   jetzt auch in `skill_run`.
3. Neun der zwoelf heute gebauten Skills waren von Fund 1 betroffen (Block-Bestaetigungen) und
   wurden einzeln neu aufgebaut und bestaetigt. Nur `bluetooth_seite` und `termux_app_details`
   (einzeln bestaetigt) waren nie betroffen.

**Autonomiestufen (neu, Dimas Wort 06.10.2026):** Eigene, kleine Stufe NUR fuer Skills, bewusst
getrennt vom bestehenden `jack_intent.py`-Autonomie-System (das bleibt bei seinen 4 festen Ketten).
Stufe 0: Claude probiert, Dima bestaetigt jeden Lauf. Stufe 1: Claude probiert, prueft selbst per
`xiaomi_screenshot`, fragt nur bei Zweifel. **Stufe 2 (`skill_run`, live bewiesen an `wlan_seite`):**
ein VERIFIED-Skill (3/3 bestaetigte Laeufe) darf ohne jede Rueckfrage ausgefuehrt werden - aber
`skill_run` prueft den gespeicherten Plan bei JEDEM Lauf erneut gegen `jack_planner.validate_safe()`,
nicht nur beim Speichern. **Neue, unverifizierte Skills bauen bleibt immer Stufe 1, nie Stufe 2.**

**Offene Fragen für später:** Was macht `jack_mission_pull.py` genau? Was ist `jack_deadletter.py`?
Wie hängen `jack_cmd_handler.py`/`jack_mission_gen.py`/`jack_schema.py`/`jack_stand.py` mit dem
Shadow-Pfad zusammen?
