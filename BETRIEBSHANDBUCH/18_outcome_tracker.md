# 18. jack_outcome_tracker.py

Gelesen 03.10.2026, Grok. Kein Umbau.

**Zweck:** Schreiber von jack_outcomes.db. Aufgerufen aus jack_exec.run.

**Tabelle:** outcomes(id, timestamp, cmd, rc, output, success). cmd auf 500, output auf 1000.

**success:** 1 nur wenn rc 0 und das Wort error nicht im Output steht. Sonst 0. Exception wird geschluckt, kein Eintrag.

**Lesen:** get_stats gruppiert nach cmd. get_recent letzte Zeilen.

**Offen:** Andere Aufrufer ausser exec nicht geprueft.
