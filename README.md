> **KI-Session?** Zuerst [00_START_HIER.md](00_START_HIER.md) lesen und den aktuellen Gerätestand prüfen. GitHub ist ein Spiegel, der HONOR ist die operative Wahrheit.

# JACK — Just Autonomous Command Kit

**Your AI. Your devices. Your rules.**

*A personal, safety-first AI agent runtime built on Android phones — with persistent memory, verified actions and role-based MCP collaboration.*

JACK ist ein experimenteller persönlicher KI-Assistent, der nicht nur antwortet, sondern **Geräte beobachten, begrenzte Aufgaben planen und überprüfbare Aktionen ausführen** kann. Das Sprachmodell liefert Vorschläge und Sprache; **JACK behält die Kontrolle über Werkzeuge, Rechte, Ausführung und Erfolgskriterien**.

Entstanden ist das Projekt weitgehend im Alleingang: Dima, LKW-Fahrer und Autodidakt, hat JACK über Monate direkt auf einem Smartphone mit Termux entwickelt – unterstützt von mehreren KIs, aber ohne klassisches Entwicklungsteam.

> **Kontrolle-first statt Cloud-versprechen.** JACK läuft als Runtime auf eigener Hardware. Für Sprache, Planung oder Bildverstehen werden teilweise Cloud-Modelle eingesetzt. Offline-Betrieb aller Funktionen wird ausdrücklich **nicht** behauptet.

**Stand dieser Übersicht: 27. Oktober 2026.** Quelle: aktuelle Geräte-Dokumentation und überprüfte Betriebsabläufe. Der Code auf GitHub kann dem Live-Stand hinterherliegen.

## In 30 Sekunden

| Baustein | Aufgabe |
| --- | --- |
| **HONOR Magic8 Pro** | Hauptsystem: Termux, Dienste, Routing, Gedächtnis, Prüfungen, MCP und Freigaben |
| **Xiaomi 11T Pro** | Separates Android-Ausführungsgerät mit Root, SSH, Tasker und eingeschränkten Geräteskills |
| **MCP** | Definierte Werkzeuge und Rollen für die Zusammenarbeit mit externen KI-Assistenten |
| **Groq** | Gesprächsebene; keine freie Ausführung von Shell-Befehlen |
| **Gemini** | Technische Modellaufgaben und bei Bedarf visuelle Interpretation |
| **JACK selbst** | Missions- und Aktionskontrolle, Beobachtung, Verifikation, Gedächtnis und Sicherheitsgrenzen |

JACK ist **kein eigenes Foundation Model, keine AGI und kein Chatbot mit uneingeschränktem Terminalzugriff**.

## Was JACK heute tatsächlich kann

Die Beispiele unterscheiden bewusst zwischen **live eingesetzt**, **gezielt getestet** und **noch nicht vollständig integriert**.

### 1. Begrenzte Geräteaktionen statt blindem Modell-Output

JACK verarbeitet Absichten als Missionen mit **benannten, erlaubten Aktionen**. Die Runtime trennt Planung und Ausführung: Das Modell kann einen Befehl vorschlagen, führt ihn aber nicht selbst direkt im Betriebssystem aus.

Dazu gehören unter anderem Aktions-Whitelists, Freigabegrenzen, Ressourcenwachen, Ergebnisprüfungen und bei Codeänderungen definierte Patch- und Prüfschritte.

Bei Android-Aktionen gilt seit der Architekturentscheidung vom 21. Oktober: **Intent/Deep-Link zuerst, Shell wenn sinnvoll, UI-Automation zuletzt.** Ein einfacher Timer muss nicht durch eine simulierte Fingerreise durch Android-Einstellungen entstehen.

### 2. Zusammenarbeit mehrerer KIs über MCP

Externe KI-Assistenten können innerhalb **rollenabhängiger Rechte** Informationen aus JACK lesen, den echten Gerätestand prüfen und Ergebnisse in einem gemeinsamen Arbeitsplatz übergeben.

Der Unterschied zum klassischen „KI schreibt ein Skript“: Ein Assistent muss den Zustand nicht erraten; er kann die dafür freigegebenen Fakten und Dateien abfragen. Schreiben, Veröffentlichen und sensible Aktionen behalten eigene Grenzen und Freigaben. **MCP ist eine Schnittstelle, kein Freifahrtschein.**

### 3. Gespräch mit einem ehrlicheren Selbstbild

JACK besitzt eine getrennte Gesprächsebene und ein lokal erzeugtes **Selbstbild** aus technischen Messwerten, den jüngsten Handbuchkapiteln und dem bekannten Projektstand.

Ein konkreter Fehler vom 21. Oktober: JACK erfand zuvor Kapitelinhalte und schätzte Akkustände. Nach der Korrektur antwortete es bei der Frage nach Kapitel 295 anhand der tatsächlich vorhandenen Inhaltszeile. Die Regel lautet sinngemäß: **Was nicht im Selbstbild steht, weiß JACK über seinen aktuellen technischen Zustand nicht.**

Das ist keine Lösung aller Halluzinationen, sondern eine gezielte, überprüfte Verbesserung.

### 4. Telegram mit Fahrkontext

Ein gemeinsamer Sende-Helfer protokolliert Nachrichten mit **Quelle** und **Wichtigkeit**. Bei erkanntem LKW-Bluetooth kann JACK unwichtige Hinweise lokal zurückhalten; wichtige Alarme werden weiterhin gesendet.

Die Sammelmeldung wird nach **mindestens zwei Minuten bestätigter Trennung** und beim nächsten Wächterlauf ausgelöst. Der Wächter prüft ungefähr alle fünf Minuten; damit kann die Benachrichtigung nach dem Aussteigen mehrere Minuten brauchen.

**Status:** Am 21. Oktober auf dem HONOR integriert, 35/35 zugehörige Tests bestanden. Die erste komplette Fahrt als End-to-End-Feldtest war zum Dokumentationszeitpunkt noch offen. Die Pufferung ist kein Ersatz für sicherheitskritische Warnsysteme.

### 5. Tasker-Brücke mit Quittung

JACK kann auf dem Xiaomi freigegebene Tasker-Testaufgaben auslösen und deren Quittungsdateien abholen. Die dokumentierte Datei-Testaufgabe meldete nach etwa 1,5 Sekunden `DONE`; nicht freigegebene Aufgabennamen wurden abgelehnt.

**Grenze:** Die Tasker-Quittung bestätigt die Ausführung aus Tasker-Sicht. Ob die reale gewünschte Wirkung eingetreten ist, muss wo nötig unabhängig verifiziert werden. Die Brücke ist noch kein allgemeiner Hintergrunddienst oder unbegrenzter Act.

### 6. Erste alltagsnahe Skills

Für Timer und Mediensteuerung existieren direkte Android-Wege, die ohne visuelle UI-Automation auskommen. Timer konnten über einen Android-Intent gesetzt und anhand einer Benachrichtigung belegt werden; Medienbefehle prüfen den Zustand einer aktiven Sitzung.

**Grenzen:** Das Abbrechen eines Timers funktionierte auf MIUI nicht zuverlässig über den getesteten Intent. Medien-`play` kann nichts starten, wenn zwar Spotify geöffnet, aber noch keine Wiedergabe vorbereitet ist. Für Spotify gibt es inzwischen Telegram- und Sprachbefehle (siehe 7); Timer und allgemeine Medienbefehle per Telegram sind noch in Arbeit.


### 7. Spotify: Playlisten, Lieblinge und „Spiel X“

JACK spricht seit dem 26. Oktober direkt mit der **Spotify-Web-API** (eigene Entwickler-App, PKCE-Login, Token nur lokal).

- **Lesen:** Playlisten, mit Herz markierte Songs, Toplisten (vier Wochen, sechs Monate, Jahre), Hörverlauf alle 30 Minuten.
- **Automatische Playlist** „JACK – Lieblinge nach Hördauer“: Herz-Songs, oben am meisten gehört. Wird jede Nacht neu sortiert, zusammen mit einer Sicherung aller Playlisten.
- **„Spiel X“ per Telegram und Sprache:** JACK sucht den Titel, startet ihn auf dem HONOR und meldet „läuft“ **nur**, wenn Android die Wiedergabe tatsächlich bestätigt. Sonst sagt er ehrlich „nicht bestätigt“.
- Sortieren, Zurücksetzen und Neuaufbau von Playlisten nur mit **Bestätigungsknopf** (Einmal-Code, 10 Minuten gültig, nur Dimas Privatchat).

**Grenzen:** Spotify liefert keine Abspielzahlen, nur Ranglisten. Die Reihenfolge ist oben echt und unten geschätzt. Die Spracherkennung verhört Songtitel teils deutlich. Der ältere Xiaomi-UI-Weg existiert parallel noch und ist nicht zusammengelegt.

### 8. Ehrlichkeitsfilter für behauptete Taten

Am 26./27. Oktober behauptete JACK im Gesprächsmodus mehrfach Aktionen, die nie passiert waren (zum Beispiel „Track gestartet“). Seit dem 27. Oktober prüft ein **deterministischer Filter** jede Gesprächsantwort: Erfolgsbehauptungen ohne echten Aktionsbeleg werden ersetzt durch „Das habe ich hier nicht ausgeführt“. Fragen, Verneinungen, Hypothesen und historische Fakten bleiben stehen.

**Status:** Alle drei echten Feldfälle werden abgefangen. Es ist eine Heuristik, keine vollständige Lösung.

### 9. App-Sperrliste

Ein zentraler Wächter prüft vor jedem App-Start durch Planer und UI-Agenten eine private Sperrliste (Banking, Bezahlen und Ähnliches). Fehlt die Liste oder ist sie defekt, ist **alles gesperrt** (fail-closed). Noch nicht abgedeckt sind Tasker-Aufgaben und einige ältere Intent-Wege.

### 10. Im Aufbau: n8n als Werkzeugkasten

Seit dem 27. Oktober läuft ein selbst gehostetes **n8n** auf dem Xiaomi. Es ist nur lokal erreichbar und hat eine eigene Notbremse bei Hitze oder Absturzschleifen. Ziel: JACK bleibt die Urteilsschicht, n8n übernimmt Anbindungen wie den Kalender. **Status (27.10.):** erster Ende-zu-Ende-Ablauf nachgewiesen: Telegram-Knopf -> JACK -> n8n -> Google-Kalender, Termin unabhaengig im Kalender bestaetigt. Google-Freigabe noch im Testmodus (laeuft nach 7 Tagen ab).

## Architektur: Modell und Ausführung bleiben getrennt

```text
Mensch / Telegram / berechtigte MCP-Clients
                  |
               HONOR
     Gespräch · Missionen · Freigaben
       Memory · Regeln · Prüfung
                  |
          erlaubte Aktion
                  |
         HONOR oder XIAOMI
          Ausführung / Beobachtung
                  |
             Verifikation
                  |
          Ergebnis und Erfahrung
```

Der kanonische Kreislauf lautet:

`Intent → Mission → Plan → Capability → Execution → Observation → Verification → Result → Memory → Learning`

**Ein Modell darf denken und vorschlagen. JACK entscheidet anhand seiner Regeln und Rechte, was ausgeführt wird.** Dafür sind Groq und Gemini austauschbare Komponenten, während die Runtime die Kontrolle behält.

## Sicherheit durch überprüfbare Grenzen

- **Keine freie Shell aus Modelltext:** nur benannte und begrenzte Werkzeuge sowie Missions-Acts.
- **Freigaben:** Sensible Operationen und neue Fähigkeiten benötigen ausdrücklich erlaubte Wege.
- **Verifikation:** Ein ausgeführter Befehl ist noch kein belegter Missionserfolg.
- **Schutzschalter:** RAM, Temperatur, Laufzeit, Budget und Stop-Dateien begrenzen Last und Risiken.
- **Nicht vertrauenswürdige Eingaben:** UI-Texte, Webseiten, Logs und KI-Ausgaben sind Daten, keine Ausführungsanweisungen.
- **Privater Zustand:** Token, persönliche Datenbanken, Logs, Telemetrie und Arbeitsakten gehören nicht in das öffentliche Repository.

Diese Regeln reduzieren Risiken, stellen aber **keine formale Sicherheitszertifizierung** dar.

## Lernen: Ergebnisse müssen übertragbar sein

JACKs Arena vergleicht Änderungen gegen Baselines mit vorregistrierten Hypothesen, frischen Aufgaben, versiegelten Holdouts und Transferprüfungen.

Ein bewusst kritisches Beispiel vom 12. Oktober: JACKs erste selbst formulierte Arbeitsregel verbesserte die Ergebnisse auf dem frischen Testsatz und Holdout, verschlechterte aber die Leistung auf fremden Aufgaben. Deshalb blieb sie **Arena-intern**, statt in die produktive Runtime zu gelangen.

**Ein grüner Benchmark allein ist noch kein Lernen.** Die Arena ist ein Prüfwerkzeug, nicht das eigentliche Ziel. Aktuell steht wieder der Alltagsnutzen im Mittelpunkt.


## Wo die Grenzen heute liegen

| Thema | Aktueller Stand |
| --- | --- |
| **Live-Telefonat mit JACK** | Persönliches Hauptziel, aber noch keine nachgewiesene, durchgehend unterbrechbare Echtzeit-Sprachverbindung wie bei einem Telefonat. Schneller Telegram-Textchat ist dafür nicht derselbe Beleg. |
| **Cloud und Offline** | Runtime und Sicherheitskontrolle auf Android; Gespräch, Technik und Vision verwenden auch externe Modell-APIs. |
| **Lokale Sprachmodelle** | Ollama wurde als zu schwach eingestuft und gelöscht; der lokale Modell-Fallback ist derzeit nicht in Betrieb. |
| **UI-Automation** | Ergänzende Ausführungsmethode, nicht der Standardweg. Die unabhängige Abschlussprüfung ist noch nicht überall verifiziert. |
| **Fahrmodus** | Live eingebaut und mit 35/35 Tests geprüft. Die erste vollständige Fahrt als Feldtest war am 21. Oktober noch offen. |
| **Selbstverbesserung** | Geprüfte Experimente mit Freigabe, keine grenzenlose Selbstmodifikation. |
| **GitHub-CI** | Test-Workflow nutzt `continue-on-error: true`. Testfehler blockieren derzeit nicht zuverlässig. |
| **Produktstatus** | Persönlicher experimenteller Prototyp, keine fertige Endnutzer-App oder kommerziell unterstützte Plattform. |

## Was als Nächstes zählt

1. **Alltag statt Prüfstand:** Timer und Mediensteuerung über Telegram zuverlässig nutzbar machen.
2. **Fahrpraxis statt Simulation:** Puffern und Sammelmeldung nach einer echten Schicht beobachten.
3. **Natürliche Live-Sprache:** Aufnahme, Pausenerkennung, Reaktionszeit, Audioausgabe und Unterbrechungen als Gesamterlebnis messen, bevor Hardware gekauft wird.
4. **Echte Erledigung statt Erfolgssymbol:** Missions-Ergebnisse unabhängig bestätigen und Fehler sichtbar machen.
5. **Weniger Wartung:** JACK soll auch nach Tagen ohne Entwicklung verständlich bleiben und tatsächlich Arbeit abnehmen.

Das sind Entwicklungsrichtungen, keine zugesagten Liefertermine.

## Einstieg für Entwickler und KI-Assistenten

JACK ist **kein One-Click-Installer**. Ein eigener Betrieb benötigt passende Android-Geräte, Termux, Rechte, Konfiguration und private Zugangsdaten. Relevante Laufzeitdateien und Geheimnisse werden bewusst nicht veröffentlicht.

- [00_START_HIER.md](00_START_HIER.md) – Regeln und Einstieg für neue KI-Sessions.
- [BETRIEBSHANDBUCH.md](BETRIEBSHANDBUCH.md) und [BETRIEBSHANDBUCH/](BETRIEBSHANDBUCH/) – Modul-Dokumentation. Neuere Kapitel können dem öffentlichen GitHub-Spiegel voraus sein.
- `jack_mcp_server.py` – MCP-Schnittstelle.
- `jack_mission_runner.py` – kontrollierte Aktionsausführung.
- `jack_autonomous.py` – Wächter und wiederkehrende Arbeit.
- `jack_chat_router.py` – Gesprächsrouting.
- `jack_ui_agent.py` – experimentelle Android-UI-Aktionen.

Vorhandene gerätespezifische Selbstchecks auf einem passend eingerichteten System:

```bash
python3 jack_selftest.py
python3 jack_whitelist_guard.py
```

**Lizenz:** Derzeit ist keine ausdrückliche Open-Source-Lizenz angegeben. Öffentlich sichtbarer Code ist nicht automatisch zur Weiterverwendung lizenziert.

## Die Idee dahinter

JACK entstand auf einem Smartphone – weitgehend in Eigenarbeit, mit KI als Werkzeug und einem einzigen Daumen als Entwicklungsoberfläche. Die eigentliche Frage war nie nur, wie viele Befehle ein Assistent kennt.

**Kann ein einzelner Mensch mit KI ein System bauen, das verantwortlich handelt, ehrlich über seinen eigenen Zustand Auskunft gibt und ihm im Alltag spürbar Arbeit abnimmt?**

Darauf arbeitet JACK hin. Ohne AGI-Versprechen, ohne perfekte Benchmarks zu erfinden – und ohne aus dem Menschen den Wartungsdienst seiner eigenen Idee zu machen.

---

*JACK = Just Autonomous Command Kit · Android / Termux · Control-first · Evidence before claims · Built by Dima.*

*GitHub is the mirror. The device is the source of truth.*
