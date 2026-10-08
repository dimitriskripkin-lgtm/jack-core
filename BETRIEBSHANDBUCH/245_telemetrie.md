# 245 Telemetrie (JACK_TUNE_TELEMETRIE)

Zweck: Temperaturen, Akku, RAM, Last und Top-Prozesse von HONOR und XIAOMI als Zeitreihe. Grundlage fuer spaeteres Tagesprofil (Alltag erkennbar).

- Modul: jack_telemetry.py, Thread 'telemetrie' in jack_autonomous (nach dem proaktiv-Thread).
- Takt: 120 s Anlauf, dann alle 300 s. Datei: ~/jack/telemetry/telemetrie_JJJJ-MM.jsonl (eine Zeile pro Messung).
- Xiaomi nur ueber jack_xiaomi.run_shell (Schutzschalter + Schnellpfad). Honor >= 58 Grad: Xiaomi-Messung wird uebersprungen.
- Stop: Datei ~/jack/.telemetry_stop anlegen. Fehler: log_decision TELEMETRIE-ERR.
- Datenschutz: telemetry/ steht in .gitignore, nie ins Repo. Keine Inhalte, nur Werte und Prozessnamen.
- Regel: Logs werden nie automatisch zu Fakten. Auswertung nur als Vorschlag (gemeinsam/tagesprofil.md).
- Befund 08.10.2026 16:44: erster Lauf ok, beide Geraete liefern Werte. Honor 'last' zeigt '?' (loadavg nicht lesbar), kosmetisch offen.
