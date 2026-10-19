# 288. Recovery v1 (`jack_recovery.py`, Hook im Kern von `jack_ui_agent.py`)

Stand: 17.10.2026. Bau: ChatGPT (Entwurf R01–R10), Claude (Kern-Patch, Review, Integration, Messung).

## Zweck
Wenn der UI-Agent auf dem Xiaomi in einen Störzustand gerät (Popup, Hänger, leerer UI-Baum, Login, Berechtigung), soll er deterministisch und begrenzt reagieren, statt blind weiterzutippen oder Vision zu verbrennen. Recovery setzt **nie** einen Erfolg. Erfolg bleibt allein beim Finish-Verifier (Kap. 284).

## Aufbau
- `jack_recovery.py`: reiner Klassifikator, ohne SSH, ohne Vision. `classify(Context)` liefert eine Klasse (R01–R10/UNKNOWN), eine Aktion (dismiss, back, wait, wake, abort, none) und einen Grund. `Budget`: höchstens 2 Recovery-Aktionen pro Lauf, gleiche Klasse nie zweimal hintereinander.
- Login-, Berechtigungs- und Netz-Erkennung greift nur bei Dialog-Klasse, Passwortfeld oder Systempaket, nicht auf beliebigem Seitentext (Claude-Einwand 15.10., Beleg C3-P07 „erlauben").
- Hook im Kern (`_run_agent_kern`), zwei Stellen: Budget-Init vor der Schrittschleife, Prüfung nach `letzte=(letzte+[sig])[-4:]`.

## Regeln im Kern
- Der Lauf endet **nur** bei LOGIN_REQUIRED, PERMISSION_UNBEWIESEN, SYSTEM_DIALOG_UNBEWIESEN, FORBIDDEN_DIALOG.
- R01-Tap (Popup schließen) nur nach Gegenprobe gegen `_lese_ui`: Index gültig, `gefahr=False` (JACK_TUNE_LEITUNG), Label in der SAFE_DISMISS-Liste. Sonst verworfen, dann alte Logik.
- Ist das Budget erschöpft, der Fall mehrdeutig oder unbekannt, läuft die alte Logik unverändert weiter (Vision-Fallback, Gemini).
- Nach jeder Recovery-Aktion: `letzte=[]` und `continue`, also frischer Dump.
- R04 (falsche Seite) ist bewusst **nicht** verdrahtet, weil es für Navigationsziel und Parent keine belegte Quelle gibt.
- Not-Aus: `~/jack/.recovery_off`. Fehlt das Modul, ist Recovery aus und die alte Logik greift.

## Messung
- Offline: 24 Snapshots aus C2+C3 ergeben 0 Auslöser. Instrumentierter Kern (Attrappen, ohne SSH): 12/12.
- Live-Regression, jeweils dieselbe Spec, derselbe Runner, dasselbe Tor wie C3:
  - Regression 1 (16.10.): P04 FAIL (der Actor drückte HOME, Recovery griff einmal R05 harmlos ein), T02 leerer Dump.
  - Regression 2 (16.10.): P06/P08 FAIL wegen leerem Dump (uiautomator Exit 137, siehe Kap. 289).
  - C4 (17.10.): P07 UNBEWIESEN, weil das Entsperren einmal nicht griff (siehe Kap. 289).
  - **C5 (17.10.): Tor BESTANDEN.** 8/8 VERIFIZIERT, Fallen 4/4, false_success 0, Vision 0, 0,37 Cent, Gerätezyklus 12/12. Recovery hat dabei nicht eingegriffen, sie stört also auf Normalaufgaben nicht.
- Offen: D1, eine Live-Serie mit echten Störfällen (Popup, Hänger, kaputter Dump), die zeigt, dass Recovery wirklich rettet. Plan von ChatGPT in `BUEROS/chatgpt/`.

## Nachtrag 19.10.2026: D1 BESTANDEN (echte Stoerfaelle, Recovery v1 rettet)
Spec/Runner ChatGPT (sha ff5a683b / 6840e604), Lauf Claude 05:5x. D01 echter MIUI-Dialog Geraet umbenennen: R01 drueckt Abbrechen, danach VERIFIZIERT, Orakel ohne Dialog-IDs. D02 haengender Zustand (scripted warte): R05 back, kein Erfolg. D03 einmal kaputtes XML: R07 wait, danach VERIFIZIERT. D04 dauerhaft kaputtes XML: R07 einmal, sicher ohne Erfolg beendet. 4/4, 0 false success, je 1 Recovery, Geraet nach jedem Fall gesperrt, 0 API-Kosten. Grenzen: D02-D04 sind im Testprozess injiziert, keine spontanen Android-Fehler. D04 rief den Vision-Rueckfall 3x (Stub) auf, im Ernstfall kostet das. Runner-Maengel: braucht PYTHONPATH=~/jack; Fehler vor setup() lassen das Geraet entsperrt (transport() vor try).
