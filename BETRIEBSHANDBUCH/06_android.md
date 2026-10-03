## 6. jack_android.py (523 Zeilen, UI-Automatisierungs-Grundlage)

**Zweck:** Die tiefste Ebene der Bildschirmsteuerung. Primitive wie `tap`, `swipe`, `type_text`,
`get_ui_tree` (uiautomator-Dump), Screenshot+Bildanalyse — plus ein fertiger, zielgerichteter
autonomer Agent (`run(goal, ...)`), der mehrere Runden lang selbst entscheidet, was zu tun ist.

**Nur von `jack_telegram.py` importiert**, und dort nur an **einer** Stelle genutzt: dem Befehl
`/vision <frage>` (Zeile ~685). Mit Frage ruft das `jack_android.run(frage, max_rounds=5)` auf —
den vollen autonomen Agenten. Ohne Frage nur `get_ui_tree()` zum Elemente-Zählen.

**Aufgelöster Verdacht aus Kapitel 2/README:** Die Stub-Befehle `/agent` und `/auto` ("Status: In
Entwicklung") sind **keine fehlende Fähigkeit** — die Fähigkeit existiert fertig und funktionsfähig
in `jack_android.run()`. Sie ist nur unter einem anderen Namen erreichbar (`/vision <frage>`), nicht
unter `/agent`. Reine Verdrahtungslücke, kein technisches Loch. Leicht behebbar, falls gewünscht:
`/agent <ziel>` könnte direkt `jack_android.run(ziel)` aufrufen statt der Platzhalter-Textantwort.

**`run(goal, app_package, app_activity, max_rounds=10)`** — die Kernschleife:
1. App starten (falls `app_package` angegeben), Popups wegklicken.
2. UI-Baum lesen (`get_ui_tree`), bei unverändertem Screen kurz warten und erneut lesen.
3. **Erst lokal suchen** (`find_element_smart`, reine Text-/Beschreibungs-Übereinstimmung) —
   **kein KI-Aufruf, wenn ein Treffer ohne Hilfe gefunden wird** (Kostenersparnis, bewusst
   kommentiert im Code: "kein API-Call wenn Treffer").
4. Nur wenn lokal nichts gefunden wird: `analyze_screen()` — vermutlich ein Vision-Modell-Aufruf
   (noch nicht im Detail geprüft, welches Modell).
5. `execute_action()` wertet das Ergebnis aus, prüft ob das Ziel erreicht ist, sonst nächste Runde.

**Weitere bemerkenswerte Bausteine:**
- `image_hash()` + `cleanup_screenshots(days=14)` — Screenshots werden gehasht (vermutlich um
  Duplikate zu erkennen) und nach 14 Tagen automatisch aufgeräumt.
- `add_som_markers()` — "SoM" vermutlich "Set-of-Marks", eine bekannte Technik, UI-Elemente im Bild
  nummeriert zu markieren, bevor sie an ein Vision-Modell gehen (Vermutung, nicht im Detail geprüft).
- `keycode()`/`keycode_suche()`/`syntax()`/`keyevent_sicher()` — Hilfsfunktionen rund um
  Android-Keyevents, inkl. Suche nach Keycode-Namen.

**Verhältnis zu den diese Woche gebauten Xiaomi-Acts (Kapitel 1):** `chrome_search_xiaomi` &Co.
sind eng geschriebene, einzelne Wrapper um `jack_ui_type`-Funktionen (feste Abläufe für genau eine
App). `jack_android.run()` ist generisch und zielgerichtet für **beliebige** Apps/Ziele — mächtiger,
aber auch unvorhersehbarer. Beide Systeme existieren nebeneinander, für unterschiedliche Zwecke;
keine Dopplung im problematischen Sinn, eher zwei Werkzeuge unterschiedlicher Präzision.

**Offene Fragen für später:** Welches Modell nutzt `analyze_screen()`? Ist `/vision` ohne erweiterte
Steuerung (z. B. Abbruch-Knopf) riskant, wenn `run()` zehn Runden lang eigenständig tippt? Sollte
`/agent` auf `jack_android.run()` umgebogen werden, oder bleibt die Trennung bewusst?
