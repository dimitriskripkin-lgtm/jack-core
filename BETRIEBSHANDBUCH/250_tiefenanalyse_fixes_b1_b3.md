# 250 Tiefenanalyse-Fixes B1-B3 (09.10.2026)

Stand: umgesetzt, Dienste neu gestartet (telegram, cortex, missions), Negativtests bestanden.

## B1 Runner-Pfadpruefung (jack_mission_runner.py, Marker JACK_TUNE_REALPATH)
Die Pruefung `fp.startswith(J)` in fix / file_create / file_delete liess `../` und Symlinks durch.
Jetzt: `os.path.realpath(fp)` muss J selbst sein oder mit J + "/" beginnen. Test: file_create nach J/../x -> "Pfad-Tabu".

## B2 approve_proposal nur mit Dima-Freigabe (JACK_TUNE_DIMASIG)
- Neu: jack_dima_sig.py (sign/verify, HMAC-SHA256). Schluessel: ~/jack/.dima_secret (wird beim ersten sign() angelegt, 0600, in .gitignore, per read_file gesperrt weil "secret" im Namen).
- jack_telegram.py: /freigeben <id> haengt `dima_sig` an die Mission (nur chat_id von Dima kommt dort durch).
- Runner: approve_proposal ohne gueltige Signatur -> "nur mit Dima-Freigabe (Telegram /freigeben)". Test ohne Signatur: abgelehnt.
- Direkte Acts exec_proposed / write_proposed bleiben den vollen Rollen (claude, legacy) vorbehalten, Nachtlauf ist per NIGHT_DENY gesperrt.
- Offen: Positivtest = Dima gibt einmal einen echten Vorschlag per /freigeben frei.

## B3 Xiaomi input text (JACK_TUNE_SAFETEXT)
Neu: jack_safe_text.typed(txt): Whitelist A-Za-z0-9 und `. , : _ @ / + = -`, Leerzeichen -> %s, max 300 Zeichen. Eingebaut in jack_planner.py, jack_ui_agent.py, jack_ui_type.py, jack_android.py. Folge: Umlaute und Sonderzeichen werden beim Tippen gestrichen (input text kann sie eh nicht).

## Rueckbau
Marker per grep suchen; .mcp_roles_off betrifft nur die MCP-Rollen, nicht diese Fixes.
