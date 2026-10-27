# 296 Xiaomi-Karte und App-Sperrliste (21.10.2026)

Gemessen (nur lesen, root ueber jack_xiaomi):
- Geraet 2107113SG (Xiaomi 11T Pro), Android 13, MIUI 14 (V14.0.5.0.TKDMIXM), 1080x2400, 440 dpi, laeuft seit 15 Tagen durch.
- Standard: Launcher com.miui.home, Browser Chrome, Assistent Google, Tastatur Gboard. Kein Notification-Listener aktiv.
- 129 Nutzer-Apps, 25 deaktivierte Pakete. /data 224 GB, 40 % belegt. WLAN haengt am Hotspot des Honor.
- Magisk 30.7 mit Shamiko; die Magisk-App ist versteckt unter einem Zufallsnamen (in magisk.db als requester eingetragen, kein Fremdpaket).

WICHTIG: Das Xiaomi ist NICHT leer. Darauf liegen Bank-, Krypto-, 2FA-, Versicherungs- und Messenger-Apps.
Daraus folgt eine harte Regel fuer UI-Steuerung, Tasker und Benachrichtigungen:
- Sperrliste: ~/jack/.sperrliste_apps (privat, gitignored, Paketnamen bewusst nicht im Repo).
- Diese Apps nie oeffnen, nie bedienen, nie per Tasker ausloesen; Benachrichtigungen nur zaehlen, nie Inhalt lesen (2FA-Codes!).
- Offen: Sperrliste in jack_ui_agent, jack_tasker und Lehrer/Wegbuch technisch erzwingen (nicht nur hier dokumentieren).

## Nachtrag 21.10. 08:52: Magisk-Toast-Flut
- Jeder su-Aufruf (JACK/Claude, UID 10069 Termux) erzeugte einen Toast "Superuser-Rechte gewaehrt", hunderte in der Warteschlange. Einstellung muss in der AKTIVEN versteckten Magisk-App (Mamagisk) gesetzt werden: su_notification=0 (Keine) in deren Prefs. Zusaetzlich policies.notification=0 fuer 10069 und 10390. Danach keine neuen Toasts (gemessen).

**Nachtrag 27.10.2026 (Claude, K1c von ChatGPT) JACK_TUNE_APPSPERRE**
Neu jack_app_sperre.py: gesperrt(paket) liest ~/jack/.sperrliste_apps (24 Eintraege), fail-closed bei fehlender/leerer/kaputter Liste und ungueltigem Paketnamen. Erzwungen in jack_planner.step_open_app (P1) und jack_ui_agent.run_agent-Wrapper vor Unlock (P2). Live-Negativtests: gesperrte App und Muellname in beiden Wegen blockiert, Chrome/Termux/Settings/Spotify erlaubt. P1 wirkt im Missions-Dienst erst nach Neustart jack_missions (nur Dima). NICHT eingebaut: P3 open_url_xiaomi mit Pflicht-Zielpaket (bricht alte Aufrufer). Weiter offen: Tasker-Tasks, skill_run-Intent-Fallback, andere direkte Appstarts.
