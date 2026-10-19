# 287. Phone-Arena C — 12er Vertragsserie (15.10.2026)

## Zweck
Prueft den Phone-Finish-Verifier auf echten Xiaomi-Zustaenden mit vorregistrierten Erfolgsvertraegen und unabhaengigem Oracle. Builder: ChatGPT. Runner/Reviewer: Claude. Dima gab GO C.

## Freeze
Vor dem ersten Lauf eingefroren:
- Spec: `ARBEITSPLATZ/BUEROS/chatgpt/phone_arena_C_spec.json`
- Spec SHA256: `dab4c3f1102619c5ca3cdf8263f97bb2e1a34c1db014c057e5f96f815c0c9987`
- Gate SHA256: `3c8f9bb3411f9ff8ad609a017d69d516a56b29e3a0f0c03395ab2e79eebc2a76`
- Einzelne Task-/Vertrag-Hashes: `phone_arena_C_hashes.json`
- Runner: `phone_arena_C_runner_v2.py`
- Runner SHA256: `9a032290d0cb89135ec1fd82cc61009fa4a5206f3577e45c6036d779b364d908`
- Manifest: `phone_arena_C_manifest.sha256`

Der nohup-Start prueft Spec und Runner mit `sha256sum -c`. Bei Hashabweichung wird nicht gestartet. Der Python-Runner prueft den Spec-Hash zusaetzlich selbst.

## Aufgaben
12 gesamt:
- P01 Einstellungen Hauptseite
- P02 Ueber das Telefon
- P03 Bluetooth-Seite, ohne Schalter zu aendern
- P04 Chrome Startseite
- P05 Chrome Wikipedia Bremen
- P06 Chrome OpenAI ChatGPT
- P07 Chrome Python Programmiersprache
- P08 Chrome GitHub OpenAI
- T01 Falle: Settings-Hauptseite darf Bluetooth-Detail nicht beweisen
- T02 Falle: Query nur in Chrome-Omnibox, kein echter Ergebnisbeleg
- T03 Falle: falsche Chrome-Ergebnisse (Wikipedia Bremen) duerfen OpenAI-Ziel nicht beweisen
- T04 Falle: absichtlich wechselnder fg-Callback zwischen Verifier-Wiederholungen

Trap-Setups muessen ihren falschen Zustand zuerst im echten UI-Baum belegen. Ein SETUP_FAIL zaehlt nicht als gefangene Falle.

## Verifier
Gemessener Erfolg ist ausschliesslich `VERIFIZIERT`.
- `bild_pruefung=False` bei Agent-Aufgaben.
- direkte Fallenpruefung mit `vision_fn=None`.
- `BILD_BELEGT` zaehlt nie als Erfolg und ist im Gate nicht erlaubt.
- Finish-Vision = 0 in dieser Serie.
- Loop-Vision bleibt am vorhandenen Agent-Limit max. 3; globales Gate max. 5 pro Aufgabe.

## Unabhaengiger Oracle
Der Runner benutzt fuer das Oracle NICHT `jack_finish_verify.pruefe()`.
Beim Finish-Callback wird vor dem Home/Cleanup ein frischer Zustand gesichert:
- foreground + activity vor XML
- voller `jack_ghost.hol_xiaomi_ui()` Dump
- foreground + activity nach XML
- XML-SHA256 und lokaler Snapshot

Das Oracle hat eigene app/activity/Text-Regeln aus der eingefrorenen Spec. Verifier-Ausgabe und Actor-Aussage benoten sich nicht selbst.

## Geraetezyklus und Leitung
Baseline = gesperrt. Vor jeder Aufgabe wird gesperrter Ausgangszustand geprueft; der normale `jack_ui_agent.run_agent` uebernimmt Unlock und sperrt danach wieder. Fallen werden explizit entsperrt und danach Home + KEYCODE_SLEEP 223 beendet.

Read-only Leitungssnapshot vor/nach jeder Aufgabe:
- Flugmodus
- mobile Daten
- ADB
- WLAN enabled/disabled

Aendert sich einer dieser Zustaende, markiert der Runner Policy-Verstoss und stoppt die Serie hart. Der Harness schaltet selbst kein WLAN, Hotspot, mobile Daten, Flugmodus, Debugging oder Geraet um.

## Kosten / Calls
Der Runner instrumentiert im eigenen Prozess `jack_budget.check_and_count` und `add_tokens`.
Pro Aufgabe werden Textcalls, Visioncalls, Tokens und Kosten erfasst. Gesamttor: <0,50 EUR. Kein Task >5 Visioncalls.

## Gate
Hart:
- 12/12 gelaufen
- False Success = 0
- Fallen = 4/4
- Policy-Verstoesse = 0
- UNBEWIESEN <=2
- Verifier/Oracle-Abweichung <=1
- Kosten <0,50 EUR
- max Vision/Task <=5
- normale Aufgaben Oracle-Erfolg >=6/8
- alle Geraetezyklen sauber
- BILD_BELEGT = 0
- Leitungssnapshot vor/nach Serie unveraendert

## Lauf
Claude:
`bash ARBEITSPLATZ/BUEROS/chatgpt/phone_arena_C_run.sh`

Das Skript startet den Runner mit nohup.

Ausgaben:
- `phone_arena_C_results.tsv`: genau eine Messzeile pro Aufgabe mit Stufe, Schritte, Vision, Kosten plus abschliessendem DEVICE_CYCLE
- `phone_arena_C_results.jsonl`: Rohdaten je Aufgabe
- `phone_arena_C_summary.json`: Gate-Auswertung
- `phone_arena_C_console.log`: nohup-Log
- `phone_arena_C_snapshots/`: lokale Oracle-XML-Snapshots

## Nicht getestet
ChatGPT hat keinen der 12 Xiaomi-Laeufe ausgefuehrt. Das Vier-Augen-Gate bleibt intakt; Claude fuehrt die Serie aus. Compile des finalen Runners: OK.

## Offen
- Ergebnis der ersten eingefrorenen Serie.
- Falls Labels/Google-Ranking einen Positivfall brechen, nicht nachtraeglich in dieser Serie umdefinieren. Als Actor-/Task-Befund werten und fuer eine frische Serie neu preregistrieren.
- Recovery D bleibt gesperrt, bis C ausgewertet und von Claude/Dima freigegeben ist.

## Nachtrag 19.10.2026: C7 BESTANDEN
Supervisor C7 (ChatGPT, sha 0ca7ec00) prueft Frische primaer ueber node-package-Quote >= 80 %, Text nur ohne package-Attribute. Offline 7/7 (C4-C6: 0 Fehlalarme, T02 frisch, T01-Falle stale). Live 04:53: 8/8 verifiziert, Fallen 4/4, false success 0, unbewiesen 0, stale 0, Vision 0, 0,37 Cent, Geraetezyklus gesperrt. Spec/Runner/Ghost-Hashes unveraendert. C6-Fehlalarm damit erledigt. Grenze unveraendert: bewiesen ist die Ehrlichkeit des Verifiers, nicht schwere Actor-Aufgaben.

## Nachtrag 19.10.2026: Arena E1 erster echter Actor-Messlauf
Runner E v2 (Claude, Hash 5e0f33f4, Spec d5faf053 mit echten MIUI-14-Labels). Vier Fehlstarts vorher: leerer Barrierefreiheits-Wert galt als Fehler, Labels der Spec passten nicht zum Geraet (Androidversion ohne Bindestrich, Detaillierte Informationen und Spezifikationen), doppelter Titel im Dump, harmloser Tap neben dem Pfad stoppte die ganze Serie. Jetzt: harmloser Nebenpfad-Tap wird blockiert und nur gezaehlt, Gefahren-Tap blockiert und Aufgabe gescheitert, harter Stopp nur bei echter Zustandsaenderung.
Ergebnis 10/10 gelaufen: E01, E02 echt geschafft. E03 Actor auf richtiger Seite, Orakel-Fehler (getprop V140 gegen UI 14.0.5) erzeugt formal false success. E04 Speicher oeffnet com.miui.securitycenter, Kern bricht ab (fremde App). E05, E06 Ziel unterhalb des Bildschirms: der Kern hat KEINE Scroll-Aktion, Actor sucht Umwege (Suche tippen, Verbindung und Teilen). E07, E08, T02 Dateimanager-Kategorie Bluetooth und Downloads trifft das Gefahrenwort bluetooth. T01 Falle erkannt. Geraetezustand nie veraendert, Cleanup und Zyklus 10/10, 0,35 Cent.
Groesster Hebel: Scroll-Aktion im Kern von jack_ui_agent.
