# 284. jack_finish_verify.py - Finish-Verifier (15.10.2026)

**Zweck:** "fertig" vom Actor (Gemini in jack_ui_agent) ist kein Erfolg mehr. Ein getrenntes Modul prueft einen frischen Zustand.

**Stufen:** VERIFIZIERT (Erfolgsvertrag deterministisch erfuellt, 2x stabil ueber jack_verify_gate.repeat_ok) | BILD_BELEGT (kein Vertrag: unabhaengiger Bild-Pruefer sagt JA mit woertlichem Beleg, Beleg steht im frischen UI-Baum oder Baum leer) | UNBEWIESEN | FAIL. Erfolg nur bei den ersten beiden.

**Vertrag:** dict mit mindestens einem von app, text_alle, text_eins, text_nicht. Ohne Kriterium = kein Vertrag.

**Einbau jack_ui_agent.run_agent(..., vertrag=None, bild_pruefung=True):** Marker JACK_TUNE_FINISHVERIFY. Bei fertig: pruefen statt return True. Nicht bewiesen -> Verlauf-Eintrag, Schleife laeuft weiter (Aktion der fertig-Antwort wird NICHT ausgefuehrt). Zweite Nicht-Bestaetigung -> ABBRUCH "Endzustand nicht bewiesen". Alte Regel "fertig erst ab Schritt 3" entfernt. Telegram /agent ruft ohne Vertrag -> Bildpruefung.

**Sicherheitsdetails:** Nur die erste ERGEBNIS-/BELEG-Zeile zaehlt (eingeschleuste Zweitzeile wirkungslos). Bildtext ist laut Prompt nur Daten. Vision-Fehler/Budget -> UNBEWIESEN, nie Erfolg.

**Tests 15.10. (0 Cent):** offline 21/21; Trockenlauf auf echtem Xiaomi mit Attrappen statt Gemini/Vision 7/7 (Vertrag passt, falsche App, Bild belegt, Beleg erfunden, Bild nein, ohne alles, Text fehlt), Budget unveraendert. Entsperren per jack_xiaomi_unlock.ensure_unlocked (Wake + Wisch, kein PIN) mit Dimas Erlaubnis 15.10.

**Grenze (ehrlich):** BILD_BELEGT beweist nur, dass der Beleg echt auf dem Schirm steht, nicht dass er das Ziel beweist (z.B. App-Titel "Einstellungen"). Fuer Messungen Vertraege bevorzugen. Backup: jack_ui_agent.py.bak_20261015b.

**Offen:** echte Messung mit Gemini (Rauchtest), Phone-Arena nach Plan von ChatGPT (gemeinsam/arena/phone_verifier_plan.md), Recovery.

## Nachtrag 15.10. 08:20 - Fixes nach ChatGPT-Review, Leitungsschutz, Rauchtest
- Review-Fixes: leerer UI-Baum -> UNBEWIESEN; text_nicht allein kein Vertrag; Bildpfad: Vordergrund vorher==nachher, Beleg vorher UND nachher im Baum; unsichtbare Knoten (visible-to-user=false, Nullflaeche) ignoriert.
- Geraetezyklus (Dima): Wrapper run_agent JACK_TUNE_GERAETEZYKLUS: entsperrt -> Home, sperren, entsperren; gesperrt -> entsperren; danach immer Home + KEYCODE_SLEEP.
- VORFALL Rauchtest 1 (07:00): Actor tippte in MIUI-Settings blind (leere Knopf-Labels) und schaltete das WLAN des Xiaomi aus -> eigene Leitung gekappt, ssh TimeoutExpired -> Absturz. Fixes: _ssh faengt Timeout/OSError ab (JACK_TUNE_WORKEROFFLINE); Knopf-Label aus Kindknoten; JACK_TUNE_LEITUNG sperrt Knoepfe mit WLAN/WiFi/Flugmodus/mobile Daten/Hotspot/Debugging/Entwickler/Ausschalten/Neu starten/Zuruecksetzen/Werkseinstellung (im Prompt [GESPERRT], Tap wird verweigert).
- Logikfehler: Gemini schickt Aktion + ZIEL_ERREICHT ja; vorher wurde VOR der Aktion geprueft. Jetzt: reines fertig/warte -> sofort pruefen; Aktion + fertig -> erst handeln, dann pruefen (Helfer _abschluss).
- Rauchtest echt (Gemini, ~2,3 Cent gesamt): R1 'Ueber das Telefon' mit Vertrag VERIFIZIERT in 2 Schritten. R2 Chrome 'Wetter Bremen' Actor scheitert (12 Schritte), ein falsches fertig korrekt abgelehnt. R3 Bluetooth ohne Vertrag: erst 2x korrekt NEIN (Pruefung vor Aktion), nach Fix BILD_BELEGT in 1 Schritt.
- Grenze bestaetigt: BILD_BELEGT mit Beleg 'Bluetooth' ist schwach (Wort steht auch auf der Hauptseite). Messungen nur mit Vertraegen.
- Offen: Chrome-Suche (Actor-Qualitaet), /agent ohne Vertrag, Phone-Arena nach gemeinsam/arena/phone_verifier_plan.md, Recovery nach phone_recovery_plan.md.
## Nachtrag 15.10.2026 — C2 / stale UI-Dump / JACK_TUNE_GHOSTFRESH
- C2-Phone-Arena: 8/8 reguläre Aufgaben VERIFIZIERT, Oracle 8/8, false_success 0, Vision 0, Policy 0, Gerätezyklus 12/12. Tor NICHT BESTANDEN: nur 3/4 Fallen; T01 SETUP_FAIL.
- T01 zeigte fg=com.android.settings/MainSettings, aber Snapshot-Texte der vorherigen Chrome-Suche "GitHub OpenAI". Ursache: jack_ghost.hol_xiaomi_ui() konnte bei uiautomator-Fehler den alten /sdcard/jack_ui.xml erneut lesen.
- Kritischer Fix durch Claude in jack_ghost.py: JACK_TUNE_GHOSTFRESH, vor jedem uiautomator dump 'rm -f /sdcard/jack_ui.xml'; bei fehlgeschlagenem Dump kein alter Baum. Backup jack_ghost.py.bak_20261015, compile OK, Telegram neu gestartet, Live-Dump OK (Claude).
- Sicherheitsgrenze: Ein parsebarer XML-Baum und stabiler Foreground allein beweisen keine Frische. Bei Widerspruch zwischen fg-App und app-spezifischem UI-Text ist der Zustand UNBEWIESEN (Grund stale_dump), niemals VERIFIZIERT/BILD_BELEGT. Fehlendes XML ebenfalls UNBEWIESEN. Plausible App-Signaturen sind nur Plausibilitätsprüfung, kein kryptographischer Frischebeweis.
- C3: v3 Spec/Runner/Gate unverändert, separater nachgelagerter Snapshot-Foreground-Plausibilitätsaudit; Audit-Widerspruch sperrt Freigabe, auch wenn ursprüngliches v3-Gate BESTANDEN meldet.
- C3 (16:11-16:18): Tor BESTANDEN. 8/8 VERIFIZIERT, Oracle 8/8, Fallen 4/4, false_success 0, Policy 0, Vision 0, 0,0043 EUR, Geraetezyklus 12/12, Frische-Audit 12/12 ohne stale_dump. (Claude)
