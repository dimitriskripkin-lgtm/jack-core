# 25. jack_xiaomi_unlock.py

Gelesen 03.10.2026, ganz, 38 Zeilen. Kein Umbau.

**Zweck:** Bildschirm wecken vor UI-Befehlen. Kein Passwort. Wake keyevent 224, dann Swipe nach oben. Von Dima bestaetigt.

**Funktionen:** wakefulness, keyguard_showing, unlock_sequence, ensure_unlocked. SSH xiaomi-jack, su.

**Aufrufer:** jack_exec vor Tap und vor monkey/am/input.

**Nachtrag 26.10.2026 (Claude, K1b)**
JACK_TUNE_XIGATE_UNLOCK: _su ueber jack_xiaomi.run_shell(as_root=True); ganze Pipeline laeuft jetzt als root (vorher nur der erste Befehl). Live-Zyklus: Dozing+gesperrt -> ensure_unlocked Awake/entsperrt -> keyevent 223 -> Dozing/gesperrt.
