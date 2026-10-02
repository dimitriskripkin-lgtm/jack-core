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
