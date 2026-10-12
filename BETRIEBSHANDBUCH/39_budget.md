# 39. jack_budget.py

Gelesen 03.10.2026, erste 36 Zeilen. Kein Umbau.

**Grenzen:** text 600 (seit 11.10.2026 auf Dimas Wunsch, vorher 300), vision 40 pro Tag. Wochengrenze 3 EUR bleibt der eigentliche Kostendeckel. Aenderung wirkt in laufenden Diensten erst nach Neustart (LIMITS wird beim Import gelesen). Woche 3.0 Euro, 0.40 Euro pro Million Tokens. Dateien .api_budget und .api_budget_week.

**Funktionen:** week_ok, check_and_count. Tageszaehler setzt sich um Mitternacht zurueck.

## Nachtrag 12.10.2026 (JACK_TUNE_BUDGETEUR)
- Problem: Wochenschaetzung rechnete alle Tokens mit 0.40 EUR/Mio. Nach den Arena-Laeufen stand die Woche nach wenigen Stunden bei 2.45 von 3 EUR, echt ausgegeben waren 0.66 EUR. Volles Wochenlimit sperrt auch JACKs eigenes Gemini.
- Fix: add_tokens(n, eur=None). Kennt der Aufrufer die echten Kosten (Arena-Runner, Lerner), wird genau dieser Betrag addiert, sonst wie bisher die Schaetzung 0.40 EUR/Mio (jack_gemini_bridge, jack_vision). Wochen-EUR wird jetzt aufsummiert statt aus der Tokenzahl neu berechnet.
- Woche W42 einmalig korrigiert: 2.45 -> 0.66 EUR (alle Tokens der Woche waren Arena, echte Kosten aus costs.jsonl). Feld korrigiert in .api_budget_week.
- Neu geladen: jack_telegram, jack_cortex, jack_autolearn, jack_waechter, jack_publisher, jack_focus_monitor. jack_missions NICHT per Auftrag (Kap 275), Dima startet in Termux neu; bis dahin kann dessen alter Code bei einem Gemini-Aufruf die Woche wieder aus der Tokenzahl berechnen.

## Nachtrag 11.10.2026
- LIMITS text 1000/Tag (Dima, vorher 600, davor 300), vision 40, Wochendeckel 3 EUR unveraendert. Wirksam fuer Prozesse nach Neustart (Import-Zeit).
