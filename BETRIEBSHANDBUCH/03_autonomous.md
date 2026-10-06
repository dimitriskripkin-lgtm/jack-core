## 3. jack_autonomous.py (728 Zeilen, Wächter-Logik)

**Zweck:** Die eigentliche Logik hinter dem Dienst `jack_waechter` (der Dateiname passt nicht zum
Dienstnamen — historisch gewachsen, bewusst so benannt laut Projektnotizen). Prüft zyklisch, ob
alle Dienste und das Xiaomi leben, startet Tote neu, meldet Auffälligkeiten per Telegram.

**Fund (seit 06.10. korrigiert): der Prozess startete beim Hochfahren ZUSÄTZLICH acht Hintergrund-Threads
im selben Prozess** (`start_consolidated()`, läuft unbedingt vor der Hauptschleife):
`_autolearn_loop`, `_publisher_loop`, `_missions_loop`, `_scout_loop`, `_monitor_loop`,
`_sanity_loop`, `_lerner_loop`, `_proaktiv_loop`. **Seit 06.10. nur noch sechs** - die beiden
toten (`_publisher_loop`, `_missions_loop`) sind raus, siehe Update unten.

**Geklärt, welche davon echte Dopplungen zu den separaten runit-Diensten sind:**
- `_autolearn_loop` — **tot**, frühes `return` mit Markierung `JACK_TUNE_D2ONE`
  ("Lernen nur Dienst, nicht Thread"). Bewusst stillgelegt, Code darunter unerreichbar.
  Keine Dopplung mit dem echten `jack_autolearn`-Dienst.
- `_publisher_loop` — **läuft wirklich**, ruft alle 180s `jack_publish.push()` auf.
  **Mögliche echte Dopplung** mit dem separaten `jack_publisher`-Dienst — beide könnten git-Pushes
  auslösen, auf unterschiedlichem Takt. Noch nicht geklärt, ob das Absicht oder Altlast ist.
  Eigenes Kapitel zu `jack_publish.py` vs. was der `jack_publisher`-Dienst tatsächlich ausführt nötig.
- `_missions_loop` — **läuft wirklich**, nutzt `jack_missions.py` (dispatch_once/recover_stale,
  deutsche Status-Wörter: "fertig", "blockiert", "fehler", "wartet_freigabe", "verschoben") —
  ein **komplett anderes, älteres Mission-System** als `jack_mission_runner.py` (Kapitel 1),
  das diese Woche fast ausschließlich benutzt wurde. "wartet_freigabe" deutet darauf hin, dass
  dies der Ort ist, an dem die Shadow-Freigabe-Pipeline (Kapitel 1/2, `pending_approvals.json`)
  tatsächlich beheimatet ist. **Noch nicht live geprüft, ob beide Systeme gleichzeitig Missionen
  verarbeiten oder ob eins faktisch inaktiv ist** (z. B. weil `jack_missions.py`s eigene
  Eingangsquelle nie befüllt wird). Wichtigster offener Punkt der ganzen Kartierung bisher.
- `_proaktiv_loop` — **läuft wirklich**, aber **keine Dopplung** mit der proaktiven Kognition aus
  `jack_autolearn_loop.py` (26./27.09. gebaut). Andere Zuständigkeit: Morgengruß 6-9 Uhr
  (`jack_chains.run('morgen_briefing')`, max 1x/Tag) und eine einfache Akku-Warnung unter 20%
  (`JACK_TUNE_AUTOBAT` — **bestätigt derselbe Text, den wir am 29.09. von der Ollama-Erwähnung
  befreit haben, läuft also wirklich im echten Pfad**).
- `_scout_loop`, `_monitor_loop`, `_sanity_loop`, `_lerner_loop` — noch nicht einzeln geprüft.

**Die eigentliche Wächter-Schleife (`main()`):** nutzt eine `jack_queue.TaskQueue` (RAM-bewusst,
`min_ram_mb=800`) statt einer einfachen `while True`-Schleife, reiht `cycle`, `_maybe_audit`,
`_maybe_self_improve`, `_maybe_self_audit`, `_maybe_ingest_schedule`, DB-Optimierung, Xiaomi-Explore
und einen Shadow-Autofixer (nur unter 55°C, nur wenn Xiaomi per SSH erreichbar) ein.

**`cycle()`** — der Kernvergleich: merkt sich den letzten Zustand (`jack_waechter_state.json`),
vergleicht mit jetzt, meldet nur **Zustandswechsel** (Dienst war tot → neu gestartet, Xiaomi war da
→ jetzt weg, Fehlerzahl gestiegen), nicht jeden Zyklus neu. Xiaomi-Abwesenheit wird höchstens alle
3 Stunden gemeldet (`.xi_hb_down`-Marker, `JACK_TUNE_CYCL3H`) — das erklärt, warum die
Xiaomi-Meldung heute nicht bei jedem Check wiederkam.

**`_heartbeat_sv_check()`** — der eigentliche "Herzschlag tot → Dienst neu starten"-Mechanismus
(Phase A/A2/Sleepcap aus den älteren Übergabeprotokollen, hier erstmals im Code selbst bestätigt).
Prüft `jack_telegram`, `jack_cortex`, `jack_publisher`, `jack_autolearn` gegen `jack_tune.json`-Werte
oder Festwert-Fallback. **`jack_missions` steht nicht in dieser Liste** — der frisch gefixte
`jack_cortex`-Herzschlag-Bug (29.09.) lag in einer anderen Datei (`jack_cortex.py` selbst), nicht hier.

**GELOEST 06.10.2026** (`JACK_TUNE_DEADTHREADS`, live gemessen): `_missions_loop` fuetterte sich
aus `jack_missions.db`, die seit Wochen niemand mehr beschreibt - toter Thread, lief nur fuer nichts
mit. `_publisher_loop` war eine echte Dopplung zum `jack_publisher`-Dienst (identische
`jack_publish.push()` alle 180s). Beide Thread-Starts aus `start_consolidated()` entfernt (jetzt
6 statt 8 Threads). `jack_missions.py` und `jack_oracle.py` selbst bleiben unberuehrt - ersteres
wird noch von einem Telegram-Status-Befehl gelesen, letzteres von jack_stress.py/jack_cortex.py
gebraucht. Backup: `Attic/jack_autonomous.py.bak_20261006_deadthreads`.

**Offene Fragen für später:** Was tun `jack_scout`, `jack_monitor`, `jack_sanity`, `jack_lerner`
im Detail? Was ist `jack_queue.TaskQueue` genau (RAM-Drosselung)?
