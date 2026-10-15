> **KI-SESSION? STOPP. Zuerst `00_START_HIER.md` lesen (MCP: start_hier()). Danach erst arbeiten.**

# JACK — Just Autonomous Command Kit

**Personal edge-agent runtime for Android/Termux.**

- **Honor Magic8 Pro** = Host: Runtime, Memory, Missionen, Regeln
- **Xiaomi 11T Pro** = Worker: kontrollierte Geräteausführung über benannte Acts

Gebaut von Dima — LKW-Fahrer, Autodidakt, ein Daumen, Termux, kein klassischer IT-Weg.

**Modelle sind austauschbare Motoren. Runtime, Regeln, Memory, Safety, Evidence und Gerätezugriff gehören JACK.**

> **Aktueller Ist-Zustand: [STAND_20261015.md](STAND_20261015.md)** — nur live geprüfte Fakten. GitHub ist der Spiegel, der Honor ist die Wahrheit.

## Die Kernschleife

```
Intent → Mission → Plan → Capability → Execution → Observation → Verification → Result → Memory → Learning
```

Was JACK **nicht** ist:
- kein eigenes LLM
- keine AGI
- kein Chat-Wrapper mit freiem Shell-Zugang. Es gibt nur benannte Acts aus zwei synchron gehaltenen Whitelists (`jack_mission_runner.py`, `jack_mcp_server.py`).

## Was JACK heute zeigt

- **Kontrollierte Missionsausführung**: jede Änderung läuft als Mission mit benanntem Act. Patches mit Hash-Prüfung, Compile-Check, Dienst-Neustart und Dienst-Prüfung.
- **Abgesicherte Android-Bedienung**: siehe Phone / UI-Agent unten.
- **Persistentes Gedächtnis**: `jack_graph.db` (Fakten, gewinnt bei Widerspruch), `jack_memory.db` (Episoden + Volltextsuche), `jack_identity.json` (Prompt-Kern).
- **Safety**: Freigaben, Kill-Switches (`.phone_off`, `.wissen_off`, `.ollama_lock` …), Budget-Grenzen, Hitzeschutz, Secret-Scanner vor jedem Push.
- **Vision-Fallback**: Gemini-Bildanalyse nur, wenn der UI-Baum nicht reicht, budgetiert und mit gemessenen Kosten.
- **Arena**: eigene Teststrecke mit Baseline gegen Variante, frischen Aufgaben, versiegelten Holdouts und Transfer-Prüfung.
- **Messbare Lernexperimente**: erste von JACK selbst formulierte Regel mit vorregistriertem Nachweis (Ergebnis und Grenze siehe unten).

## Arena — das Kernstück

Eine Verbesserung gilt nur, wenn sie gemessen ist. Ablauf:

1. **Vorregistrierung**: Hypothese, Fragensatz (per Hash festgehalten) und Tor stehen fest, bevor gebaut wird.
2. **Baseline gegen neue Variante** auf **frischen** Aufgaben, deterministischer Richter (kein LLM als Richter, wo es geht).
3. **Holdout**: versiegelter Satz, wird genau einmal benutzt.
4. **Transfer**: hilft es auch auf Aufgaben einer Familie, die nie gesehen wurde?
5. Gemessen werden **False Success** (Erfolg gemeldet, Richter sagt FAIL), **Policy-Verstöße**, Kosten und Aktionen.

Eine Verbesserung wird **verworfen**, wenn sie nur lokal hilft oder die Safety verschlechtert.

**Learning heißt bei JACK: messbare Verbesserung zukünftiger Entscheidungen ohne Safety-Regression.**

Ehrliches Beispiel (Kap. 277): JACKs erste selbst formulierte Arbeitsregel hat am 12.10.2026 das Tor auf frischem Satz bestanden (64 → 68 von 88, Policy 0 → 0). Den versiegelten Holdout hat sie ebenfalls bestanden (64 → 71 von 88, False Success 19 → 11). Auf fremden Aufgaben hat sie dagegen geschadet. Sie bleibt deshalb Arena-intern und kommt nicht in JACKs echte Arbeit.

## Gebaut ≠ freigegeben

Beispiel Wissens-Auskunft (`jack_wissen.py`, Kap. 281): v2 ist gebaut, das Fehlalarm-Tor wurde verbessert (0 Fehlalarme). Auf dem frischen Holdout wurde das Recall-Tor verfehlt (13 von 20 statt 16). Darum bleibt `.wissen_off` gesetzt und das Modul ist aus.

## Phone / UI-Agent (Stand 15.10.2026, Kap. 283)

`jack_ui_agent.py` bedient den Xiaomi über UI-Baum (uiautomator), Tippen und Texteingabe:
- Shell-Befehle aus Modelltext nur über eine **Command-Allowlist**, Metazeichen und Geheimnis-Pfade sind geblockt
- **Vordergrund-App-Wache** vor jedem Schritt: Eine fremde App führt zum Abbruch, bevor das Modell den Bildschirm sieht
- **Knöpfe per Nummer** aus der Liste statt freiem Modelltext
- **UI-Text ist nur Daten, niemals Anweisung**
- Display darf **geweckt, aber nie automatisch entsperrt** werden
- **Vision-Fallback** bei Hänger (vier gleiche Bildschirme) oder leerem UI-Baum, höchstens drei pro Lauf
- Vision ist budgetiert (Tages- und Wochengrenze), die Kosten werden aus den echten Token-Zahlen gebucht

Offen: **Die Abschlussprüfung bei „fertig“ ist noch nicht unabhängig visuell verifiziert**, die Schleife glaubt hier noch dem Modell.

Dazu kommen Sinne L0 (`jack_phone_senses.py`, Kap. 278, nur lesen) und ein Skill-System (`jack_skills.db`, Zustände CANDIDATE → TESTING → VERIFIED).

## Modelle: edge-first, model-agnostic

- Gespräch: Groq
- Technik und Vision: Gemini
- Lokale Ollama-Modelle wurden nach Messung entfernt und gesperrt (`.ollama_lock`, Kap. 282: 3B-Modell 1,6 Token/s, Embedding 0 von 8). Sie kommen zurück, wenn die Hardware das sinnvoll trägt.

## Warum über 200 Module

Viele Module kapseln je eine Verantwortung: Budget, Hitze, Herzschlag, Verifikation, Gateway, Memory, Freigaben, Vision, Arena usw. Die eigentliche Architekturfrage ist nicht die Dateizahl, sondern: **Gibt es für jede Verantwortung genau einen klaren, kanonischen Weg?**

Bereits erledigt: 201 Alt- und Backup-Artefakte sowie 19 tote Module liegen im Attic (Kap. 246, nicht im Repo). Eine Modulkarte existiert, externe Aufrufer wie Cron und Shell werden mit erfasst.

Ehrlicher Schuldenpunkt: Es gibt noch doppelte Zuständigkeiten. Ein Beispiel sind mehrere gewachsene Freigabe-Wege, die sich nicht gegenseitig kennen.

## Repo-Hinweise

- Einstieg ins Verständnis: `BETRIEBSHANDBUCH.md` und `BETRIEBSHANDBUCH/` (Kapitel 1 bis 283).
- Einstiegspunkte im Code: `jack_mcp_server.py` (MCP für externe KIs), `jack_mission_runner.py` (Acts), `jack_autonomous.py` (Wächter), `jack_chat_router.py` (Gespräch), `jack_ui_agent.py` (Xiaomi-Bedienung).
- Bewusst nicht im Repo: Datenbanken, Logs, Telemetrie, `ARBEITSPLATZ/`, Arena-Inhalte (Aufgaben, Oracle, Holdouts), Token und Schlüssel.
- **CI**: `.github/workflows/tests.yml` läuft bei jedem Push, steht aber auf `continue-on-error: true`. Testfehler blockieren derzeit nichts, **CI ist also noch kein hartes Quality Gate**.

## Selftest

```
python3 jack_selftest.py
python3 jack_whitelist_guard.py
```

## Wie hier gearbeitet wird

Erst messen, dann ändern. Die Temperatur geht vor, ein Patch kann warten. Vor jeder Änderung steht ein Backup, Gelöschtes landet im Attic. Werkzeuge bleiben eng benannt und auf einen Zweck zugeschnitten. Ein Act, der genau eine Sache tut und das beweisen kann, ist mehr wert als einer, der vieles könnte.
