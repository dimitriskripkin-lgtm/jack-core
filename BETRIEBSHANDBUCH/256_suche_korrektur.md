# 256 Suche und Korrektur (Telegram)

- /suche <Begriff>: jack_suche.py (JACK_TUNE_SUCHE). SQLite-FTS5-Index jack_suche.db (nicht im Repo, *.db ignoriert) ueber BETRIEBSHANDBUCH, ARBEITSPLATZ/gemeinsam, *.md, Missions-Logs, jack_decisions.log. Token-aehnliche Folgen werden zu [X], Dateien mit token/secret/passw im Namen uebersprungen. Kein LLM. Index wird bei Abfrage hoechstens stuendlich im Hintergrund aktualisiert. Neuaufbau: jack_suche.db loeschen.
- /korrigiere <alt> => <neu>: jack_korrektur.py (JACK_TUNE_KORREKTUR). Sucht genau einen Fakt-Knoten in jack_graph.db (bei mehreren: Liste, keine Aenderung). Der alte Wert wird in Tabelle korrekturen (node, alt, neu, ts, von) gesichert, der Knoten bekommt den neuen Wert (src=korrektur). Nichts wird geloescht. Geheimnis-Pruefung wie beim Speichern.
- Erster Einsatz 09.10.: Starlight auf PS5 -> Starfield auf PS5.
- Grenzen: jack_memory.db (Episoden) enthaelt den alten Text weiter. Der Graph ist die Wahrheit fuer Fakten. Die Suche indexiert seit 09.10. auch die Graph-Fakten (Quelle fakt, JACK_TUNE_SUCHEFAKT).
- BUG gefunden und gefixt 09.10. (JACK_TUNE_SEEDONCE): jack_graph._ensure_facts_230923() lief bei jedem Import und ueberschrieb die Fakten spiel (Starlight) und kaffee_nacht -> Korrekturen waren nach jedem Dienst-Neustart weg. Jetzt nur noch anlegen, wenn der Knoten fehlt. Nach dem Fix 'spiel' = Starfield auf PS5 bestaendig.
- Rueckgaengig: Zeile aus korrekturen lesen und mit /korrigiere zurueckschreiben.
- Menue: setMyCommands enthaelt suche und korrigiere.
