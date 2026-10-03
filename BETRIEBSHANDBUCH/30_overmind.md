# 30. jack_overmind_client.py

Gelesen 03.10.2026, erste 45 Zeilen. Kein Umbau.

**Zweck:** State lesen, Teacher fragen, nur erlaubte Hooks ausfuehren.

**Gatter:** API-Teacher hoechstens alle 180s, Datei .overmind_last_api. ALLOWED: status, ssh_check, adb_heal, sv_status, skills_list. FORBIDDEN: core_patch_without_approval, rm_rf, read_secrets, shell, raw_shell, eval, exec.

**Dateien:** jack_overmind_state.json, plan, result.
