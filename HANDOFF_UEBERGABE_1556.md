# JACK HANDOFF — Übernahme durch nächste Session
Stand 17.09. 1556 · Qwen3.8-Max · Honor Magic8 Pro

REGEL: Honor=Wahrheit, erst ls/grep/PRAGMA. Code ans Ende max 40 Zeilen, Gerät-Prefix, EIN Heredoc. Backup+py_compile+pycache+Restart nur Drain+Dimas Ja. E19 definiert≠aufgerufen. E21 module_status vor Patch. Branch master. $PREFIX/tmp. Kurz antworten.

## PRIO 1 — F5 FTS-Trigger-Asymmetrie
Trigger fts_sync_dima feuert NUR bei NEW.source='dima_chat'. save() macht KEINEN FTS-Insert. Folge: jeder Save mit source=manual/self_improve/kortex_archive ist im Talk-MATCH unsichtbar. 16403 Bestandszeilen, WAL.
ENTSCHEIDUNG NÖTIG: Trigger auf alle Sources erweitern (ein ALTER, idempotent) ODER FTS-Insert in save(). Ersteres ist sicherer für Bestand, Zweiteres sauberer für Zukunft. Vor Patch: Backfill-Test mit 1 Zeile.

## BEANTWORTET
F2 Futter: jack_errors.db hat 3170 errors, ALLE resolved=1. autolearn sucht unresolved und findet 0. FIX: autolearn lernt aus resolved ODER source=self_improve als Futter ODER neue Fehler einsammeln.
F3 CB: check_allowed() ist nirgends definiert, Aufruf nur jack_autofixer_shadow.py:135. FIX: Methode in jack_circuit_breaker.py ergänzen oder Aufruf dort entfernen.
F1 Stand: autolearn pid 508, State=S (sleeping), log stumm seit 15:42:37. KEIN 'sv down autolearn' im Live-Code. nohup-Zeilen = zweiter Startmechanismus neben runit. Verdacht: Prozess hängt oder Doppelstart.

## F4 Kortex-Referenzen (Import-Zahl = wer lädt es noch)
  jack_learn: 1 Importe
  jack_skill_builder: 1 Importe
  jack_briefing: 1 Importe
  kortex_memory: 4 Importe
  0 Importe = streichen/attic sicher. >0 = erst umhängen.

## F6 save() Caller (Tor-Ausbau beachten)
/data/data/com.termux/files/home/jack/jack_android.py:212:    img.convert("RGB").save(buf, format="JPEG", quality=SCREENSHOT_QUALITY)
/data/data/com.termux/files/home/jack/jack_callback_handler.py:53:            import jack_memory as _jm; _jm.save(fact,"Dima erwaehnte",intent="dima_fact")
/data/data/com.termux/files/home/jack/jack_explorer.py:64:                sk.save('explore_'+paket.split('.')[-1], plan, 'Auto-exploriert: '+paket)
/data/data/com.termux/files/home/jack/jack_explorer_deep.py:104:            sk.save(sname,{'steps':[
/data/data/com.termux/files/home/jack/jack_grid_vision.py:25:    img.save(buf, format="JPEG", quality=88)
/data/data/com.termux/files/home/jack/jack_planner.py:121:                    _sk.save(name, plan, 'Auto-gespeichert nach erstem Erfolg')

## F7 Tabellen-Zoo jack_memory.db (Nutzung in Live-Dateien)
  activity_log: 3
  app_packages: 0
  consolidated_knowledge: 0
  curated_knowledge: 1
  episoden: 3
  ingested_context: 6
  ui_skills: 0
  ui_transitions: 0
  vision_log: 0
  web_recipes: 0
  memory_vec: 1
  0 = tot/attic-Kandidat, >0 = leben. memory/memory_fts/memory_vec sind Kern.

## VERIFIZIERT HEUTE (nicht neu messen)
Topologie Live-Baum=jack/ Top-Level, jack-core=tot. M1 56 Kortex→jack_memory source=kortex_archive. BugH 16022 FTS-Backfill done. M2 self_improve→jack_memory. M3 Kortex-Import aus telegram weg. M3b Filter IN(dima_chat,manual,kortex_archive). Kortex-Rente C. Jev KANDIDAT_GESPERRT.

## OFFEN / REIHENFOLGE
1. F5 patchen (Prio1). 2. F1 autolearn-Hang klären (/proc/508 prüfen). 3. F3 check_allowed. 4. F2 Futter-Architektur. 5. F4 attic nach Import-Check. 6. F8 Restart-Reihenfolge Wächter/telegram/autolearn mit Drain. 7. F6 save() Tor. 8. F7 Zoo kartieren.