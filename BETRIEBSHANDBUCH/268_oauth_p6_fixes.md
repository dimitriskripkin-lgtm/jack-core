# 268 OAuth: Fixes aus dem P6-Review (09.10.2026 20:1x)
Quelle: ChatGPT-Review gemeinsam/review_oauth_chatgpt.md, von Claude gegen den Code geprueft (Befund 1 und 2 bestaetigt).
## Aenderungen in jack_mcp_oauth.py (Marker JACK_TUNE_OAUTH3)
1. _load(): Datei fehlt = leerer Zustand wie bisher. Jeder andere Lesefehler (kaputtes JSON, Rechte) sichert die Datei einmalig als .jack_oauth.json.corrupt (chmod 600, gitignore, in SECRET_NAMES) und loggt nur den Fehlertyp. Der Zustand wird weiter leer geladen, die Originalbytes gehen aber nicht mehr verloren.
2. _ipguard(): Limit pro Client-IP vor dem SDK. /register 3 pro Stunde, /authorize 10 pro Stunde, Antwort 429. IP aus Header cf-connecting-ip (Cloudflare setzt ihn), sonst scope client. Nur im Speicher, Neustart setzt zurueck. Die globalen Limits in RL bleiben als zweite Schicht.
## Tests
reports/t_oauth_fix.py: fehlt, kaputt, Kopie vorhanden. Live lokal 127.0.0.1: 3x 400, dann 429. Extern via Proxy nicht aussagekraeftig, weil der Proxy die Quell-IP wechselt.
## Offen aus dem Review
Mittel/niedrig: state-Handling im SDK nicht eigenstaendig geprueft, Mehrprozess-Race nur relevant bei mehreren Workern (aktuell ein Prozess), Framework-Fehlerantworten nicht vollstaendig geprueft.
