# 107. jack_self_improve.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Bewiesen 03.10.2026, Zeilen 72-115:** run() patcht jack_cortex.py nicht. fix_vorbereiten schreibt ein Script nach ~/jack_werkstatt. Das Script selbst enthaelt open(quell).write. Backup und py_compile-Rollback sitzen im Script, nicht im Aufruf. Zusaetzlich Zeile in jack_memory.db und jack_fixes.json.

**Knopf 03.10. 15:10:** callback ruft cmd_handler /approve_id. Der kopiert staged_path aus pending_approvals.json ueber die Live-Datei. Er startet das Werkstatt-Script nicht. Self-Improve schreibt das Script und jack_fixes.json, nicht pending_approvals.json. Knopf und Script treffen sich im gelesenen Code nicht. Stand 15:16: pending_approvals.json ist [], jack_fixes.json ist {}. Werkstatt liegt ausserhalb von JACK_HOME, Liste nicht erlaubt.
