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
