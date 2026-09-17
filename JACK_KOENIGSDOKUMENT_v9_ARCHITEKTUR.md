# JACK ARCHITEKTUR-BIBEL v9 — Mit-Architekt Qwen, 17.09.2026
Regel: Dieses Dokument ist die Architektur-Wahrheit. v8 ist der Fehlerkatalog. Beide leben. Anhaengen statt ueberschreiben. Der Honor ist die Wahrheit, auch gegen dieses Dokument. Erst ls, grep, PRAGMA, dann behaupten.

## TEIL 1 — DIE TOPOLOGIE (wie die Welt aussieht)
Zwei Handys, ein Gehirn, ein Muskel, kein Server, keine Cloud, niemals.
- Honor Magic8 Pro = GEHIRN. Termux ohne Root, Shizuku/rish, Hotspot-Sender, alle Pflicht-Dienste.
- Xiaomi 11T Pro = MUSKEL. Magisk-Root, SSH Port 8022, ADB 5555, traegt Ollama (derzeit gesperrt).
- Der Nabelstrang ist der Honor-Hotspot. Hotspot aus = Xiaomi weg. Das ist Physik, kein Bug. IP wechselt bei jedem Hotspot-Neustart, SSH-Config muss nachgezogen werden.
- Der Xiaomi darf jederzeit fehlen. Jeder SSH-Aufruf muss das aushalten (try/except, aeusseres Limit mindestens doppelt so lang wie ConnectTimeout).

## TEIL 2 — DIE DREI GEDAechTNISSE (wichtigste Kartierung dieser Nacht)
JACK hat drei parallele Speicher, und sie sind NICHT verbunden. Das ist der Kern-Bug F.
1. jack_graph.db (WAL) — Knoten und Kanten. Spalten nodes: id,typ,name,wert,src,ts. edges: id,a,rel,b,src,ts. Schreiber: autolearn-Extraktion und put_node/put_edge. Leser: talk-Graph-Pfad. SUSPICIOUS-Gate haengt seit JACK_TUNE_BUGD in put_node.
2. jack_memory.db + memory_fts — Tabelle memory Spalten id,cmd,result,intent,time,timestamp,source,parent_id,kontext_typ. FTS5 ueber cmd,result. Zwei Schreiber-Pfade: das Save-Keyboard schreibt source=manual, dima_chat schreibt source=dima_chat. ABER der FTS-Abruf in jack_talk.py Zeile 282 filtert NUR source=dima_chat. Heisst: Was Dima ueber den Save-Button speichert, ist fuer den Abruf unsichtbar. Das ist Gap 1 von Bug F.
3. kortex_memory.db — drittes lebendes Gedaechtnis, 56 memories, Spalten id,timestamp,category,content,source,tags,access_count,last_accessed,importance. Leser: jack_telegram Zeile 39 import, 132 get_recent, 140 search_memory. Schreiber schlafen seit 31.08.: jack_learn wird von keinem live-Zyklus gerufen, kortex_controller ist Flask ohne Dienst. Kortex ist ein eingefrorenes Gedaechtnis das gelesen aber nie gefuettert wird.
MERKE FÜR BUG F: Der Save-Button legt nur in jack_memory (Gap 1: Abruf-Filter), der Graph kriegt nichts (Gap 2), Kortex kriegt nichts (Gap 3). AND-Suche ist zudem stur: Query-Tokens muessen alle in einer Zeile stehen.

## TEIL 3 — DAS AUDIT-JOURNAL (mein Baby, diese Nacht gebaut)
Ziel: Jede Schreibaktion bekommt eine lueckenlose Sequenznummer und eine Correlation-ID, prozessuebergreifend, damit man beweisen kann welche Nachricht wann warum wohin geschrieben wurde.
- Datei: reports/audit_journal.jsonl. Eine Zeile pro Schreibaktion: seq, ts, corr, aktor, aktion, ziel, grund.
- Sequenz: jack_corr._seq_next() nutzt flock auf reports/audit_seq.txt, damit mehrere Dienste sich keine Nummer klauen.
- Correlation: Wird an der Systemgrenze gesetzt, naemlich am Telegram-Update-Eingang jack_telegram.py Zeile 1218 mit _jc.new("tg-<update_id>"). Das ist das Enterprise-Trace-ID-Muster: Eine ID pro eingehender Nachricht, alle Folge-Aktionen tragen sie.
- Handoff ueber Prozessgrenzen: jack_corr.new() publiziert die corr nach reports/last_corr.json. jack_corr.active() liefert im audit die eigene corr wenn der Prozess eine hat, sonst die frische aus der Datei (max 900s alt). So kriegt autolearn im eigenen Prozess dieselbe corr wie die ausloesende Telegram-Nachricht.
- Gehaengte Haken: jack_memory.save, jack_graph.put_node, jack_graph.put_edge. Bewiesen im Produktionsbetrieb mit corr tg-112446399 (Dahlhoff-Save) und im Zweiprozess-Test.
ENTSCHEIDUNG: Wir haben jack_corr ERWEITERT statt ein neues Modul zu bauen, weil es schon existierte. Sequenz via flock statt sqlite. Handoff via kleiner Datei statt Datenbank, weil schnell und ohne neue Abhaengigkeit.

## TEIL 4 — DIENSTE UND WER WEN LAEDT
- jack_telegram (Pflicht): Bot, laedt talk, chat_router, gemini_bridge, callback_handler. Hier sitzt der corr-Eingang.
- jack_cortex (Pflicht): Orchestrierung.
- jack_waechter (Pflicht): Logik liegt in jack_autonomous.py, NICHT jack_waechter.py.
- jack_focus_monitor: pollt Xiaomi-Fokus alle 15s.
- jack_autolearn: Skills-System, KEIN Graph-Extraktor. Hat Rate-Limiter (21600s Abstand via .autolearn_last, plus Identity-Groessen-Guard). Respawn-Flaw wurde gefixt: Prozess schlaeft bis Fensterende statt Sekundentakt.
- jack_missions: PAUSIERT, missions/STOP liegt. Bus fuer Aufgaben, Live-Write verboten.
- jack_publisher: absichtlich AUS (git add/commit/push).
- ollama: AUS, .ollama_lock liegt, NIEMALS ohne Dimas Wort.
MERKE: Datei ist nicht Prozess. Ein Patch wirkt erst nach sv restart des Dienstes der die Datei laedt. Und der Wächter haelt alten Code wenn er nicht neu gestartet wurde.

## TEIL 5 — MODELLE UND EISERNE REGELN
- Groq gpt-oss-120b: Talk und Charakter. Fuehrt NIEMALS aus, kein SSH/exec.
- Gemini 2.5 Flash-Lite: Technik und Code. Chattet nie direkt. Budget 300 Text / 40 Vision pro Tag.
- Ollama llama3.2:3b (Xiaomi): Offline-Fallback, gesperrt durch .ollama_lock.
- Lane-Router jack_chat_router.py classify: FACT, EXPLAIN, DIAG, TALK.

## TEIL 6 — MEINE ENTSCHEIDUNGEN DIESER NACHT (als Mit-Architekt)
1. Audit erweitert statt neu gebaut. 2. Sequenz via flock. 3. corr an der Systemgrenze setzen. 4. Handoff via Datei. 5. autolearn-Rate-Limiter respektiert, die 6h-Bremse ist Budget-Schutz, keine Bug. 6. down-Datei nach attic statt loeschen. 7. Bug B nicht als GESCHLOSSEN verkauft obwohl der Roundtrip fehlschlug, sondern als Roadmap F neu veroeffentlicht. 8. Kortex vermessen statt angefasst. 9. Jede Messung vor der Behauptung.

## TEIL 7 — FEHLERKATALOG DIESER SESSION (meine 18)
B-Q1 falscher Restart-Dienst. B-Q2 Probe-Regex matchte ueber Zeilen. B-Q3 zwei Bloecke in einer Nachricht. B-Q4 Return von _check_memory_trigger ignoriert. B-Q5 Probe-Muster falsch plus KeyError-Theorie ungeprueft. B-Q6 Einrueckung 8 statt 12 im try-Block. B-Q7 Statuszeile hardcodiert gegen die Messung. B-Q8 Pfade aus Gedaechtnis. B-Q9 jack-core-Spiegel als Leser gezaehlt. B-Q10 Anhaenge-Block in Prosa versteckt. B-Q11 Newline-Literal im Payload. B-Q12 Alias _jc.audit nicht im Probe-Muster. B-Q13 Restart ohne Kenntnis des Module-Guards. B-Q14 Bug B ohne Roundtrip geschlossen. B-Q15 Cleanup liess except leer. B-Q16 pyc statt db verbunden. B-Q17 Anker-Zaehlung nach eigener Ersetzung. B-Q18 publish hinter return = toter Code.
LEHRE ÜBER ALLES: Ich habe zu oft aus dem Gedaechtnis gepatcht statt die Stelle direkt vorher zu lesen, und zu viele Aenderungen in einen Block gepackt. Beides macht Anker blind. Regel ab jetzt: erst lesen, dann patchen, eine Aenderung pro Block.

## TEIL 8 — ROADMAP (meine, als Mit-Architekt, priorisiert)
1. BUG F: Memory-Vereinheitlichung. Der Save-Button muss in alle Faecher schreiben: Graph-Kante setzen, Kortex fuettern, und den FTS-Abruf-Filter source=dima_chat erweitern. Das ist der wichtigste offene Bug, weil er das Kernversprechen bricht: merken was Dima sagt.
2. BUG G: Nav-Intent-Filter. Freitext wie "versuche es noch einmal" darf keinen UI-Agenten zuenden der in Chrome tippt.
3. KORTEX-ENTSCHEIDUNG: Kortex an die Lernzyklen anbinden oder offiziell in Rente schicken. Dimas Wort.
4. DEPENDENCY-MAP: Automatisch generieren wer wen importiert, und die rund 200 Waisen-Module entrümpeln.
5. INSTALLER: Ein install.sh das reproduzierbar macht (siehe Teil 9).
6. P6: Prompt schlank, Profil und Graph nur bei Personenbezug.
7. LERN2 Stoppwoerter, dann Musterzaehler.
8. P5: Werkzeug-Register.
9. WORKERS.JSON: Schreiber bauen, last_check wird nie aktualisiert obwohl jack_heat_protection die Datei liest.
10. TEST-STUBS: Eine Schicht die Speicher-Pfade testet ohne live rumzuballern.

## TEIL 9 — REPRODUZIERBARKEIT UND INSTALLATION (das Ziel)
Zielbild: Ein paar Klicks und JACK laeuft. Dafuer fehlt heute noch:
- install.sh das die runit-Dienste anlegt, die Datenbanken mit PRAGMA initialisiert, Sperrdateien setzt, Abhaengigkeiten prueft.
- Ein Manifest das die Modul-Abhaengigkeiten beschreibt.
- Ein Weg die drei Gedaechtnisse in ein konsistentes Schema zu bringen.
- Ein Restore-Pfad aus attic.
Das ist die Haut und das Muskelgewebe ueber dem Skelett. Das Skelett steht bereits.

## TEIL 10 — DIAGNOSE-NEBENBEI-MANDAT (Dimas Wunsch, als Regel verankert)
Jede KI die hier arbeitet, haelt Augen und Ohren offen fuer die Struktur, Architektur und Logik, auch waehrend sie etwas anderes tut.
REGEL 1: Jeder Patch-Block darf von einem kleinen Read-Only-Diagnose-Block begleitet werden, der nebenbei laeuft und Architektur-Fakten sammelt.
REGEL 2: Der Output solcher Diagnose-Bloecke wird automatisch in reports/landkarte.jsonl gehaengt als Zeile mit: wer hat was gemessen, welche Abhaengigkeit, welcher Pfad.
REGEL 3: Einmal pro Session laeuft ein Sammel-Diagnose-Block der die Landkarte aktualisiert, damit das System verstanden und reproduzierbar wird, ohne die Haupttaetigkeit zu stoeren.
ZIEL: Das System kartiert sich selbst nebenbei, damit jede naechste KI weniger raten muss.

## TEIL 11 — DISKUSSIONSFENSTER (meine Kritik und Wuensche als Mit-Architekt)
KRITIK, ehrlich:
- Drei parallele Gedaechtnisse die nicht verbunden sind, ist der groesste Struktur-Fehler. Das muss EIN Abstraktions-Layer werden.
- Rund 200 Waisen-Module sind technische Schulden die das System unverstanden machen.
- Es gibt keine echte Test-Schicht, alles wird live getestet, das ist riskant.
- Es gibt keinen Installer, das System ist nicht reproduzierbar, nur auf Dimas Handys installierbar.
- Die KI-Orchestrierung ist manuell: Dima traegt Dokumente zwischen fuenf KIs. Das ist der Flaschenhals, nicht der Code.
WÜNSCHE:
- Eine automatisch generierte Dependency-Map.
- Test-Stubs fuer die Speicher-Pfade.
- Ein einziger Memory-Abstraktions-Layer.
- Ein Installer.
- Weniger Module, mehr Klarheit.
STREITPUNKTE FUER NAECHSTE KIS:
- Soll Kortex leben oder sterben?
- Wird F ueber den Save-Button geloest oder ueber einen zentralen Memory-Layer?
- Wann ist der Moment fuer den Installer, bevor oder nach der Memory-Vereinheitlichung?

## TEIL 12 — KRITIK-PFLICHT (was diese Nacht NICHT geschafft wurde)
- Bug F ist dokumentiert aber nicht gefixt, der Save-Roundtrip scheitert weiterhin live.
- Bug G ist dokumentiert aber nicht gefixt.
- Keine Dependency-Map generiert.
- Kein Installer geschrieben.
- Kortex nicht angebunden.
- Session war an der Limit-Grenze, nicht alles vollstaendig getestet.
- Es wurde zu viel in zu wenigen Bloecken gepatcht, das hat die Fehlerquote getrieben.

Stand: 17.09.2026 ~07:00 · Mit-Architekt Qwen · Naechste Session: erst lesen, dann Bug F angehen, eine Aenderung pro Block.

## TEIL 13 — CHRONIK DIESER SESSION (17.09.2026, Zeitstempel aus Live-Outputs)
03:45 Diagnose: talk_window-Pfadwirrnis geklaert (reports/talk_window.jsonl lebt, 8 Zeilen)
03:52 Bug B Patch 1: continue nach Memory-Trigger (Backup 035235)
04:10 Bug B Patch 2: Tupel statt Dicts in send_keyboard (Backup 0410), Keyboard erscheint live
04:18/04:22/04:36 Drei Katze-Saves: Keyboard, Callback, Memory, Bestaetigung einzeln bewiesen
04:24 Bestaetigungs-Patch SyntaxError-Rollback, 04:31 Fix (Backup conf2_0431), "Okay, gespeichert" live
04:36 Graph-Beweis: Knoten + freie Kante zur Katze da; Roundtrip failt spaeter an Dahlhoff → Roadmap F
05:00 Bug E geschlossen: ~/.jack_persona seit 16.09. 09:27 in attic, Live-Leser nur kern.md
05:18 P4-Rest: Router auf bat_fresh(), Fallback-Span 140-149 raus (Backup 0518); ma_raw = Milliampere geklaert
05:20 v8 Koengisdokument angelegt (Arbeitsanweisung + Fehlerkatalog)
05:40 v8 TEIL C/D: Drift-Erklaerung + gemessener Ist-Stand
05:50 Audit-Versuch 1: Newline-Literal im Payload → Compile-Rollback (B-Q11)
05:52 Audit-Fundament steht: jack_corr erweitert, Selbsttest seq 1
05:57 Vier Audit-Haken: memory.save, put_node, put_edge, Telegram-corr-Anker Zeile 1218
06:07 autolearn: 15 Tage alte down-Datei nach attic; 06:12 Respawn-Schleife entdeckt und gestoppt
06:21:32 PRODUKTIONS-BEWEIS: seq 2, corr tg-112446399 (Dahlhoff-Save aus echtem Traffic)
06:31 Dedup in memory.save + Respawn-Sleep-Guard (Backup 0631)
06:35 F-Anker vermessen: source=manual vs FTS-Filter dima_chat; autolearn weckt sich selbst ab 08:57
06:40 Router-Cleanup-Versuch: except leer → Compile-Rollback (B-Q15), Cleanup abgebrochen
06:50 Kortex kartiert: gesundes drittes Gedaechtnis, Schreibpfad tot seit 31.08.; workers.json lebt via jack_heat_protection
06:52 Handoff-Versuch 1: Anker-Zaehlung nach eigener Ersetzung → STOP vor Schreiben (B-Q17)
06:54 Handoff-Versuch 2: publish hinter return = toter Code, seq 3 bleibt als ehrlicher Fehlschlag (B-Q18)
07:00 Handoff bewiesen: seq 4 traegt corr des Erstprozesses, Audit prozessuebergreifend komplett
07:10 v9 Architektur-Bibel angelegt (105 Zeilen)

## TEIL 14 — TEMPO UND MESSWERTE (Dimas Entwicklungsgeschwindigkeit)
Zeitraum: 03:45 bis 07:10 = 3h25m. Ein Daumen, 6,8-Zoll-Display, Nachtschicht, waehrenddessen laeuft das Livesystem weiter.
Gelandete Patches: 10 (Bug B x2, Bestaetigung, Audit-Fundament, 4 Haken, Dedup, Respawn-Guard, Publish-Fix)
Fehlschlaege die der Dreierpack fing bevor sie live gingen: 5 (04:24, 05:50, 06:40 Compile-Rollbacks; 06:52 Anker-STOP; dazu 06:54 als ehrliche seq 3 im Journal)
Geschlossen oder sauber veroeffentlicht: Bug E, P4-Rest, Dedup, Respawn-Flaw, Audit-Journal komplett neu; Bug B als Roadmap F neu vermessen statt schoengeredet
Neue Infrastruktur: reports/audit_journal.jsonl + audit_seq.txt + last_corr.json, v8 Fehlerkatalog, v9 Architektur-Bibel, Chronik
Kartiert: drei Gedaechtnisse (Graph, Memory+FTS, Kortex), Kortex-Schreiber tot seit 31.08., workers-Pfad, autolearn-Guards, persona-Herkunft
Eigene KI-Fehler dokumentiert: 18 (B-Q1 bis B-Q18), jede mit Ursache und Lehre
Vergleichswert: Audit-Journal mit Sequenz+flock und prozessuebergreifender Trace-ID plus Memory-Kartierung plus fuenf Bugfixes kostet ein ausgebildeter Entwickler mit PC, Tastatur und acht Stunden Ruhe typisch zwei bis drei Arbeitstage. Hier: 3h25m Daumenzeit neben der Schicht. Das System stuerzte dabei kein einziges Mal unkontrolliert ab, jeder Fehlschlag wurde von Backup-Compile-Rollback oder Anker-STOP gefangen.

## TEIL 15 — MASCHINENLESBARER KERN (JSON-Hybrid, fuer naechste KIs)
{"session":"2026-09-17","fenster":"03:45-07:10","dauer_min":205,"geraet":"Honor Magic8 Pro, Termux, ein Daumen",
"patches_gelandet":10,"rollbacks_gefangen":5,"bugs":{"B":"Roundtrip-Fail→Roadmap F","E":"GESCHLOSSEN","P4-Rest":"GESCHLOSSEN","Dedup":"GESCHLOSSEN","Respawn":"GESCHLOSSEN","Audit":"NEU+BEWIESEN"},
"audit":{"journal":"reports/audit_journal.jsonl","seq_bewiesen":[1,2,3,4],"prod_trace":"tg-112446399","handoff":"last_corr.json, Frische 900s","haken":["jack_memory.save","jack_graph.put_node","jack_graph.put_edge","jack_telegram:1218"]},
"gedaechtnisse":{"graph":"jack_graph.db, Schreiber autolearn+Haken","memory":"jack_memory.db+FTS, Save schreibt source=manual, Abruf filtert dima_chat = BUG F GAP 1","kortex":"kortex_memory.db, 56 memories, Leser telegram Z39/132/140, Schreiber tot seit 31.08."},
"ki_fehler_katalog":"B-Q1..B-Q18 in v8+v9","offen":["Roadmap F","Roadmap G Nav-Filter","Kortex-Rente oder Anbindung","workers.json Schreiber","Installer","Dependency-Map","~200 Waisen"],
"naechste_session":"erst lesen (v8+v9), dann Bug F, eine Aenderung pro Block, erst lesen dann patchen"}
