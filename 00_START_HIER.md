# 00 START HIER — Pflichtzettel für JEDE KI (Claude, Grok, Gemini, Qwen, ...)

## 0. NEU 21.10.2026 – Claude-Session-Start (zuerst!)
1. Lies `claude/KONTEXT_CLAUDE_20261021.md` im claude.ai-Projekt "Jack" (kompletter Arbeitskontext, Regeln, offene Punkte).
2. **JACK-Zugriff = Connector "JACK-MCP"** (seit 21.10. in claude.ai, Rolle `claude`, Header Authorization Bearer, kein OAuth; create_mission und ap_post fragen Dima vorher). Als Erstes `start_hier(wer="claude")`. Fehlt der Connector: Dima aktiviert ihn unter Konnektoren. Reserve: Werkbank nach `claude/WERKBANK_HELFER.md` (nur Cloud-Session mit Shell).
3. Lies die neueste `claude/UEBERGABE_CLAUDE_*.md` (Projekt), dann den Briefkasten `ARBEITSPLATZ/BUEROS/claude/eingang.md`.
4. Neueste Handbuch-Kapitel: 291–299 (Intent zuerst, Lagebild/Fahrmodus, Chatlog, Versatz-Fix, Tasker-Brücke, Xiaomi-Karte, Selbstbild, Timer/Medien, zentraler Sende-Helfer).

Du bist eine neue Session ohne Gedächtnis. Das ist normal. Dieser Zettel ersetzt das Gedächtnis.
Lies ihn ganz (3 Minuten), BEVOR du irgendetwas änderst, baust oder "drosselst". Stand 11.10.2026 (Abschnitt 0: 21.10.).

## 1. Wahrheitsrangfolge (bei Widerspruch gewinnt die höhere Zeile)
1. Die LIVE-Datei auf dem Honor (MCP `read_file`). Honor ist Wahrheit, GitHub kann stale sein.
2. Das Betriebshandbuch-Kapitel des Moduls: `BETRIEBSHANDBUCH/NN_modul.md` (Tools `handbuch_index`, `handbuch_kapitel`).
3. Dieser Zettel.
4. Alles andere ist ARCHIV und kann veraltet sein: JACK_WAHRHEIT.md (23.09., alte IP), ONBOARDING.md (02.09.),
   ARCHITEKTUR.md, JACK_KOENIGSDOKUMENT_*, JACK_UEBERGABE_v28, HANDOFF_*, Projekt-Extrakt "v14" (31.08.).
   Nutze sie für Geschichte, nicht für Fakten über heute.

## 2. Pflichtablauf vor JEDER Änderung (kein Abkürzen)
1. `start_hier()` lesen (= dieser Zettel) und `handbuch_kapitel('<modul>.py')` für das Ziel-Modul lesen.
2. Live-Datei lesen. Alle `JACK_TUNE_*`-Marker im betroffenen Bereich verstehen: jeder Marker ist eine
   bewusste frühere Entscheidung. Nicht ohne Grund überschreiben.
3. Vorhandene Schalter prüfen, bevor etwas "gedrosselt" oder neu gebaut wird (Abschnitt 5).
4. Existiert die Funktion schon? Erst `handbuch_index(suche)` und Repo-Suche, dann bauen. Dima hat schon
   mehrfach 6 gleiche Dinge gebaut, weil die KI nicht nachgesehen hat.
5. Patch per Mission: `py_replace` mit `file` (voller Pfad, NICHT `path`), `old`, `new`, `sha256_old`, `sha256_new`
   (Hash jeweils über den String `old`/`new`, nicht über die Datei). Ersetzt nur das ERSTE Vorkommen.
   Kompiliert .py automatisch und rollt bei Fehler zurück.
6. Danach: `sv_restart` des Dienstes + `sv_ok` prüfen. Ohne Restart läuft der alte Code im RAM weiter.
7. Nachweis: Ergebnis wirklich prüfen (Log, Status), nicht nur "ok:true" glauben.
8. Kapitel im Betriebshandbuch um 2 Zeilen ergänzen (was, warum, Marker). Wenn du etwas Neues baust: neues Kapitel.

Das MCP erzwingt Punkt 1: Jeder schreibende `create_mission`-Aufruf wird beim ersten Mal abgelehnt und
liefert dir den Auszug dieses Zettels plus Kapitelauszug plus eine Tages-`quittung`. Mit
`extra: {"quittung":"<code>", ...}` wiederholst du den Aufruf. (Modul `jack_handbuch_gate.py`, Marker JACK_TUNE_HBGATE.)
Die Quittung gilt nur für heute und je Kapitel. Sie ist kein Trick, sie ist der Beweis, dass du gelesen hast.

## 3. Was JACK ist (kurz)
JACK = Just Autonomous Command Kit. Selbst gebauter autonomer Reparatur- und Programmierassistent auf zwei Android-Handys.
Besitzer: Dima (Nachtschicht-LKW-Fahrer, Selbstlerner Python, bedient alles mit einem Daumen).
- HONOR Magic8 Pro = Gehirn/Host. Kein Root. Termux, Shizuku/rish. Hier läuft ALLES Wichtige und der MCP-Server.
- XIAOMI 11T Pro = Muskel/Worker. Magisk-Root. SSH-Alias `xiaomi-jack` Port 8022. IP wechselt per DHCP,
  nie fest einbauen. Zuletzt gesehen 11.10.: 172.29.165.131 (kann sich ändern). Ollama läuft nur hier.
- Pfade IMMER voll: Code `/data/data/com.termux/files/home/jack`, Dienste `/data/data/com.termux/files/usr/var/service`.
  In Skripten nie `~` (os.path.expanduser benutzen).
- Dienste auf dem Honor (runit, `sv`): jack_telegram, jack_cortex, jack_waechter (Logik in jack_autonomous.py!),
  jack_autolearn, jack_publisher, jack_focus_monitor, jack_missions (Runner), dazu jack_mcp und cloudflared.
- Mission-Pipeline: KI -> `create_mission(act, extra)` -> `missions/pending/` -> `jack_mission_runner.py` ->
  `done|fail` + Zeile in jack_memory.db. Nur Acts aus `jack_acts.py` (Whitelist). Kein freies exec.
- Telegram: `jack_telegram.py` (sehr groß), Chat-Router `jack_chat_router.py` (Lanes FACT/EXPLAIN/DIAG/TALK).
  `send(text)` nimmt GENAU EIN Argument. Callbacks: `jack_callback_handler.py`.
- Gedächtnis: Graph `jack_graph.db` (Fakten, geht VOR identity.json), `jack_memory.db` (Verlauf).
- Modelle: Talk = Groq gpt-oss-120b (darf NUR reden, nie SSH/ADB/exec). Technik = Gemini 2.5 Flash-Lite.
  Ollama (llama3.2:3b) = Fallback nur auf dem Xiaomi, standardmäßig AUS (Entscheidung 28.09., ZETTEL_20260928_OLLAMA.md).
- Publisher: `jack_publish.py` pusht nur den Kontext (`~/jack-context`), NICHT den Code. Code-Commits sind manuell,
  deshalb kann GitHub hinter dem Honor zurückliegen.

## 4. Eiserne Regeln
- Groq darf nur TALK. Kein Chat-Modell führt SSH/Shell aus. Kein Freitext-exec, nirgends.
- KEIN Ollama auf dem Honor. Kein Autonomie-Level erfinden. Keine Rechte erweitern.
- Keine Tilde in Skripten. Keine festen Xiaomi-IPs (SSH-Alias oder `ssh -G xiaomi-jack`).
- `setsid` für SSH-Hintergrundprozesse auf dem Xiaomi. `git reset --hard origin/master` auf dem Xiaomi nur bewusst.
- RAM = MemAvailable (nicht MemFree). Sensor-Temperatur durch 1000 teilen (thermal_zone66/68 zeigten am 07.10. dauerhaft 105, vermutlich Platzhalter, ungeprüft; echte Zonen lagen bei ~47).
- Geheimnisse (config.ini, Token, .ssh) nie ausgeben oder committen. Das Repo ist öffentlich.
- Telegram-Fehler dürfen nie still verschluckt werden (Marker JACK_TUNE_SICHTBAR: Fehler werden gemeldet).
- Python-Falle: Ein Name, der irgendwo in einer Funktion zugewiesen wird (auch `import os`), ist in der ganzen Funktion lokal.
  Vorheriger Gebrauch = UnboundLocalError. Vor jedem Patch `pyflakes` im Kopf mitlaufen lassen.
- Keine Selbstbefehle auf Verdacht: erst messen, dann ändern. Nichts raten, nachsehen.

## 5. Vorhandene Schalter und Takte (VOR dem Bauen prüfen)
- `~/jack/.mission_boost`: Runner holt Git im 1-s-Takt statt 30 s. Schaltet sich nach 15 Min selbst ab (JACK_TUNE_BOOSTTTL).
  Standard-Poll des Runners 30 s. Die lokale Queue-Prüfung läuft immer im 1-s-Takt (billig).
- `~/jack/.ollama_lock`: Ollama gesperrt. `missions/STOP`: Runner beendet sich. `~/jack/.focus_stop`: Focus-Monitor aus.
- `jack_tune.json`: Feinabstimmung einzelner Module. `jack_acts.py`: Whitelist aller Acts (+ Freigabe-Flag).
- Focus-Monitor pollt Xiaomi alle 15 s, bei fehlendem Xiaomi alle ~60 s.
- Heartbeats: `.heartbeat_<dienst>`; Dead-Man: `jack_deadman.py` (Cron */30) prüft `.heartbeat_jack_waechter` und `jack_health_now.json`, Telegram nach 3 h Stille, höchstens alle 3 h (Kap 271).
- Freigabe-Wege: Vorschlagsliste (`/vorschlaege`, `/vorschau`, `/freigeben`, `/ablehnen`), PENDING_EXEC/PENDING_WRITE, `.selfsee_pending`.
- Neu seit 21.10. (Stand 24.10.): `~/jack/.heat_paused_autolearn` = Hitzebremse hat Autolearn gestoppt, Wächter startet ihn unter 55 °C wieder (Kap 300). `~/jack/.fahrmodus` + `logs/telegram_fahrt_queue.jsonl` = Fahrmodus (MBUX-Bluetooth) und Puffer, Sammelmeldung nach dem Aussteigen (Kap 292/299). `~/jack/.sperrliste_apps` = 24 Xiaomi-Apps, nie öffnen, Benachrichtigungen nur zählen (Kap 296). `logs/link_inbox.jsonl` = Video-Links für Claude (Kap 302).
- `~/jack/.gemini25_weg` = nach einem 404 biegt jack_modelmap Gemini 2.5 auf 3.5-flash um (etwa 15-fach teurer). Fehlt = 2.5. Not-Aus: `.recovery_off` (Recovery), `.aenderung_off` (Änderungs-Auskunft), `.mcp_roles_off` (Rollen-Auth aus, Rückfall alter Token, seit 24.10. ohne Token zu), `.oauth_off`.
- jack_budget LIVE (gemessen 24.10.): text 10000 Aufrufe/Tag, Wochendeckel 8 EUR (Dima 15.10.). Die Zahlen 600/3 EUR in Abschnitt 12/13 sind veraltet.

## 6. Bekannte Fallen (schon einmal teuer geworden)
- Äußere `except Exception: sleep` in einer Hauptschleife versteckt Abstürze. Immer melden.
- Hartkodierte IP statt SSH-Config. 13 Fallback-Stellen wurden am 07.10. nachgezogen.
- Ein "Tuning" ohne Handbuch zu lesen hebelt vorhandene Schalter aus (Runner-Takt 1 s fest -> Honor heiß).
- Zwei Kopien derselben Sache (persona, Freigabewege, Fehler-DBs). Vor jedem Neubau: gibt es das schon?
- Mehrere KIs mit gemeinsamer Zwischendatei kontaminieren sich. Eine Datei pro Vorgang.
- GitHub-Klon in der KI-Sandbox ist oft stale. Immer gegen die Live-Datei prüfen und `sha256` mitschicken.
- rish (Shizuku) verliert stdout oder meldet "Failed transaction": Ausgabe erst nach /data/local/tmp, dann nach /sdcard kopieren (RISHTMP, Kap 292).
- `cmd media_session dispatch` trifft die "Media button session", oft das Claude-Vorlesen statt Spotify. Die Honor-Uhr ignoriert die Timer-Länge, deshalb JACK-eigener Timer (Kap 301).
- `.xi_hb_down` ist nur der 3-h-Abkühlstempel der Wächter-Meldung, KEIN Zustand "Xiaomi weg" (wird nie gelöscht). Zustand immer frisch messen (Kap 303).
- Teilwort-Schlüsselwörter täuschen: "log" steckt in "Logik", "dienst" in "Dienstag". Ganze Wörter prüfen. Zähler über alle Zeiten (missions/fail) machen Selbsttests dauerrot, Zeitfenster nehmen. Vergessene Arbeitsdateien (jack_mission_active.json vom 24.08.) erzeugten Wochen später Meldungen (Kap 303).

## 7. Wegweiser
- Alle Kapitel: Tool `handbuch_index(suche)`. Ein Kapitel: `handbuch_kapitel('jack_xyz.py')`.
- Bekannte Bugs / Modulkarte (Waisen): im Projekt "Jack" `areas/jack-modulkarte.md`, Betriebshandbuch-Index `BETRIEBSHANDBUCH.md`.
- Regeln für Entwickler: `ENTWICKLER_REGELN.md`. Vor-dem-Patch-Liste im Projekt: `claude/VOR_DEM_PATCH_CHECKLISTE.md`.

## 8. Umgang mit Dima
Deutsch, direkt, locker. Immer Gerät labeln: HONOR: oder XIAOMI:. Befehlsblöcke zu einem zusammenfassen, 30-40 Zeilen max,
Code ans ENDE der Antwort, Ausgaben mit `| tail -20`. Sicherheitswarnung VOR einem riskanten Befehl.
Nie nach Schlaf oder Pause fragen, kein Kommentar zum Tempo. Kein Rumfragen, wenn die Antwort im System steht.
Dima setzt die Prioritäten. Unsichere Annahmen kennzeichnen statt behaupten.

## 10. Arbeitsplatz (gemeinsames Büro)
Ordner ARBEITSPLATZ/ auf der Honor. Rufe start_hier(wer="claude"|"grok"|"gemini") bzw. buero(wer) auf: du bekommst Regeln, offene Punkte, Eingang, Journal, Roadmap. Notizen mit ap_notiz, Session-Ende mit ap_journal. Fremde Büros nur an eingang.md anhängen. Kanal: ap_lese holt Post, ap_post schreibt (Rundengrenze 10 ohne Dima, Notaus missions/STOP), ap_claim reserviert Module vor dem Patchen (Kapitel 235). Details: Handbuch-Kapitel 234.

## 11. Neu seit 08.10.2026 (zuerst lesen, wenn du lange weg warst)
- Aufgeraeumt: ~200 Dinge und 19 tote Module nach Attic/ (Kap. 246). Karte aller Module: MODULKARTE.md. Gesamtueberblick: Kap. 247.
- Xiaomi-Zugriff NUR ueber jack_xiaomi.run_shell (Schutzschalter + Schnellpfad, Kap. 244). Keine neuen eigenen ssh-Aufrufe bauen.
- Telemetrie laeuft: telemetry/telemetrie_JJJJ-MM.jsonl, alle 5 Min Temperaturen, Akku, RAM, Last, Top-Prozesse beider Handys (Kap. 245). Stop: Datei .telemetry_stop. Nie ins Repo.
- Lade-Ton: Akku unter 15 Prozent und nicht am Laden -> Vibration + Ansage (JACK_TUNE_LADETON, Kap. 243).
- Cloud-Nachtlauf: geplante Aufgabe 'JACK Nachtlauf' taeglich ca. 03:20 MESZ (Stufe A2) liest ARBEITSPLATZ/gemeinsam/auftraege.md, bearbeitet nur Auftraege mit Status OFFEN, schreibt gemeinsam/morgenbericht.md. Regeln: auftrag_regeln.md. Ohne neue OFFEN-Auftraege tut er nichts (Stand 09.-11.10.: leer).
- Dienst jack_qwen (jack_qwen_client.py): seit 22.10.2026 auf Dimas Wunsch AUS (down-Datei). Nicht loeschen, nicht ohne Dima starten.
- Token-Rotation steht aus (eine Token pro KI-Rolle). Token nie ausgeben.
- Logs werden nie automatisch zu Fakten. Auswertungen nur als Vorschlag.
- Grosse Datei lesen: read_file einzeln, nie parallel (vermischt Antworten), Feld 'path' der Antwort pruefen.

## 12. Neu seit 10./11.10.2026
- ARENA (messbares Lernen): jack_arena.py = deterministischer Richter (Kap 273), jack_arena_runner.py = Runner mit Gemini-Pruefling (Kap 274). Aufgaben, Loesungen, Holdout NUR privat in /data/data/com.termux/files/home/jack_arena_private (nie ins Repo, nie als Lernmaterial oeffnen). Kategorie C (Codeausfuehrung) gesperrt bis Sicherheitsrahmen C steht.
- Arena-Schalter: `~/jack/.arena_off` (Not-Aus), `~/jack/.arena_holdout_ok` (Holdout einmalig, wird geloescht), `~/jack/.arena_einrichtung` mit `YYYY-MM-DD N` (Tagesgrenze nur an diesem Tag anheben, max 600).
- jack_budget: text 600 Aufrufe/Tag (seit 11.10., vorher 300), Wochendeckel 3 EUR bleibt. Arena darf davon max 300/Tag. LIMITS wird beim Import gelesen: nach Aenderung Dienste neu starten (Kap 39).
- NIE jack_missions per Auftrag (exec_proposed) neu starten: Selbstabschuss, Auftrag bleibt haengen (Kap 275). jack_mcp auch nicht.
- Log-Dienste: log/run von sshd, ssh-agent, cloudflared ist ein Symlink auf die gemeinsame svlogger-Datei. Vor jedem Schreiben `readlink -f`, nie durch Symlinks schreiben (Kap 272). cloudflared laeuft als Dienst mit `--protocol http2`.
- Kein `pgrep -f '<muster>'` in einem Befehl, dessen eigene Kommandozeile das Muster enthaelt (trifft sich selbst). Stattdessen `ps -A -o pid,args | awk`.
- Hitze Honor: Hauptursache war die MeinVodafone-App (com.appseleration.android.selfcare, CarrierService wird vom System neu gebunden). Beobachtung: reports/selfcare_cpu.log alle 5 Min durch jack_honor_watch (Kap 270).
- Karte: reports/karte_roh.py zaehlt jetzt auch Cron/Shell/crontab-Aufrufer (MODULKARTE.md Nachtrag).
- git_publish: Commit-Nachricht kurz halten (rund 100 Zeichen), laengere werden abgelehnt.

## 13. Neu seit 11./12.10.2026 (ersetzt Teile von 12)
- Arena Kategorie C ist FREI: Sicherheitsrahmen jack_arena_sandbox.py v5 (Kap 276), Code-Aufgaben C01-C08 und C-v2 (Generator privat). Richter-Kennzahl public_overfit (sichtbar gruen, versteckt rot).
- Runner-Schalter: ARENA_MODEL (Flash-Lite Standard), ARENA_TOOLS (Standard grep2), ARENA_RULES_FILE. `.arena_einrichtung` jetzt `YYYY-MM-DD N EUR` (max 10000 Aufrufe, max 4 EUR, nur an dem Tag). Nur EIN Runner-Lauf gleichzeitig (Lock), auch Selbsttest.
- Jede Aenderung: Vorregistrierung VOR dem Lauf (ARBEITSPLATZ/gemeinsam/arena/*_vorregistrierung.md), frischer Satz, dann Holdout. Verbrauchte Holdouts nach jack_arena_private/holdout_verbraucht/ + seal.
- JACK als Lerner: jack_arena_lerner.py (Kap 277). Erste eigene Regel hat Tor + Holdout bestanden (12.10.). Uebernahme in JACKs echte Regeln NUR mit Dimas Ja und nach Abstraktion (Ebene 3).
- Phone-Haende: jack_phone_senses.py (Kap 278) = L0 nur lesen, Tabu/Allowlist/Not-Aus ~/jack/.phone_off/Audit. Phase 3 (L1-Aktionen) NUR nach Dimas Go. rish schreibt zufaellig auf stderr: immer stderr=STDOUT.
- jack_budget-Wochenlimit 3 EUR teilen Arena und JACK. Grosse Arena-Serien koennen JACKs Gemini bis Montag sperren.

## 8b. Uebergabe 12.10.2026
Neue Session: zuerst ARBEITSPLATZ/gemeinsam/uebergabe_claude_20261012.md lesen (Arena, Lernkreislauf, Phone, offene Entscheidungen). Davor: uebergabe_claude_20261011.md.
Aeltere Uebergabe 11.10.2026: ARBEITSPLATZ/gemeinsam/uebergabe_claude_20261011.md lesen (Stand, Arena, offene Punkte, Lehren). Aeltere: uebergabe_claude_20261009.md. Jack-Onboarding: onboarding_jack_20261009.md. Kapitel 250-255 = Tiefenanalyse.

## 9. Session-Ende-Pflicht
Was geändert wurde, in die Betriebshandbuch-Kapitel eintragen. Offene Punkte nennen. Neue Schalter in Abschnitt 5 aufnehmen.

- Neu 26.10.: `jack_melderegeln.json` = Regeln der Meldestelle (Kap 304; ins Attic = alte Logik), `logs/telegram_nur_log.jsonl` = still protokollierte Meldungen, `logs/.tg_m2_seen.json` = Dedupe-Stempel. Router: JACK_TUNE_TALKVORDIAG (Kap 05).

- Neu 26.10.: `~/jack/.klingel_off` = Briefkasten-Klingel aus (Kap 305), Cron */5 jack_klingel.py.

- Neu 26.10. (Umgang mit Dima, Dima: "exakt so"): Anleitungen in kleinen nummerierten Teilen. Alles fuer Termux als fertiger Befehl; Dima baut nie selbst Werte/Keys in Befehle ein. Werte holt der Befehl per Abfrage ("X einfuegen:"), ein Befehl pro Wert: Befehl rein, Enter, Wert rein, Enter. Jeder Befehl meldet sichtbar Erfolg.

- Neu 27.10.: n8n auf dem Xiaomi (Kap 307). WICHTIG: jack_xiaomi.run_shell ist standardmaessig ROOT - fuer Termux-Arbeit as_root=False setzen.

- Neu 27.10.: Xiaomi heiss/haengt? python3 jack_xiaomi_notaus.py messen | n8n_aus (Kap 307). Nach jedem Arbeitsblock Doku + Commit/Push (Dima-Regel).

- Neu 27.10.: Kalender per JACK: "Morgen Werkstatt um elf" (Text/Sprache) -> Knopf -> n8n (Xiaomi) -> Google. Google-App im Testmodus: Freigabe laeuft ca. 03.11. ab (Kap 307).
