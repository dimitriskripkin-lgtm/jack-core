# 236. nachtrag_20261007 (Abgleich Kapitel 01-20)

Angelegt 07.10.2026 aus dem Handbuch-Abgleich Grok/Claude. Ergaenzt die Kapitel 01-20, deren Text hinter dem Code zurueckliegt. Zeilenzahlen in den Kapiteln sind veraltet und gelten nicht.

**Zweck:** Sammelstelle fuer Marker und Schalter, die im Code stehen, aber in den alten Kapiteln fehlen. Geprueft: Claude hat die mit (C) markierten Punkte selbst gegen die Live-Datei gelesen, die anderen hat Grok gelesen.

**01 mission_runner:** (C) ALLOWED = set(_acts.names()), nicht mehr fest 39. (C) sv_restart nur fuer: telegram, cortex, waechter, autolearn, publisher, focus_monitor, missions, mcp. (C) reload_module nur fuer: ui_type, verify_gate, xiaomi_unlock, yt_hybrid, chat_router, ui_session. STOP-Datei beendet den Runner (JACK_TUNE_STOPKILL). Boost-TTL 15 Min (JACK_TUNE_BOOSTTTL), git pull im Poll-Takt (JACK_TUNE_PULLTHROTTLE).
**02 telegram:** (C) /lage (Zeile ~415) und /sms (~421) existieren, ebenso /ablehnen (JACK_TUNE_ABLEHNEN). (C) feste IP 10.229.239.131 nur als Befehlsfilter (Zeile ~1280), harmlos.
**03 autonomous (Waechter):** (C) adb-Check ohne feste IP (JACK_TUNE_ADBIPFREE, 07.10.). Vorher lief jack_adb_heal.py bei jedem Durchlauf, weil die feste IP nicht mehr stimmte (DHCP).
**04 talk / 05 chat_router / 07 autolearn:** nur Zeilen und feste IPs als Filter, keine Logikabweichung.
**11 oracle:** (C) Hauptschleife stand vor _py_skript_ok und SKRIPT_ALLOW, beide wurden nie definiert. Gefixt: Schleife am Dateiende (JACK_TUNE_MAINEND). Bei neuen Skripten fuer Oracle SKRIPT_ALLOW pflegen.
**12 cmd_handler:** JACK_TUNE_ALLFIX (/approve_all) und JACK_TUNE_ONEPATH ("Echte Tuer: /vorschlaege").
**13 coder:** py_compile ohne timeout (Kleinigkeit).
**14 write:** Hilfen _safe_name und _backup.
**15 planner:** JACK_TUNE_PLANGATE (validate_safe).
**16 selfsee:** JACK_TUNE_ONEPATH, JACK_TUNE_CHATGATE (Selfsee fuehrt nicht mehr selbst aus).
**17 ui_type:** Marker SPOTIFY, SPOTIFY_SCORE, SPOTIFY_SURPRISE, MAPS_YT, YTFALLBACK, YTHYBRID.
**18 outcome_tracker:** init_db, log_outcome.
**19 graph:** Marker BUGD, KATZEFIX, FAKT1, EMBLOKAL.
**20 groq_bridge:** Marker TPDSTOP, TPDSET, COOL429, KERNREAD (Tageslimit/Abkuehlung bei 429).

**Regel fuer neue Dateien mit Hauptschleife:** if __name__ == "__main__" mit Endlosschleife immer ans Dateiende. Alles, was die Schleife braucht, muss vorher definiert sein. pyflakes findet das nicht, der Abgleich schon.
