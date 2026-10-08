# 238. nachtrag3_20261007 (Abgleich Kapitel 81-237, Abschluss)

Angelegt 07.10.2026. Ergaenzt 236 und 237. Abgleich Grok (gelesen) mit Stichproben von Claude (C).

**Fixes aus diesem Teil:** jack_android._adb (Timeout, bei Timeout Rueckgabe "adb timeout", Code 124) und jack_freigabe py_compile (Marker JACK_TUNE_SPTO).

**Gelernt (C):** Der Abgleich meldete "ssh ohne timeout im Kopf" fuer navi, karte, lerner, wissen_ernte, wissen_tief. Falsch: der Aufruf geht ueber mehrere Zeilen, timeout=t steht in der letzten Zeile (alle gelesen). Mehrzeilige subprocess-Aufrufe immer bis zur schliessenden Klammer lesen.

**196 jack_ollama_guard.py:** Datei existiert nicht mehr (stillgelegt mit der Ollama-Entscheidung vom 28.09.2026). Das Kapitel ist Archiv, Honor startet kein Ollama. Gate: jack_ollama_gate.py (Fallback-IP nur hinter ssh -G, HARDSTOP MAX_RUN 300, GURL).

**Marker ohne Kapiteltext:** 82 XITHINKLOCK, 83 BATFRESH, 84 UIELOCK, 91 BATFRESH, 93 XIWEBLOCK, 95 ADBG, 97 PERSONA_NOWRITE, TRAINERSTOP, 98 MON3D, 100 NAV_UNLOCK, 102 ICHBIN, 119 AUTOROLL, 122 NC, 125 UNLOCK_GATE, 130 NOTUNNEL, 133 AL3H (3 Alarme, 3 h Pause), 139 MAPG, 144 BUGE, 148 LOKLOCK, FRAGELOCK, 183 F6ADB, K3ZERO, 186 NC, 195 GURL, HARDSTOP, 198 K5ORCH, 211 F1SVCS, 221 NC, 227 WORKERFLIP, FRESHTEMP, 231 TUN, INTSU. Dazu die Lock-Marker (VLOCK, UIREADLOCK, LOOPLOCK, ANLOCK2): "lock" heisst, die Funktion antwortet mit einer Sperrmeldung, solange Ollama aus ist.

**Bekannt und liegen gelassen:** except Exception: pass an vielen Stellen, espeak und termux-microphone-record ohne Timeout (voice_router, hey, voice_chat_live), git add/commit/push ohne Timeout in jack_improve, shell-Aufrufe in jack_operator (cortex_cmd report) und stress.

**Geprueft (Grok):** jack_handbuch_gate, jack_arbeitsplatz, jack_kanal schreiben nur unter ARBEITSPLATZ, kein Geheimnis, kein Subprozess.
