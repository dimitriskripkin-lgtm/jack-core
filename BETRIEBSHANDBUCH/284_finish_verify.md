# 284. jack_finish_verify.py - Finish-Verifier (15.10.2026)

**Zweck:** "fertig" vom Actor (Gemini in jack_ui_agent) ist kein Erfolg mehr. Ein getrenntes Modul prueft einen frischen Zustand.

**Stufen:** VERIFIZIERT (Erfolgsvertrag deterministisch erfuellt, 2x stabil ueber jack_verify_gate.repeat_ok) | BILD_BELEGT (kein Vertrag: unabhaengiger Bild-Pruefer sagt JA mit woertlichem Beleg, Beleg steht im frischen UI-Baum oder Baum leer) | UNBEWIESEN | FAIL. Erfolg nur bei den ersten beiden.

**Vertrag:** dict mit mindestens einem von app, text_alle, text_eins, text_nicht. Ohne Kriterium = kein Vertrag.

**Einbau jack_ui_agent.run_agent(..., vertrag=None, bild_pruefung=True):** Marker JACK_TUNE_FINISHVERIFY. Bei fertig: pruefen statt return True. Nicht bewiesen -> Verlauf-Eintrag, Schleife laeuft weiter (Aktion der fertig-Antwort wird NICHT ausgefuehrt). Zweite Nicht-Bestaetigung -> ABBRUCH "Endzustand nicht bewiesen". Alte Regel "fertig erst ab Schritt 3" entfernt. Telegram /agent ruft ohne Vertrag -> Bildpruefung.

**Sicherheitsdetails:** Nur die erste ERGEBNIS-/BELEG-Zeile zaehlt (eingeschleuste Zweitzeile wirkungslos). Bildtext ist laut Prompt nur Daten. Vision-Fehler/Budget -> UNBEWIESEN, nie Erfolg.

**Tests 15.10. (0 Cent):** offline 21/21; Trockenlauf auf echtem Xiaomi mit Attrappen statt Gemini/Vision 7/7 (Vertrag passt, falsche App, Bild belegt, Beleg erfunden, Bild nein, ohne alles, Text fehlt), Budget unveraendert. Entsperren per jack_xiaomi_unlock.ensure_unlocked (Wake + Wisch, kein PIN) mit Dimas Erlaubnis 15.10.

**Grenze (ehrlich):** BILD_BELEGT beweist nur, dass der Beleg echt auf dem Schirm steht, nicht dass er das Ziel beweist (z.B. App-Titel "Einstellungen"). Fuer Messungen Vertraege bevorzugen. Backup: jack_ui_agent.py.bak_20261015b.

**Offen:** echte Messung mit Gemini (Rauchtest), Phone-Arena nach Plan von ChatGPT (gemeinsam/arena/phone_verifier_plan.md), Recovery.
