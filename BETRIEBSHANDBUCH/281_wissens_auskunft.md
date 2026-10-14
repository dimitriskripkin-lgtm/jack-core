# 281 Wissens-Auskunft (jack_wissen.py)

Stand 14.10.2026, MODULE_VERSION 2 (JACK_TUNE_WISSEN2). Status: gebaut, NICHT live. Schalter ~/jack/.wissen_off ist gesetzt (= alter Arm). Router-Haken JACK_TUNE_WISSEN (classify + neu_antwort) sind drin, wirken nur ohne die Datei.

## Was es tut
Deterministisch, kein LLM. Wissensfragen ueber JACK ("Was weisst du ueber X", "Wie funktioniert X", "Was ist X") -> woertlicher Auszug aus dem Betriebshandbuch plus Kapitelnummer. Kein Treffer bei starkem Ausloeser und JACK-Bezug -> "Dazu steht nichts im Handbuch."

## JACK-Bezug-Gate (v2, vor der Suche)
- A explizit: jack/jacks, dein/deine/deinem/deinen/deiner/deines, "bei dir"/"von dir". Mit A wirkt auch "was ist ..." wie ein starker Ausloeser.
- B Entitaet: JACK-Eigenname (haliza, kortex, cortex, overmind, selbstmodell, autolearn, xibreaker) oder zwei aufeinanderfolgende Fragewoerter = Wortpaar aus Kapitel- oder Modulnamen (z. B. "cmd handler", "git publish").
- Mehrdeutige Einzelwoerter (Router, Fokus, Graph, Publisher, Budget, Deadman, Hitzeschutz) oeffnen das Gate nie allein.
- Ohne Bezug -> None (alter Weg). Unbestimmter Artikel / "eigentlich" -> nie die Nichts-Antwort.
- Synonyme nur fuer die Suche: hitzeschutz/ueberhitzung->heat, fokus->focus, totmannschalter/totmann->deadman, kortex->cortex.

## Messungen (talk_vorregistrierung.md)
- v1 Holdout 12.10.: Rang1 18/20, Rang2 19/20, woertlich 20/20, unbeantwortbar 10/10. Aber Kontrolle2 1/20 und Kontrolle3 7/20 Fehlalarme -> Gate verfehlt.
- v2 14.10. (einmal): Kontrolle4 (24 Fangfragen von ChatGPT) 0/24 Fehlalarme. Kontrolle/2/3 je 0/20. Holdout2: Rang1 13/20, Rang2 13/20 (Ziel 16 -> VERFEHLT), woertlich 14/14, unbeantwortbar 10/10. JACK-Themen ohne Bezug: 0/6 beantwortet (gewollt).

## Restfehler v2
- Ausloeser fehlen: "wie steuert", "wie erkennt", "wie funktionieren" (Mehrzahl), "wie laufen".
- Bezug fehlt bei Schreibvarianten: "Fakten-Filter" vs Kapitel "faktfilter", "Stufe 1" vs "stufe1".
- Falsches Kapitel: "Talk-Modul" -> 279_talk_probe statt 04_talk.
- Viele Kapitel sind nur Stubs (Handbuch-Luecke).

## Naechster Schritt
Runde 3: Ausloeser-Liste erweitern (Mehrzahl + Verben), Wortpaar-Vergleich auch zusammengeschrieben, neuer frischer Holdout + neue Kontrolle. Aktivieren erst nach bestandenem Gate: rm ~/jack/.wissen_off, sv_restart jack_telegram.
