# 107. jack_self_improve.py

Gelesen 03.10.2026, Kopf. Kein Umbau.

**Bewiesen 03.10.2026, Zeilen 72-115:** run() patcht jack_cortex.py nicht. fix_vorbereiten schreibt ein Script nach ~/jack_werkstatt. Das Script selbst enthaelt open(quell).write. Backup und py_compile-Rollback sitzen im Script, nicht im Aufruf. Zusaetzlich Zeile in jack_memory.db und jack_fixes.json.

**Knopf:** run() schickt Telegram approve:fix_id und reject:fix_id. Es startet das Script nicht. Aufrufer in autonomous, telegram, autolearn, cortex, missions: grep_count fehlgeschlagen, nicht null. Wer den Knopf ausfuehrt, nicht in diesem Schnitt.
