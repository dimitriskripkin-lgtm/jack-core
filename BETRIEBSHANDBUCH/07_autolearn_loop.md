## 7. jack_autolearn_loop.py (480 Zeilen, Hintergrund-Kognition)

**Zweck:** Der Dienst `jack_autolearn`. Läuft zyklisch (Standard-Pause 120s), prüft Fähigkeiten
("Skills") auf Erfolg/Defekt, generiert (eigentlich, s. u.) neue Fähigkeiten aus Fehlerlogs, und
seit letzter Woche: proaktive Beobachtung (Akku/Fehlerrate/SSH/Honor-Hitze) mit Self-Tooling-Vorschlägen.

**`run_cycle(cycle_num)` — Ablauf pro Zyklus, in dieser Reihenfolge:**
1. `_proaktiv_check()` — diese Woche gebaut, siehe ältere Lehren-Notizen. Beobachtet Xiaomi-Akku,
   Fehlerrate der letzten 20 Missionen, Xiaomi-SSH-Ausfall >10 Min, Honor-Hitze (≥45°C). Generiert bei
   echter Fehlerrate-Spitze automatisch einen `propose_fix`-Vorschlag (`sv_restart jack_missions`).
2. `check_db_integrity()` — **das ist die Stelle des uralten F1-Bugs** (900s-HB_RESTART-Loop,
   Tage vor dieser Handbuch-Kartierung gefixt): `quick_check` statt vollem `integrity_check`, nur
   noch jeden 10. Zyklus.
3. `promote_candidate_skills()` — hebt erfolgreich getestete Kandidaten-Skills in den aktiven Status.
4. `detect_futile_skills()` — Skills mit >20 Ausführungen und 0 Erfolgen werden automatisch auf
   `DEFEKT` gesetzt, Alarm per `jack_autonomous.notify()`. Eine Art Selbstkritik-Mechanismus für
   die eigenen gelernten Fähigkeiten.
5. `genesis_skills()` — **bestätigt weiterhin stillgelegt** (`return 0  # JACK_TUNE_GENESIS`,
   deckt sich mit Notizen aus früheren Übergabeprotokollen). Der tote Code danach (nie erreicht)
   würde mehrere Logdateien nach Tracebacks durchsuchen und daraus automatisch neue Fix-Skills
   vorschlagen — eine Art Vorläufer des heutigen `propose_fix`-Systems, nie reaktiviert.
6. `test_candidate_skills()` — prüft offene Kandidaten.
7. Jeden 6. Zyklus: `health_check_faehigkeiten()`.

**Datenablage:** `jack_skills.db` (eigene Datenbank für Fähigkeiten/Skills — nicht zu verwechseln mit
dem unverdrahteten, toten Modul `jack_skills.py` aus der alten Modulkarte, das ist eine Datei,
hier ist es eine Datenbank). `jack_memory.db` wird zusätzlich einmal täglich um 4 Uhr per
`jack_memory_pruning` bereinigt, läuft laut Kommentar je nach Last auf Honor oder Xiaomi
(`jack_heat_protection`-Worker-Entscheidung).

**`main()`** — Dauerschleife, schreibt bei jedem Zyklus zuerst den Herzschlag
(`JACK_TUNE_HBEARLY` — das ist die VOR dem eigentlichen F1-Fix liegende, zu frühe Teil-Lösung,
die in den alten Protokollen als "zu früh gefeiert" beschrieben wurde; der echte Fix liegt in
`check_db_integrity`, Punkt 2 oben).

**Verhältnis zu `_proaktiv_loop()` aus Kapitel 3:** keine Dopplung (dort: Morgengruß + einfache
Akku-Warnung; hier: die viel umfassendere proaktive Beobachtung mit Self-Tooling-Anschluss).
Zwei unterschiedlich mächtige, getrennt gewachsene proaktive Systeme im selben Projekt — nicht
falsch, aber ein Vereinheitlichungs-Kandidat für später.

**Offene Fragen für später:** Was genau prüft `_d2_rate_ok()`/`_skill_cmd_allowed()` (ganz am
Dateianfang, noch nicht gelesen)? Was ist `jack_memory_pruning.py` im Detail?
