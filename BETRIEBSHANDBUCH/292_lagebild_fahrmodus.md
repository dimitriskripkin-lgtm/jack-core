# 292 Lagebild und Fahrmodus-Erkennung (21.10.2026)

Datei: ~/jack/jack_lagebild.py (JACK_TUNE_LAGEBILD), nur lesen, kein Dienst, kein Act (noch).

## Aufruf
- `python3 jack_lagebild.py` -> JSON mit Honor + Xiaomi + Fahrmodus, ca. 2,6 s.
- `python3 jack_lagebild.py --fahrmodus` -> nur Fahrmodus, schreibt ~/jack/.fahrmodus.

## Inhalt
- Honor (Shizuku/rish, uid 2000): Bluetooth an/aus, aktives Audiogeraet, Anzahl gekoppelt, Akku, Temperatur, Vordergrund-App.
- Xiaomi (ssh xiaomi-jack + su): gesperrt, Vordergrund, Akku, Temperatur, Benachrichtigungen NUR als Paket + Anzahl (nie Titel/Text), Logcat-Fehler der letzten 400 Zeilen, WLAN-IP.
- Fahrmodus: aktiv, wenn das aktive Bluetooth-Audiogeraet des Honor mit "MBUX" oder "MB Bluetooth" beginnt (LKW wechseln, z. B. MBUX 33188 / MBUX 61123). Ist Bluetooth nicht lesbar, bleibt der alte Zustand stehen (unsicher=true), nie raten.

## Gemessene Lehren
- rish-stdout verliert Daten: dieselbe dumpsys-Abfrage lieferte 0 bis 21 Treffer, mal mit, mal ohne mActiveDevice. Loesung: Shizuku-Shell schreibt in /sdcard/Download/.jack_rish_<pid>.txt, Termux liest /storage/emulated/0/Download/... und loescht sofort. Danach 5/5 stabil.
- pm/cmd aus der Termux-App auf dem Xiaomi: "Failed transaction (2147483646)", wenn die Ausgabe in eine Termux-Pipe geht. Loesung: Ausgabe nach /dev/null oder in eine Datei umlenken.
- UI-Baum per `uiautomator dump` auf dem Xiaomi: 2,9 s (langsamste Lesestelle).

## Offen
- Fahrmodus-Waechter (alle 30 s) und Wirkung auf Telegram-Antworten (kurz, Sprache, Unwichtiges sammeln).
- Act `lagebild` fuer MCP/Nachtlauf (Sicherheitskern, braucht Dimas Go).
- Tasker-Bruecke (Tasker auf dem Xiaomi hat noch keine Aufgaben).

## Nachtrag 21.10. 06:58: Fahrmodus wirkt im Talk
- jack_talk.py (JACK_TUNE_FAHRMODUS, Backup .bak_20261021_fahrmodus): im System-Prompt von _talk_to_gemini_impl wird bei aktivem Fahrmodus angehaengt: hoechstens zwei kurze Saetze, kein Code, keine Listen. Ist .fahrmodus aelter als 60 s, wird er frisch ueber jack_lagebild.fahrmodus() geprueft (ca. 0,6 s, kein eigener Dienst noetig). Fehler werden geschluckt, Antwort laeuft dann normal.
- jack_telegram neu gestartet, laeuft. Trockenlauf des Blocks: Hinweis wird bei MBUX 33188 gesetzt.
- Noch offen: Unwichtiges zurueckhalten und nach dem Aussteigen gesammelt melden.

## Nachtrag 21.10. 07:31: Tasker-Bruecke LIVE BEWIESEN
- Import: Tasker-Hauptseite, ganz unten Reiter "Standardprojekt" lang druecken -> Project Importieren (Datei muss in /sdcard/Tasker/projects/ liegen). Tasker braucht Speicherzugriff (von Dima erteilt). Kein Anfaengermodus in 6.6.20.
- Ausloesen (root): am broadcast -a net.dinglisch.android.tasker.ACTION_TASK -e task_name <NAME>. JACK_TEST_DATEI schrieb /sdcard/Tasker/JACK/outbox/datei_<ms>.json mit result DONE (Weg Tasker->JACK ueber Datei bewiesen).
