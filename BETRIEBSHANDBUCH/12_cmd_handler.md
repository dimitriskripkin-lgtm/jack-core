# 12. jack_cmd_handler.py

Gelesen 03.10.2026, Grok, live per read_file. Kein Umbau.

**Zweck:** Fruehe Slash-Befehle ohne eigenen Thread. handle(rt, text, send) gibt einen String zurueck oder faellt durch.

**Wer ruft:** jack_telegram.handle(), frueh.

**Befehle:**
- /akku und /sensor: jack_sensors
- /log: jack_log.recent(15)
- /level: jack_intent.get_level(), nur Anzeige x/4
- /errors: jack_errors.db, resolved=0, fuenf Zeilen
- /budget: jack_budget.status()
- /missionen: zaehlt pending, done, fail
- /approve_ und /reject_ mit ID: pending_approvals.json plus staged Datei. Approve kopiert staged auf live, wenn staged nicht aelter ist als live (E31 ist_veraltet). Sonst verworfen. Mission-JSON von fail oder pending nach done.
- /approve_all und /reject_all: Marke ALLFIX. Quelle shadow. Approve leert die JSON und ruft jack_health_monitor.check_after_approve. Reject loescht staged.
- /report: reports jsonl, letzte drei, Schnitt 3500
- /status: Akku und Temp ueber jack_thermal_guard, Missions pending und fail

**Freigabe:** shadow/pending_approvals, nicht missions/proposals. ID aus dem Slash, kein Diff. /level entscheidet nichts. PENDING_EXEC und PENDING_WRITE stehen hier nicht.

**Offen:** Ob Telegram approve_ noch hier landet oder schon bei proposals.
