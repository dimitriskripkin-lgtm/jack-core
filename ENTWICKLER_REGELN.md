# ENTWICKLER-REGELN (verbindlich fuer jede KI-Session)

1. BOT-RESTART PFLICHT: Nach JEDER Aenderung an jack_telegram.py,
   jack_talk.py, jack_persona.md oder Parser-Modulen (jack_exec_parser.py)
   zwingend "sv restart jack_telegram" ausfuehren.
   Ohne Restart laeuft der alte Code im RAM weiter - Aenderungen unsichtbar.
   (Regel von Dima, 20.08.2026)
2. Backup + py_compile + Rollback vor jedem Patch.
3. Live-Output vor Urteil - nie raten.
4. 3x gescheitert = Strategie wechseln.
