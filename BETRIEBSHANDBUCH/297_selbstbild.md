# 297 JACK-Selbstbild (21.10.2026)

Gebaut von ChatGPT (Auftrag 20a + Nachtrag, 20/20 offline), Review und Live-Einbau Claude.
- ~/jack/jack_selbstbild.py (JACK_TUNE_SELBSTBILD) schreibt reports/selbstbild.md (atomar, 0600, max 1100 Zeichen): Zeitstempel, Honor/Xiaomi-Akku nur als Messwert aus jack_lagebild, Temperatur, Bluetooth, Fahrmodus, 5 neueste Handbuchkapitel (Titel + erste Inhaltszeile), git log -5, offene Bugkarte (wird bei Platzmangel gekuerzt). Laufzeit ca. 2,6 s.
- jack_talk.py (Backup .bak_20261021_selbstbild): nach JACK_TUNE_HEALTHINJ wird das Selbstbild an den Groq-System-Prompt gehaengt, wenn juenger als 30 Min, sonst neu erzeugt (Timeout 5 s). Regel im Prompt: Was nicht im Selbstbild steht, weiss JACK nicht; keine "etwa"-Messwerte. Ausfall blockiert Talk nie.
- Review-Aenderungen Claude: MAX_CHARS 1500 -> 1100, weil ask_groq den System-Prompt bei 4000 Zeichen hinten abschneidet (Basis ca. 2600). Doppelte Kapitelnummer im Titel entfernt.
- Offen: Live-Bestaetigung (System-Laenge in reports/promptlog.jsonl muss unter 4000 bleiben; Antworten zu Kapiteln muessen den Inhaltszeilen entsprechen).

- Nachtrag 08:38: Live gemessen system=3797 + ask_groq-Kern 376 = 4173 > 4000, Regelsatz am Ende waere abgeschnitten. Regel jetzt VOR dem Selbstbild, MAX_CHARS 850. Test Kapitel 295: richtige Antwort.
