# 46. jack_error_to_rule.py

Gelesen 03.10.2026, erste 28 Zeilen. Kein Umbau.

**Zweck:** Fehler aus jack_errors.db werden Regeln. Schreibt jack_learned_rules.md und jack_learned_rules.json.

**Muster:** CORTEX_ERR plus SSH heisst Timeout und su -c, kein /tmp.

**Folge:** Deshalb ist jack_learned_rules.md lokal staendig geaendert. Nicht mit git add -A.
