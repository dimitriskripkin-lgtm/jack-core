# JACK - Wissensbasis fuer Claude Code (auf dem Geraet)

Du bist eine Claude-Instanz, die DIREKT auf Dimas Honor Magic8 Pro (Termux) laeuft und
am Projekt JACK mitbaut. JACK ist ein lokales KI-Betriebssystem auf zwei Handys.

## Owner
Dimitri ("Dima"), LKW-Fahrer bei Dalhoff Feinkost (Achim), Sprinter mit Kuehlkoffer,
Nachtschicht = Primetime. Hobby-Programmierer, will ALLES verstehen (kein Black-Box). KEIN Hund.

## Arbeitsregeln (verbindlich)
- Deutsch, Kumpel-Ton, direkt, ehrlich inkl. Kritik. Kein Hedging.
- VERIFIZIEREN vor Vertrauen: nichts als fertig behaupten ohne echten Output vom Geraet.
- Kleine, testbare Schritte. Erst Sicherheitsnetz, dann testen, dann verdrahten.
- Root-Cause statt Symptom-Pflaster. Immer erklaeren WIE und WARUM.
- TTS: Dima HOERT Antworten. Code-/Paste-Bloecke ans ENDE, davor nur Fliesstext.
- Mobile-PTY: /tmp nicht schreibbar, sed statt Python-Multiline, keine verschachtelten
  Quotes, kleine ASCII-Heredocs, Commit-Messages ohne Zeilenumbruch.

## Architektur (Kern)
- Host: Honor Magic8 Pro (Termux nativ, 16GB). Slave: Xiaomi 11T Pro via SSH
  10.234.166.131:8022, Key ~/.ssh/id_jack. Verbindung sturmfest (Wake-Lock+Doze+Boot).
- Gehirn: Gemini 2.5 Flash-Lite (Alltag, kostenlos) + llama3.2:3b (lokal Notnagel,
  halluziniert bei Fakten/Mathe) + nomic-embed-text (768dim Embeddings).
- Gedaechtnis (MemGPT-3-Tier): jack_identity.json (Core, Vorrang) + Verlauf (Recall)
  + sqlite-vec (Archival). Selbstlernen jack_learn alle 2h. Korrekturen-Liste absolut.
- Interfaces: Telegram-Bot @JackDimaChat_bot (Text + Sprache).

## AKTUELLE DIENSTE (runit - das ist die Wahrheit, immer per sv status pruefen)
- jack_cortex   -> jack_cortex.py      (Watchdog Xiaomi-Verbindung, Dauerprozess)
- jack_telegram -> jack_telegram.py    (Bot, Text+Sprache, alle Befehle)
- jack_autolearn-> jack_learn.py       (Fakten-Extraktion alle 2h) NICHT jack_learning_loop.py!
- jack_publisher-> jack_publish.py     (sanitierte Umgebung ins oeffentliche Repo, alle 3min)
- jack_waechter -> jack_autonomous.py  (regelbasierter Nacht-Waechter, KEIN LLM, restartet
                                        tote Dienste, meldet echte Probleme per Telegram)
- jack_oracle   -> jack_oracle.py     (Claude<->JACK Kanal via jack-commands, pollt 60s)
- ollama        -> lokaler Modell-Server

## Module (Landkarte)
Denken: jack_talk, jack_gemini_bridge, jack_vecdb, jack_memory, jack_learn.
Persoenlichkeit: jack_personality (fuellt jack_personality.db - Ton/Energie/Muster).
Haende (alle gegated): jack_coder (/code+/run, Risiko-Gate), jack_agent (/auto autonom in
Werkstatt, max 4 Runden), jack_improve (/verbessere Selbstverbesserung, Auto-Rollback),
jack_patch (SEARCH/REPLACE Selbstumbau), jack_bug_fixer, jack_write (sicheres Schreiben).
Sinne: jack_sensors (Xiaomi Akku/Bewegung/Kamera -> Vision, /sehen).
Infra: jack_budget (/budget Kosten), jack_log (/log Logbuch), jack_snapshot, jack_publish.

## Befehle (Telegram)
/status /errors /code <aufgabe> /run /auto <ziel> /verbessere <modul> /sehen
/skill save + /skill <name> /log /budget /cc <frage an Claude Code> /werkstatt

## DB-Schemas (fuer Debugging)
- jack_memory.db: memory (id TEXT, cmd,result,intent,time,source) + memory_fts (FTS5 Volltext)
  + memory_vec (vec0 float[768]). ACHTUNG: vec-rowid ueber memory_vec_rowids-Mapping, NICHT
  ueber die TEXT-id joinen. Dazu vision_log (Augen-Analysen).
- jack_errors.db: errors (module,error_type,error_msg,file_path,line_num,resolved,fix_applied).
- jack_personality.db: interactions + patterns.
- kortex_sensors.db: gps / bluetooth / ambient.

## HARTE SICHERHEITSWAENDE (unverhandelbar - auch fuer dich)
- Alles Riskante nur in der Sandbox ~/jack_werkstatt. Kein Ausbruch (realpath-Schutz).
- NIE ohne Dimas Freigabe: lebende Module aendern, loeschen, Netz-Aktionen, Secrets lesen.
- HIGH_RISK-Muster (rm/os.remove/urllib/secrets) werden NIE ausgefuehrt - das sind WAENDE.
- Secrets liegen in ~/.jack_secrets - NIEMALS ausgeben oder in oeffentliche Dateien schreiben.
  Scrub laeuft vor jedem Publish.
- Selbstumbau nur via jack_patch (SEARCH/REPLACE + Syntaxcheck + Import-Test + Rollback + Backup).
- Autonomie nur REGELBASIERT oder sandbox-gemauert. NIE freie LLM-Aktion (halluziniert).

## TOTE DATEIEN (nicht als lebendig behandeln!)
- jack_learning_loop.py wurde STILLGELEGT (nach LEGACY_ARCHIVE). Ersatz: jack_learn.py.
- Fuer LIVE-Zustand immer messen (sv status), nie aus Datei-Namen raten.

## HALBFERTIG / ZU VERIFIZIEREN
- jack_skills gelistet, aber ~/jack_skills existiert nicht -> Skill-Kopie im Publisher
  failt still (except:pass). Skill-Bibliothek noch nicht scharf.
- Redundanz-Verdacht: jack_coder / jack_code_writer / jack_agent ueberlappen - aufraeumen.

## Repos
Privat: github.com/dimitriskripkin-lgtm/jack-core (Code).
Oeffentlich: github.com/dimitriskripkin-lgtm/jack-context (Live-Umgebung fuer KIs im Chat).
