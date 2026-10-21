# 295 Tasker-Bruecke (21.10.2026)

Datei: ~/jack/jack_tasker.py (JACK_TUNE_TASKER). Kein Dienst, kein Act (noch).
- run_task(name, warte=8): Broadcast ACTION_TASK (root, jack_xiaomi.run_shell), wartet auf Quittung /sdcard/Tasker/JACK/outbox/<praefix>_<ms>.json (nur neuer als Startzeit - 2 s), liest und loescht sie.
- Whitelist ERLAUBT: JACK_TEST_DATEI (datei), JACK_TEST_VIBRA (vibra). Neue Tasks nur nach Eintrag dort.
- aufraeumen(alter_s): alte Quittungen loeschen.
- Gemessen: JACK_TEST_DATEI Hin+Rueck 1,5 s, Quittung result DONE, Outbox danach leer. Nicht erlaubter Name abgelehnt.
- Tasker-Projekt: /sdcard/Tasker/projects/JACK.prj.xml (aus Auftrag 19, ChatGPT), importiert in Tasker 6.6.20.
- Grenze: "DONE" ist Taskers Aussage. Wirkung pruefen wie immer unabhaengig (Pruefer).
