# 56. jack_skill_trainer.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Zweck:** Bis zu 3 sichere Skills am Tag. Sicher heisst nur exec und wait, Blockliste. 1 Erfolg wird TESTING, 3 Erfolge VERIFIED. UI-Skills bleiben liegen. Datenbank jack_skills.db.

**Nachtrag 28.10.2026 (Claude, Inventur I13/V01/V02/V12, Entwurf ChatGPT Runde 2b) JACK_TUNE_SKILLFAILCLOSED**
DB-Skill-Plaene werden nie mehr per shell=True ausgefuehrt: autolearn _skill_cmd_allowed sperrt alles, test_candidate_skills nur noch Inventur (log, keine Verifikation); skill_trainer _run_plan blockt cmd-Schritte und zaehlt reine wait/UI-Schritte nicht als Erfolg, _check: fehlende/unbekannte Kriterien = kein Erfolg. skill_run/plan_try (Runner, validate_safe) unberuehrt. Live-Tests ok, Backups *.bak_runde2b. Autolearn neu gestartet 13:31.
