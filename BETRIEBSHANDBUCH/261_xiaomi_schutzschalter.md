# 261 Gemeinsamer Xiaomi-Schutzschalter (09.10.2026, A-011)

- Problem: jack_xiaomi.run_shell hatte einen Schutzschalter (2 Fehlschlaege -> 30 s "Xiaomi weg"), aber nur im Prozess-RAM. ssh-Strings ueber jack_exec.run (exec_proposed, Telegram-EXEC, Missionen) liefen daran vorbei und liefen bei Ausfall in volle Timeouts.
- Loesung (JACK_TUNE_XIBREAKER2): neues Modul jack_xibreaker.py, Zustand in ~/jack/.xiaomi_breaker.json (gitignored). run_shell UND jack_exec.run (Befehle mit 'xiaomi-jack' oder '-p 8022') pruefen und melden dorthin. rc 255 oder Timeout = Fehlschlag, 2 in Folge = 30 s Sperre, jeder Erfolg setzt zurueck.
- Test: Sperre gesetzt -> jack_exec.run('ssh xiaomi-jack echo x') = rc=255 "Xiaomi weg (gemeinsamer Schutz, 30 s)"; normal weiter rc=0. Nach Test zurueckgesetzt.
- Neustart: telegram, waechter, missions, mcp (MCP-Session reisst ab, init.sh).
- Hinweis: Testbefehl mit Sperre setzen UND ssh im selben exec setzt die Sperre durch den Erfolg wieder zurueck (richtig so).
- Nicht erfasst: ssh ohne 'xiaomi-jack'/'-p 8022' im String (z.B. direkte IP ohne Port). Bei Bedarf Muster erweitern.
