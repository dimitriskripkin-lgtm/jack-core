# 13. jack_coder.py

Gelesen 03.10.2026, Grok, live per read_file. Kein Umbau.

**Zweck:** Code erzeugen und in der Werkstatt laufen lassen. Zielordner jack_werkstatt unter home, nicht jack-Home. Kein Mission-Act.

**Funktionen:**
- _safe_name: basename, nur Buchstaben, Ziffern, Punkt und Strich, Endung py.
- _in_werkstatt: realpath muss unter der Werkstatt liegen. Prefix-Check, nicht commonpath.
- assess_risk: Substring-Kleinbuchstaben auf rm, shutil, drop, delete, Forkbombe, mkfs, dd, os.system, subprocess, eval, exec, socket, urllib, requests, SSH-Ordner, Secrets-Datei, telegram, Schluesselwort, os.environ.
- write_code: Prompt an jack_gemini_bridge.ask_gemini. Kein Groq-Ersatz. Zaeune werden abgeschnitten. HALIZA syntax_ok vor dem Schreiben. Syntax-Stop schreibt nicht.
- run_code: jack_ast_gate, dann assess_risk, py_compile, python3 cwd Werkstatt, Timeout 10s, Output 1500.

**Freigabe:** Die Zeichenkette wartet_freigabe kommt in dieser Datei nicht vor. Sie steht in jack_mission_runner.py, Funktion _run_fix_shadow, Text shadow: wartet_freigabe. coder hat keinen Knopf und kein proposals-Feld. Gate ist AST plus Substring plus HALIZA-Syntax. Muster ist leicht zu umgehen.

**Outcomes:** coder schreibt nicht in jack_outcomes.db.

**Offen:** Welches Modul write_code aufruft.
