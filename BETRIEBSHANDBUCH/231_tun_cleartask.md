# 231. jack_tun.py

Angelegt 06.10.2026, Claude. Live gemessen, nicht nur Kopf gelesen.

**Zweck:** Duenne Bruecke zwischen UI-Automatisierung (`jack_planner`/`plan_try`) und echten
Android-Intents. `intent(action, data)` versucht erst ein `am start`-Kommando, `jack_sehen`/`jack_tun`
tippen nur, wenn das Kommando scheitert (`tippen_erst_wenn_kein_kommando`).

**Fund und Fix 06.10.2026 (`JACK_TUNE_CLEARTASK`):** `intent()` rief `am start -a <action>` OHNE
Task-Flags. Wenn direkt nach einer Settings-Unterseite eine neue per Intent geoeffnet wurde, holte
Android oft nur die schon laufende Settings-App nach vorne (gleicher Bildschirm wie vorher), statt
zur neuen Zielseite zu springen - erkennbar an der Android-eigenen Warnung "Activity not started,
its current task has been brought to the front". Live bestaetigt an `wlan_seite` und `akku_seite`,
die beide erst nach dem Fix wirklich navigierten. Fix: `-f 0x10008000`
(FLAG_ACTIVITY_NEW_TASK | FLAG_ACTIVITY_CLEAR_TASK) an jeden `am start`-Aufruf angehaengt.
Betrifft jeden kuenftigen Skill, der mehrere Settings-Seiten hintereinander oeffnet.
Backup: `Attic/jack_tun.py.bak_20261006_cleartask`.

**Offen:** `datei()` und `tippen_erst_wenn_kein_kommando()` noch nicht einzeln live getestet.
