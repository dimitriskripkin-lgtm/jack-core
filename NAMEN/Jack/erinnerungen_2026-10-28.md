# Erinnerungen 2026-10-28

## Ziel der Sitzung
Ein Schreibrechte-Gedächtnis für das Repo bauen: festhalten, wer Schreibrechte hat und wie sie sich über die Zeit ändern. Es liegt im separaten Ordner `NAMEN/`, **nicht als jack-Modul**.

## Vorgaben von Dima
- Nichts ersetzen, nichts löschen, nichts kaputt machen. Nur neue Dateien.
- Kein neues `jack_*.py`, kein jack-Modul.
- Ein Ordner `NAMEN/` mit den Namensordnern `Grok/`, `Tesla/`, `Dimitri/`, `Jack/` nebeneinander, die Logik in `NAMEN/schreibrechte/`.
- `.github/`, `config.ini` und bestehende Dateien bleiben unberührt.
- Repo ist öffentlich: kein Token, keine privaten Angaben.
- GitHub ist Archiv, kein Befehlsbus. Die Honor bleibt die Live-Wahrheit.
- Arbeit auf eigenem Branch mit Pull Request, Merge macht Dima.

## Was passiert ist
- Der gh-Login per Device-Code auf dem Assistenten-Computer ist nicht durchgegangen.
- Deshalb ging der Push über den verbundenen GitHub-Connector, in einem einzigen Commit auf dem Branch `schreibrechte-gedaechtnis`.
- Skript `schreibrechte.py` (nur Standardbibliothek, nur Lesen bei GitHub, Verlauf nur anhängend), Tests ohne Netzwerk, Verlaufsdatei mit einer ehrlichen Startzeile (noch kein Abruf).

## Offene Punkte
- Ein täglicher Lauf als GitHub Action kommt später, und nur mit Dimas Ja.
- Erster echter Abruf braucht einen Token mit Push-Rechten in der Umgebung, nie im Repo.
- Session-Erinnerungen kommen am Ende jeder Sitzung nach `NAMEN/<Name>/`.
