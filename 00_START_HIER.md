# 00 START HIER — Pflichtzettel für JEDE KI (Claude, Grok, Gemini, Qwen, ...)

Du bist eine neue Session ohne Gedächtnis. Das ist normal. Dieser Zettel ersetzt das Gedächtnis.
Lies ihn ganz (3 Minuten), BEVOR du irgendetwas änderst, baust oder "drosselst". Stand 07.10.2026.

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
  nie fest einbauen. Aktuell gesehen: 10.176.117.131 (kann sich ändern). Ollama läuft nur hier.
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
- Heartbeats: `.heartbeat_<dienst>`; Deadman: `jack_overmind_result.json`, Alarm nach 3 h.
- Freigabe-Wege: Vorschlagsliste (`/vorschlaege`, `/vorschau`, `/freigeben`, `/ablehnen`), PENDING_EXEC/PENDING_WRITE, `.selfsee_pending`.

## 6. Bekannte Fallen (schon einmal teuer geworden)
- Äußere `except Exception: sleep` in einer Hauptschleife versteckt Abstürze. Immer melden.
- Hartkodierte IP statt SSH-Config. 13 Fallback-Stellen wurden am 07.10. nachgezogen.
- Ein "Tuning" ohne Handbuch zu lesen hebelt vorhandene Schalter aus (Runner-Takt 1 s fest -> Honor heiß).
- Zwei Kopien derselben Sache (persona, Freigabewege, Fehler-DBs). Vor jedem Neubau: gibt es das schon?
- Mehrere KIs mit gemeinsamer Zwischendatei kontaminieren sich. Eine Datei pro Vorgang.
- GitHub-Klon in der KI-Sandbox ist oft stale. Immer gegen die Live-Datei prüfen und `sha256` mitschicken.

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

## 9. Session-Ende-Pflicht
Was geändert wurde, in die Betriebshandbuch-Kapitel eintragen. Offene Punkte nennen. Neue Schalter in Abschnitt 5 aufnehmen.
