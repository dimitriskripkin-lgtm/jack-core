# 237. nachtrag2_20261007 (Abgleich Kapitel 21-80)

Angelegt 07.10.2026 aus dem Abgleich Grok (gelesen) und Claude (Stichproben gegen die Live-Datei). Ergaenzt 236. Zeilenzahlen in den alten Kapiteln gelten nicht.

**Zweck:** Marker und Schalter, die im Code stehen, aber in den Kapiteln fehlen. Neue Pflicht: Kapitelquelle ist der Code, nicht umgekehrt.

**Fixes aus dem Abgleich (07.10.):** jack_voice_handler (Timeouts, JACK_TUNE_VOICETO), jack_bugfix_loop / jack_audit / jack_coder (Subprozess-Timeouts, JACK_TUNE_SPTO). Telegram-Dienst nach dem Fix neu gestartet.

**21 health:** BATFRESH, DAILY, DRAINLOG, HEALTHHONEST, NC. **26 mcp_server:** ACTS, HBGATE, KANAL, ARBEITSPLATZ, MCPAUTH, READCAP, WAITRESULT. **27 heat_protection:** LAGE5, NOFALL2, NOPKILL2. **28 callback_handler:** ONEPATH2, ONEPATH3, OSFIX, FAKT1. **33 focus_monitor:** FOCUS, FOCUSBACKOFF. **34 cortex:** R01IP, N2BAT, NOALLES. **39 budget:** BUDGET2009.
**45 delta / 55 thermal / 77 briefing:** BATFRESH (77 zusaetzlich STOLPER, STANDAUTO). **47 explorer:** EXPLSAFE. **51 autodoc:** HALDOC. **54 self_audit:** SOLLAUDIT4, FEATLIVE. **60 tuev3:** TUEVLOCK. **62 autofixer_shadow:** SHADOWLOCK, MTIME. **64 corr:** AUDIT1. **68 ui_read:** UIREADLOCK. **76 publish:** CRIT002, HASH2. **78 heartbeat:** SSHG (Xiaomi-Adresse wird per ssh -G aus dem Alias gelesen, die feste IP ist nur Fallback). **79 voraussetzung:** ANLOCK2. **80 loop:** LOOPLOCK.

**Merke:** Feste IPs als Fallback (config, screen_mapper, heartbeat) oder in Text/Filtern (snapshot, gemini_bridge, telegram, autolearn) sind bekannt und harmlos, solange der Alias xiaomi-jack die echte Adresse liefert. Funktionen hinter einem __main__-Testblock (chains, approval, log) sind beim Import trotzdem definiert, kein Fehler.
