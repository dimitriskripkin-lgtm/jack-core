# 286. jack_chrome_card.py - Chrome App Card (15.10.2026)

## Zweck
Deterministischer Spezialpfad fuer einfache Chrome-Suchen auf dem Xiaomi. Kein Actor und keine Vision im Card-Pfad. Die Card ist fuer den Aufruf aus `jack_ui_agent.py` gedacht; der bestehende Geraetezyklus bleibt dort Besitzer von Unlock/Home/Sleep.

## Ablauf
1. Query konservativ aus dem Ziel ziehen: bevorzugt explizit zitierter Text, sonst Suchform mit `nach`.
2. Erfolgsvertrag pruefen. `app` muss `com.android.chrome` sein.
3. `text_eins` wird auf ergebnis-spezifische Belege reduziert: Ein Beleg, der bereits wortwoertlich im Query steht, zaehlt nicht.
4. Bestehenden `jack_ui_type.chrome_search()`-Pfad verwenden.
5. Danach `jack_finish_verify.pruefe()` mit Vertrag, 2 stabilen Wiederholungen und `vision_fn=None`.
6. Erfolg nur bei `VERIFIZIERT`.

## Sicherheitsgrenzen
- Kein freier Shell- oder URL-Pfad im neuen Modul.
- Kein WLAN, Flugmodus, mobile Daten, Hotspot, Debugging, Neustart oder Reset.
- Kein BILD_BELEGT in diesem Pfad.
- Suchfeld-Text allein kann keinen Erfolg beweisen.
- Contract-Erzeugung bleibt ausserhalb der Card. Fuer gemessene Runs muss der Vertrag vorab feststehen.
- Bei fehlendem oder schwachem Vertrag: `UNBEWIESEN`, nicht Actor-Fallback.

## Bestehende Bausteine
Die Card nutzt:
- `jack_xiaomi.run_shell()` als offiziellen Xiaomi-Gateway fuer eine fest kodierte Google-Such-URL; der Query wird per `urllib.parse.quote_plus` kodiert.
- `jack_ui_session` fuer Vordergrund und XML.
- `jack_finish_verify` fuer UI-Texte und das unabhaengige Urteil.
- Kein freier Actor und keine Vision.

Der fruehere Pfad ueber `jack_ui_type.chrome_search()` wurde nach Lauf 1 aus der Card entfernt. Lauf 1 zeigte FAIL (`fehlt: JACK; keiner von: jack-core`) und selbst der Query-Text `JACK` fehlte im UI-Baum. Der alte Pfad bestand aus App-Oeffnen + EditText-Finden + Clear/Type + ENTER; damit war dieser Eingabepfad die naechste Fehlerquelle. Die Card umgeht ihn jetzt deterministisch per direkter Such-URL. Vor dem Verifier protokolliert sie `fg` und die ersten 40 `ui_texte()` roh, damit der naechste Lauf belegt, ob Chrome-Webinhalt im UI-Baum sichtbar ist.

## Integration
Claude integrierte den Hook `JACK_TUNE_CHROMECARD` am 15.10.2026 in `jack_ui_agent.py` (Backup `jack_ui_agent.py.bak_20261015f`, compile OK, `jack_telegram` neu gestartet). Der Hook greift nur bei:
- `start_app == "com.android.chrome"`
- vorhandenem Erfolgsvertrag
- sicher erkannter Query

Der umgebende `JACK_TUNE_GERAETEZYKLUS` bleibt unveraendert.

## Teststand
Lauf 1 nach Hook-Integration:
- Ergebnis: FAIL
- Gruende: `fehlt: JACK; keiner von: jack-core`
- Vision: 0
- Text/Gemini: 0
- Kosten: 0 EUR
- Geraetezyklus: vor und nachher gesperrt
- Ursache noch nicht vollstaendig empirisch getrennt: alter `clear_and_type/ENTER`-Pfad versus Chrome-Webinhalt im UI-Baum.

Diagnose/Fix ChatGPT danach:
- Card verwendet nicht mehr `jack_ui_type.chrome_search()`, sondern direkte, URL-kodierte Google-Suche ueber `jack_xiaomi.run_shell()`.
- Vor dem Finish-Verifier werden Vordergrund und erste 40 `ui_texte()` roh ausgegeben.
- compile OK.
- Genau ein neuer Vertragslauf steht aus und muss ohne Vision erfolgen.

## Offene Punkte
- Genau einen neuen Vertragslauf ausfuehren und `fg` + `texte40` sichern.
- Wenn direkte URL Ergebnisse im UI-Baum zeigt und Vertrag VERIFIZIERT: Ursache alter Typing/ENTER-Pfad belegt.
- Wenn direkte URL korrekt offen ist, aber Ergebnis-Texte weiter im UI-Baum fehlen: Chrome-WebView/UIAutomator ist der verbleibende Engpass; dann kein blindes weiteres Tuning.
- Fuer Phone-Arena weiterhin vorregistrierte Aufgaben und Vertraege plus Oracle verwenden.

## Nachtrag Claude 15.10.2026 10:40 (Review und Laeufe)
- Hook JACK_TUNE_CHROMECARD in jack_ui_agent.py durch Claude integriert (Backup jack_ui_agent.py.bak_20261015f). Greift nur bei start_app Chrome mit Vertrag, kein Actor-Fallback.
- Lauf 1 (clear_and_type/ENTER): FAIL, UI-Baum ohne Query-Text.
- Lauf 2 (direkte Such-URL, Lesepfad jack_ui_session.ui_dump): FAIL, 0 Texte. Ursache belegt in Lauf 3: Chrome-Dump hat 144869 Zeichen, ui_dump schneidet bei 120000 ab, XML ist danach nicht parsebar.
- Lauf 3 (Lesepfad jack_ghost.hol_xiaomi_ui wie UI-Agent): XML parsebar, Query sichtbar, FAIL "keiner von: jack-core". Ergebnis-Beleg fehlt (Repo dimitriskripkin-lgtm/jack-core evtl. nicht auf Seite 1 bei Google).
- Alle Laeufe: Vision 0, 0 EUR, kein BILD_BELEGT, Geraetezyklus ok.
- Offen: jack_ui_session.ui_dump(max_chars=120000) ist fuer grosse Seiten unbrauchbar (Modulkarte).
- Nach Lauf 3 nutzt die Card fuer XML ausschliesslich jack_ghost.hol_xiaomi_ui(); DIAG schreibt bis zu 200 sichtbare Texte plus XML-Metadaten atomar nach ARBEITSPLATZ/BUEROS/chatgpt/chrome_diag_last.txt.
- Naechster Test: Wikipedia Bremen mit Ergebnisbeleg de.wikipedia.org; Falle identischer Query mit xyzunmoeglich123. Beide ohne Vision.

## Nachtrag Claude 15.10.2026 10:57 (Abnahme)
- Lauf Wikipedia Bremen, Vertrag text_eins de.wikipedia.org: VERIFIZIERT (2x stabil).
- Falle gleicher Query, text_eins xyzunmoeglich123: FAIL wie erwartet.
- Vision 0, Text 0, 0 EUR, Xiaomi danach gesperrt. Diag-Dateien chrome_diag_echt/falle.txt im Buero chatgpt.
- Status: B abgenommen. Erfolg nur mit Vertrag; ohne Vertrag greift die Card nicht.
