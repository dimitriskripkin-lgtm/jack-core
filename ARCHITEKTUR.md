# JACK - Architektur und Bauanleitung

## Was JACK ist
Persoenliche KI-Betriebsschicht auf zwei Android-Geraeten (Termux).
Honor Magic8 Pro = Gehirn/Host. Xiaomi 11T Pro = Arm/Executor via SSH.
Offline-first, unter Dimas voller Kontrolle. Exit-Vehicle fuer Unabhaengigkeit.

## Die 7 Schichten (von unten)
1. FUNDAMENT: Termux nativ, Magisk (Root Xiaomi), SSH-Ruecken (10.234.166.131:8022,
   Key ~/.ssh/id_jack). Verbindung sturmfest: Wake-Lock + Doze-Whitelist + Boot-Autostart.
2. PERSISTENZ: jack_errors.db, jack_memory.db (+sqlite-vec float[768]), jack_personality.db,
   kortex_sensors.db, jack_identity.json (Core), ~/.jack_secrets (rotiert).
3. MODELL-ZUGANG:
   - Alltag: jack_gemini_bridge -> Gemini 2.5 Flash-Lite (kostenlos, Retry+Backoff gegen 429)
   - Tief: Claude Code headless (read-only Berater, kennt Codebasis, per /cc)
   - Lokal: Ollama (llama3.2:3b Notnagel + nomic-embed-text)
4. GEDAECHTNIS (MemGPT-3-Tier): Core=identity.json (Vorrang, Korrekturen absolut) |
   Recall=Verlauf | Archival=Vektorsuche | Selbstlernen=jack_learn (alle 2h).
5. DENKEN: talk_to_gemini() fuehrt Core+Recall+Archival+Live-Status zusammen, ruft Gemini.
   jack_personality wertet Ton/Energie/Muster aus.
6. HAENDE (alle gegated): jack_write (Werkstatt+Bestaetigung), jack_coder (/code+/run,
   Risiko-Gate), jack_agent (/auto autonom in Werkstatt, max 4 Runden), jack_improve
   (/verbessere Selbstverbesserung mit Auto-Rollback), jack_patch (SEARCH/REPLACE), jack_bug_fixer.
7. AUTONOM (regelbasiert, KEIN freies LLM): jack_cortex (Watchdog Xiaomi+Heilung),
   jack_waechter=jack_autonomous.py (Nacht-Waechter, restartet tote Dienste, meldet echte
   Probleme), jack_autolearn (Heartbeat 2h), jack_publisher (Live-Umgebung ins Repo, 3min),
   jack_oracle (Claude<->JACK bidirekt. Kanal via GitHub, pollt 60s).

## Interfaces
Telegram-Bot @JackDimaChat_bot: Text + Sprache (whisper.cpp -> Gemini -> ElevenLabs).
Befehle: /status /errors /code <aufgabe> /run /auto <ziel> /verbessere <modul> /sehen
/skill save + /skill <name> /log /budget /cc <frage an Claude Code> /werkstatt

## Sicherheitsprinzipien
- Werkstatt-Sandbox (~/jack_werkstatt), realpath-Ausbruchschutz.
- HIGH_RISK-Muster blockieren Ausfuehrung (loeschen/netz/secrets) - das sind WAENDE.
- Zwei-Schritt-Bestaetigung fuer Schreiben, kein Auto-Apply.
- Ehrlichkeit: nie behaupten was er nicht kann, Live-Daten statt Gedaechtnis-Raten.
- Chat-Code fasst nie die lebenden Module an - nur ueber Patch-Gate.
- Secrets nie ins Terminal/Chat/oeffentliche Datei. Scrub laeuft vor jedem Publish.
- Autonomie nur regelbasiert oder sandbox-gemauert (LLMs halluzinieren).

## LIVE bewiesen (erledigt - nicht mehr als offen behandeln)
- Keys rotiert (alte exponierte getauscht).
- Xiaomi-SSH sturmfest (nach Reboot selbstheilend bewiesen).
- Entscheidungs-Logbuch (jack_log, /log) laeuft.
- AUGEN: Xiaomi-Kamera -> Vision live verifiziert (vision_log).
- SELBSTVERBESSERUNG: /verbessere -> Patch -> Freigabe -> Auto-Rollback + Commit (LIVE bewiesen).
- Kosten-Bremse (jack_budget), Skill-Speichern, autonomer Agent (/auto) gebaut.

## OFFEN / ZU VERIFIZIEREN
- Bug-Fixer (jack_bug_fixer) einmal live an kontrolliertem Fehler testen (Datei+Log da,
  echter Testlauf noch nicht bestaetigt).
- Source/Confidence im Gedaechtnis auswerten (source-Feld existiert, Auswertung offen).
- jack_skills scharf machen: ~/jack_skills existiert nicht -> Publisher-Kopie failt still.
- raw-CDN-Cache: Zustellung der Live-Umgebung an KIs haengt (liegt an GitHub-raw, nicht JACK).

## Naechstes Level (Nordsterne)
- PROAKTIV: JACK meldet sich von selbst, schlaegt Aktionen vor (Waechter meldet schon Probleme).
- XIAOMI-LIVE-STATUS in den Publisher (Akku/Bewegung sichtbar machen).
- GPS-Fahrtenbuch getriggert vom Bewegungssensor (akkuschonend, Tasker vorhanden).
- GESTUFTE AUTONOMIE: Risiko-Stufen-Matrix (lesend=allein, gefaehrlich=Dima).
- OFFLINE-HIRN: 7B+ Modell wenn bessere Hardware da (aktuell >3B = OOM).
