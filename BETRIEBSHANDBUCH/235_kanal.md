# 235. jack_kanal.py

Angelegt 07.10.2026 (Marker JACK_TUNE_KANAL). Baut auf Kapitel 234 (Arbeitsplatz) auf.

**Zweck:** Asynchroner Briefkasten zwischen Claude, Grok, Gemini und Dima plus Reservierung von Modulen. Kein Live-Kanal: jede KI holt Post bei ihrem naechsten Zug.

**MCP-Tools (jack_mcp_server.py):** `ap_post(wer, an, typ, text, re_id)`, `ap_lese(wer, seit_id=-1)`, `ap_claim(wer, ziel, aktion)`. `start_hier(wer)` nennt die Anzahl ungelesener Nachrichten.

**Dateien:** ARBEITSPLATZ/gemeinsam/kanal.jsonl (eine Zeile pro Nachricht: id, ts, von, an, typ, re, text), claims.json, BUEROS/<wer>/kanal_cursor.json (bis wohin gelesen).

**Typen:** frage, aufgabe, antwort, info, entscheidung (nur Claude oder Dima), fertig.

**Schutz:** Rundengrenze = 10 KI-Nachrichten in Folge ohne Wort von Dima, danach Ablehnung bis Dima schreibt. Notaus: Datei missions/STOP verbietet jeden Post. Text max 2000 Zeichen. Claims laufen nach 60 Minuten ab, fremde Claims blockieren (nicht anfassen, im Kanal fragen).

**Ablauf einer Zusammenarbeit:** Claude postet typ=aufgabe an grok mit klaren Grenzen. Grok ruft ap_lese, reserviert das Modul per ap_claim, arbeitet (Handbuch-Kapitel und Gate wie immer), meldet typ=fertig mit Beleg (sv_ok, Pruefung), gibt den Claim frei. Claude prueft gegen die Live-Datei. Risiko oder Unklarheit: typ=frage an dima.

**Grenzen:** Kein Dauerprozess. Gleichzeitig denken geht erst mit dem autonomen Loop (noch ohne Go).
