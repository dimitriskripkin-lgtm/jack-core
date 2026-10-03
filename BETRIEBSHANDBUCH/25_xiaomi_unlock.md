# 25. jack_xiaomi_unlock.py

Gelesen 03.10.2026, ganz, 38 Zeilen. Kein Umbau.

**Zweck:** Bildschirm wecken vor UI-Befehlen. Kein Passwort. Wake keyevent 224, dann Swipe nach oben. Von Dima bestaetigt.

**Funktionen:** wakefulness, keyguard_showing, unlock_sequence, ensure_unlocked. SSH xiaomi-jack, su.

**Aufrufer:** jack_exec vor Tap und vor monkey/am/input.
