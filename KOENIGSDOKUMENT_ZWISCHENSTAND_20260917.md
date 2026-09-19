# JACK — Königsdokument Zwischenstand
**17.09.2026 ~12:40 · Für kontextlose KI · Qwen3.8-Max**

## SOFORT LESEN
1. Honor Magic8 Pro = GEHIRN. Termux, kein Root, alle Dienste. Xiaomi 11T Pro = MUSKEL, Root, SSH 8022.
2. Nur 124 Module sind transitiv erreichbar. Vor jedem Patch reports/module_status.json prüfen.
3. Backup → py_compile → __pycache__ löschen → Dienst neu starten. Immer.
4. Honor ist die Wahrheit. Erst ls/grep/PRAGMA, dann behaupten. Nie raten.

## PFADE
- jack=/data/data/com.termux/files/home/jack
- services=/data/data/com.termux/files/usr/var/service
- attic=jack/attic (Archiv, nie löschen)
- reports=jack/reports (Protokolle)
- ssh=/data/data/com.termux/files/home/.ssh/config

## DIENSTE (alle laufen)
jack_telegram (pid 17122) · jack_cortex · jack_waechter (Logik=jack_autonomous.py) · jack_focus_monitor · jack_autolearn
PAUSIERT: jack_missions (STOP). AUS: jack_publisher, ollama (.ollama_lock — NIEMALS ohne Dimas Wort).

## GEDÄCHTNIS-ARCHITEKTUR
- **jack_graph.db**: nodes(id,typ,name,wert,src,ts) + edges. TYPS=(person,geraet,fakt,skill,chat,persona,ziel). SUSPICIOUS-Gate in put_node aktiv.
- **jack_memory.db**: memory + memory_fts(FTS5). Save schreibt source=manual, Abruf filtert IN(dima_chat,manual). JACK_TUNE_BUGF1.
- **kortex_memory.db**: Read-Only-Archiv, 56 memories, 4 Knoten migriert in Graph (src=kortex_migration_17.09).
- **reports/audit_journal.jsonl**: seq+corr über Prozessgrenzen. jack_corr.new() publiziert nach last_corr.json, active() liefert prozessübergreifend (900s Frische).
- **reports/talk_window.jsonl**: letzte 8 Gesprächswechsel.

## MODELLE
Groq gpt-oss-120b: Talk/Charakter, NIEMALS exec. Gemini 2.5 Flash-Lite: Technik/Code. Ollama llama3.2:3b (Xiaomi): gesperrt.

## HEUTE ERLEDIGT (17.09.)
- Bug A-G alle geschlossen oder als Hypothese entlarvt
- Audit-Journal gebaut und im Produktionsbetrieb bewiesen (seq 1-15, corr tg-*)
- workers.json: Cron */30 auf check_all_workers, last_check frisch, Xiaomi online 29.3°C
- JACK_TYPS: persona und ziel hinzugefügt, live getestet
- Modul-Landkarte: 124 aktive, 31 Klein-Orphans im attic, 5 auto-gestartet, 27 stringref, 25 nirgends
- Kortex-Migration: 4 Knoten in Graph
- P6 Profil-Guard, LERN2 Stoppwörter, VERSATZ1 bestätigt
- Git-Push 5fdd5a8b auf origin/master
- v8 Fehlerkatalog + v9 Architektur-Bibel erstellt
- Dependency-Map + module_status.json erstellt

## OFFEN (priorisiert)
1. Waisen-Bereinigung: 25 Nirgends-Module einzeln sichten (reports/modul_landkarte.md)
2. Phase 8.5 Musterzähler: braucht Opus + 24h LERN2-Daten
3. install.sh: Reproduzierbarkeit auf zweitem Gerät
4. P5 Werkzeug-Register: Opus empfohlen für Architektur
5. Kontext-Trägheit messen

## EISERNE REGELN
- Ollama-Lock bleibt bis vier Belege
- Kein neues jack_*.py ohne Dimas Satz
- Patch idempotent: SCHON DRIN | PATCH OK | STOP
- PRAGMA vor SQL, NULL separat zählen
- E21: Vor Patch reports/module_status.json prüfen
- E19: Funktion definiert ≠ aufgerufen, immer beide grepen
- E22: TYPS = person/geraet/fakt/skill/chat/persona/ziel
- GESCHLOSSEN nur mit Live-Roundtrip-Beweis
- Wächter-Restart nur mit Drain + Dimas Ja
- Code ans Ende, max 40 Zeilen, HONOR/XIAOMI vor jedem Block

## FEHLERKATALOG
E1-E22 in reports/flugschreiber_stand.json und onboarding v7.1. KI-Fehler: reports/ki_fehler.jsonl. B-Q1 bis B-Q19 in v8+v9.

## FORM
Fußzeile: MSG-MMTT-NN · Modell · Phase · Warum · Jetzt · Danach · Start. Bremen-Zeitstempel. Ein Thema pro Block. Diagnose+Fix+Test gebündelt.

---
*Stand: 17.09.2026 ~12:40 · Qwen3.8-Max · MSG-0917-36*
