# 290 mobile-use (Minitap) als Haende B, Installation 20.10.2026
- Paket minitap-mobile-use 4.0.0 (Apache-2.0, github.com/minitap-ai/mobile-use), abgetrennt in ~/jack_ext/mobile_use (venv mit --system-site-packages, 91 MB+). JACK-Dienste unberuehrt.
- Termux-Haken: Python 3.14, langchain-cerebras nicht verfuegbar (nur in Tests benutzt, weggelassen), psutil/lxml per apt (python-psutil, python-lxml), iOS-Modul idb sowie langchain_google_vertexai und langchain_azure_ai als Stubs (werfen RuntimeError bei Benutzung).
- Telemetrie: immer mit MOBILE_USE_TELEMETRY_ENABLED=false starten (sonst PostHog).
- ADB zum Xiaomi steht: 172.29.165.131:5555 device.
- Import-Test OK (sdk.Agent, Builders). Noch KEIN Lauf am Geraet: erst Adapter jack_actor_b mit JACK-Waechter (Auftrag 12 ChatGPT), dann Arena E als Vergleich.

## Nachtrag 20.10.2026 06:5x: Actor-B-Paket (Auftrag 13) auf dem Honor
ZIP von Dima hochgeladen, Hashes 6/6 OK, abgelegt in ~/jack_ext/actor_b (nicht live). Code gelesen: Controller fuehrt nur tap/swipe/back/home ueber jack_xiaomi aus, liest ueber jack_ghost, sperrt Text/Install/Uninstall/Shell/am start/Longpress, prueft jeden Tap gegen frischen Dump, BAD_LABELS/_GEFAHR, Checkables, vorregistrierte Navigation. TransportFence blockt adbutils/uiautomator2/adb-Prozesse/ADB-Ports (nur In-Process, keine OS-Sandbox). Budget-Callback mit Vorab-Reservierung, Modell gemini-2.5-flash-lite. Auf dem Honor: SDK-Vertragscheck BESTAETIGT (Maestro-Pfad als NO-GO markiert, wird durch eigenen Controller umgangen), Unittests 19 (1 uebersprungen) OK.
Naechster Schritt: Schattenlauf (echtes Gemini, echter Bildschirm, Aktionen nur protokolliert), danach Pilot E01 mit Dimas Go.

## Nachtrag 20.10.2026 07:00: Schattenlauf Haende B
Kette steht: Planner > Orchestrator > Contextor > Cortex > Executor mit gemini-2.5-flash-lite, echter Bildschirm (Settings), Cortex entschied korrekt: Ueber das Telefon antippen. JACK-Controller blockte (Label-Abgleich Ueber das Telefon / Update, Fix: Praefix mit Leerzeichen, Tests OK). Aktionen im Schatten nicht ausgefuehrt. Kosten ca. 1,3 Cent fuer 12 Modellaufrufe (Limit max_calls 12 gegriffen). Noetige Fixes am Paket: GeminiBudgetLedger muss BaseCallbackHandler erben; langgraph 1.0.10 + langgraph-prebuilt 1.0.5 (neuere brechen mobile-use 4.0.0). Erwartung: ca. 3-5 Cent pro Aufgabe, etwa 10x JACK-Actor.

## Nachtrag 20.10.2026 07:2x: Erster echter Pilot Haende B (E01)
Lauf 1: Cortex wollte Settings per launch_app starten, Controller sperrte am start -> SDK brach ganz ab. Fix Claude: launch_app nur fuer Apps der Aufgabe erlaubt (monkey -p, Paketname-Regex), Tests OK. Lauf 2: mobile-use tippte Ueber das Telefon und Detaillierte Informationen und Spezifikationen, Endbildschirm zeigt Androidversion 13 (unabhaengiges Orakel: JA). Aber: (1) Controller meldet nach dem Tap faelschlich Fehler (Vordergrund aendert sich waehrend Dump = Animation), (2) mobile-use meldet nie fertig, endet am Rekursionslimit 48. Kosten Lauf 2 ca. 1,7 Cent. Geraet danach gesperrt.
Offen: Fokus-Pruefung nach Aktionen mit kurzer Wartezeit/Wiederholung, Abschlusssignal (Outputter) fuer Lese-Aufgaben, Vergleich auf allen E-Aufgaben x3.

## Nachtrag 20.10.2026 07:3x: Pilot Haende B Lauf 3 sauber
Mit Snapshot-Ruhe (3 Versuche, 0,8 s) und output_description: 2 Taps ohne Fehlalarm bis Androidversion 13 (Orakel JA), 1 harmloser Tap auf den Wert gesperrt, Outputter gestartet. 12 Modellaufrufe, 0,95 Cent, 3 Geraeteaktionen. Outputter mit flash-lite lieferte kein JSON -> Outputter jetzt gemini-2.5-flash, Ledger erlaubt beide Modelle. Damit kostet Haende B pro Leseaufgabe etwa 1 Cent, gleiche Groessenordnung wie JACK-Actor.
