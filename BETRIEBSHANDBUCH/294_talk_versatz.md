# 294 Talk-Versatz behoben (21.10.2026)

Symptom (logs/telegram_chat.jsonl 07:04): ab der 3. Nachricht beantwortete JACK die VORHERIGE Frage.
Ursache (gemessen): jack_talk baut fuer Groq _um = "Frueherer Verlauf ..." + Fenster (bis 2400) + "DIMA JETZT: " + Frage, gekappt auf die LETZTEN 2800 Zeichen. jack_groq_bridge.ask_groq kappt user_msg danach auf die ERSTEN 1500 Zeichen. Bei vollem Fenster (2034 Zeichen) lag "DIMA JETZT" bei Position 2116, Groq sah die aktuelle Frage nie und beantwortete die letzte Frage im Verlauf. groq_usage.jsonl bestaetigt: jede Nachricht begann mit "Frueherer Verlauf".
Fix (JACK_TUNE_VERSATZ2, Backup jack_talk.py.bak_20261021_versatz): Fensteranteil 1200 statt 2400, Gesamtkappung auf die letzten 1500 statt 2800. Nachrechnung: aktuelle Frage auch bei 900-Zeichen-Frage innerhalb der 1500. jack_telegram neu gestartet.
Lehre: Zwei Kappungen an zwei Stellen (hinten behalten vs. vorne behalten) heben sich gegenseitig auf. Bei jeder Kuerzung pruefen, welches Ende ueberlebt.
Offen: Live-Bestaetigung durch Dima (3+ Nachrichten hintereinander).
