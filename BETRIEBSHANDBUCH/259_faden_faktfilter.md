# 259 Gespraechsfaden + Fakten-Filter (09.10.2026)

## Faden (jack_talk.py, JACK_TUNE_FADEN)
- Fenster existierte (add_to_window, reports/talk_window.jsonl, 8 Eintraege), aber Antworten >400 Zeichen wurden komplett verworfen und der Rest auf 220 Zeichen gekuerzt. Folge: "Nein da oben" / "Und dann einfachen Worten" fand nach langen Antworten nichts.
- Jetzt: Grenze 3000 Zeichen, gespeichert 240 (Dima) / 700 (Jack), Prompt-Budget 2400 Fenster / 2800 gesamt. Slash-Befehle, Kiste, Mission-Meldungen bleiben draussen.

## Fakten-Filter (jack_chat_router.py, JACK_TUNE_FAKTFILTER)
- Ursache der Junk-Fakten: Block JACK_TUNE_EDGE_FREE schnitt bei "ich bin/habe/meine X ist Y" willkuerlich Woerter 2-4 als Name aus (aus "meine Decke ist weiss" wurde fakt:ist_wei=ja).
- Jetzt: nur noch "mein(e) X ist/heisst Y", ohne Fragezeichen und Komma, Name max 3 Woerter. "ich bin/habe/mag" erzeugt keinen Fakt mehr (dafuer gibt es "merk dir").
- Aufgeraeumt: fakt:ist_wei, fakt:dir_ein auf typ=fakt_verworfen (nicht geloescht, Eintrag in korrekturen). fakt:decke=weiss bleibt.

## Offen
- Live-Test von Dima: langes Thema, dann "Nein da oben".
- put_node ueberschreibt gleichnamige Fakten (neueste Aussage gewinnt).
