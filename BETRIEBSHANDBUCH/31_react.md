# 31. jack_react.py

Gelesen 03.10.2026, erste 45 Zeilen. Kein Umbau.

**Zweck:** analysiere(cmd, output) nach einem Fehlschlag. Fragt Gemini, Befehl 800, Output 1200, Antwort max 3 Zeilen. Kein Fix heisst KEIN_FIX.

**Aufrufer:** jack_callback_handler nach run_exec, wenn der Output nicht mit rc=0 oder BLOCKIERT beginnt.

**Offen:** Rueckgabewert hinter dem Schnitt.
