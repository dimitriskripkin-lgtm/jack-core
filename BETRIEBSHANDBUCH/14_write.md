# 14. jack_write.py

Gelesen 03.10.2026, Grok. Kein Umbau.

**Zweck:** Freitext-Datei schreiben, nur in die Werkstatt. Kein Mission-Act.

**Funktionen:**
- propose: baut Vorschau, schreibt nichts. Name wird gesaeubert, Pfad unter jack_werkstatt.
- commit_write: jack_critic.pruefe, dann git add -A und commit im jack-Home als Backup, dann Datei nur wenn realpath unter der Werkstatt bleibt. Ausbruch mit .. wird blockiert.
- detect_write_request: fragt Gemini, ob der Satz eine Datei will. Kein Groq-Ersatz in dieser Datei.

**Freigabe:** Kein pending_approvals und kein PENDING_WRITE-Feld in dieser Datei. Der Knopf sitzt beim Aufrufer. propose ist nur ein Dict.

**Offen:** Wer propose und commit_write ruft. Nicht in dieser Datei.
