# 20. jack_groq_bridge.py

Gelesen 03.10.2026, erste 90 Zeilen. Kein Umbau.

**Zweck:** Ein Ruf an Groq. load_key, ask_groq(system, user, timeout=20).

**Grenzen:** System auf 4000, User auf 1500, max_tokens 1024, temperature 0.55. Bei vorhandener Datei .groq_tpd_until wird nicht gesendet.

**Offen:** Modellname und Fehlerpfad hinter dem Schnitt nicht zitiert. Kein zweites Gehirn.
