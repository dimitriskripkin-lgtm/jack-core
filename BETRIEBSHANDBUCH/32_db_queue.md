# 32. jack_db_queue.py

Gelesen 03.10.2026, erste 45 Zeilen. Kein Umbau.

**Zweck:** Ein Schreiber-Thread pro Datenbank. write(db_path, sql, params) stellt in die Queue. WAL beim Schreiben.

**Aufrufer:** jack_memory.save. Andere Schreiber nicht geprueft.

**Offen:** wait-Pfad und Fehler hinter dem Schnitt.
