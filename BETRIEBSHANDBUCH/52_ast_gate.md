# 52. jack_ast_gate.py

Gelesen 03.10.2026, erste 26 Zeilen. Kein Umbau.

**Zweck:** check_code vor Ausfuehrung. Verbotene Rufe: eval, exec, compile, __import__, breakpoint. Verbotene Importe unter anderem os, subprocess, socket, pickle.

**Offen:** Ob der Gate an jedem Schreibweg haengt, nicht in diesem Schnitt.
