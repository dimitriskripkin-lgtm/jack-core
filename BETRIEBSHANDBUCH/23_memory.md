# 23. jack_memory.py

Gelesen 03.10.2026, erste 59 Zeilen. Kein Umbau.

**Zweck:** Episoden-Kueche jack_memory.db. Nicht der Graph.

**Tabelle:** memory mit id, cmd, result, intent, time, source, parent_id, kontext_typ. Dazu FTS5 memory_fts auf cmd und result. WAL, busy 5s.

**save:** prueft Duplikat auf cmd plus intent, dann write. query sucht per FTS, n=5.

**Offen:** FTS-Trigger und Embedding-Pfad nicht in diesem Schnitt.
