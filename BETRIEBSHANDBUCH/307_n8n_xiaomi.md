# 307 n8n auf dem Xiaomi (27.10.2026, Claude; Plan ChatGPT N1)

**Zweck:** n8n als Werkzeugkasten, den JACK benutzt (JACK bleibt Urteilsschicht). Kosten 0 EUR.

**Aufbau (gemessen):** Xiaomi Termux -> proot-distro Container ubuntu (Ubuntu 25.10 arm64) -> User n8n -> Node 24.22.1 (nvm, nur im Container; Termux-Node 25 unangetastet) -> n8n 2.44.7 (fest gepinnt, ~/jack_n8n). Lauscht NUR 127.0.0.1:5678 (per /proc/net/tcp als root geprueft). Zugriff vom Honor: ssh -N -L 8766:127.0.0.1:5678 xiaomi-jack, Browser http://127.0.0.1:8766. Owner-Konto von Dima angelegt 27.10.

**Geheimnisse:** im Container ~/.config/jack-n8n/key.env (N8N_ENCRYPTION_KEY), webhook.secret, service.env, alles 0600. Nie ausgeben. Key + database.sqlite nur gemeinsam sichern.

**Dienst:** Termux-runit $PREFIX/var/service/n8n. run: 30 s warten + Hitzesperre 45 C, dann proot-Start. finish: 120 s Pause nach Absturz (nicht bei sv down). Log $PREFIX/var/log/sv/n8n. Start dauert ~85 s. Stoppen: sv down n8n (im XIAOMI-Termux, SVDIR gesetzt).

**Vorfall 27.10. 07:16-07:44 (Claude-Fehler):** jack_xiaomi.run_shell laeuft standardmaessig als root (as_root=True). Installation lief dadurch als Android-root: Dateien root-eigen + SELinux-Kennung ohne Kategorien (s0 statt s0:c69,c256,c512,c768) -> n8n "Operation not permitted". Dienst ohne Bremse startete ~1100x neu -> Xiaomi Last/Hitze, hing bzw. startete neu. Behoben: chown 10069, chcon auf Termux-Kontext, 447 Symlinks als Termux-User neu angelegt, Neustart-Bremse. LEHRE: Fuer Termux-Arbeit IMMER run_shell(..., as_root=False). Neue Dienste nie ohne Probestart von Hand. Shell-Skripte ueber input_data schicken (sonst expandiert die Honor-Shell $-Ausdruecke).

**Offen:** Kalender-Ablauf (N1_workflow_kalender.json) inaktiv importieren, Header-Secret, Google-OAuth nur mit Dimas Freigabe; jack_n8n.py (Honor-Client) pruefen/installieren; Backup-Routine.

**Nachtrag 27.10.2026 08:30 (Claude) Notbremse + Notaus (Dima-Wunsch: "Handy heiss, miss durch")**
- XIAOMI-Dienst n8n_waechter (runit, NICHT cron: crond ist seit 09/2025 absichtlich aus wegen alter Titan-Startjobs in der Crontab): prueft jede Minute ~/n8n_waechter.sh; stoppt n8n + down-Datei bei CPU >= 48 C oder >= 3 Abstuerzen in 15 Min (svlogd-Zeit = UTC, date -u). Log ~/n8n_waechter.log. Trockentest Absturzzaehlung 3/3.
- HONOR jack_xiaomi_notaus.py (JACK_TUNE_XINOTAUS): messen | n8n_aus | n8n_an, alles as_root=False. Claude darf n8n auf Dimas Zuruf selbst stoppen.
- Skripte im Repo unter deploy/xiaomi_n8n/.
- Beobachtung: Ollama auf dem Xiaomi lief nach dem Neustart 07:4x nicht (pgrep), nicht angefasst.

**Nachtrag 27.10.2026 08:32:** Kalender-Workflow (N1_workflow_kalender.json) per n8n import:workflow INAKTIV importiert, ID 20oqHGmlPNa6Jawg "JACK N1 - Kalender, Bestaetigung erforderlich". Offen: Header-Auth-Credential (X-JACK-Secret aus webhook.secret) zuordnen, Google-Calendar-Credential nur nach Dimas OAuth-Freigabe, jack_n8n.py (Honor-Client, ChatGPT) pruefen/installieren, E2E-Testtermin.

**Nachtrag 27.10.2026 09:58 (Claude) Google-Kalender-Zugang VERBUNDEN**
- Google-Cloud-Projekt "JACK n8n", Calendar API an, OAuth-Zustimmung Extern/Testmodus, Testnutzer Dima, Web-Client (Redirect http://localhost:5678/rest/oauth2-credential/callback). Erster Client verlor seinen Schluessel (Google zeigt ihn nur EINMAL), zweiter Client genutzt.
- n8n-Zugang jackGoogleCal001 "Google Kalender (JACK)": clientId, clientSecret, oauthTokenData mit refresh_token (gemessen, ohne Werte).
- n8n meldet sich als localhost (N8N_HOST=localhost, N8N_EDITOR_BASE_URL=http://localhost:5678), lauscht weiter nur 127.0.0.1. Tunnel Honor: ssh -N -L 5678:127.0.0.1:5678 xiaomi-jack.
- Werkzeug jack_n8n_google.py (JACK_TUNE_N8NGOOGLE): fragt Client-ID/Schluessel ab (Schluessel unsichtbar), importiert per n8n-CLI, oeffnet Tunnel + Seite.
- Stopp-Fix: runit control/t beendet n8n gezielt (vorher traf sv down nur die proot-distro-Huelle!), Notbremse ebenso.
- ACHTUNG: Testmodus -> Google-Freigabe laeuft laut n8n-Doku nach 7 Tagen ab (ca. 03.11.). Vorher App auf "In Produktion" stellen oder neu verbinden.
- Offen: Zugang an Workflow haengen, Header-Secret, jack_n8n.py, Testtermin mit Dimas Knopf.

**Nachtrag 27.10.2026 10:12 (Claude) Ablauf scharf + Telegram-Knopf**
- Header-Auth-Zugang jackWebhookSec01 (X-JACK-Secret = webhook.secret) + Google-Zugang an Workflow 20oqHGmlPNa6Jawg gehaengt, per n8n publish:workflow veroeffentlicht, n8n neu gestartet. Webhook: POST http://127.0.0.1:5678/webhook/jack-kalender (nur Xiaomi lokal).
- jack_n8n.py (Honor, JACK_TUNE_N8N, Entwurf ChatGPT, Timeouts 20/30 s) + Secret ~/jack/.n8n_webhook_secret (0600, gitignored). Tests ohne echten Termin: falscher Schluessel 403, ungueltiger Termin 500 (abgelehnt), ohne Knopf PermissionError.
- jack_termin.py (JACK_TUNE_TERMIN): vorschlag() schickt Telegram-Knopf, confirm() nur Dimas Privatchat, Einmal-Code 10 Min, offene Freigaben logs/termin_pending.json (0600, gitignored). jack_telegram handle_callback: tm:-Knoepfe -> Thread. Backup logs/jack_telegram_vor_TERMIN_20261027.py.
- n8n-Neustart dauert ~3,5 Min wenn per Kill (finish-Pause 120 s greift, weil rc != TERM-Signal).

**Nachtrag 27.10.2026 10:12: ENDE-ZU-ENDE NACHGEWIESEN.** Dima drueckte "Ja, eintragen" -> JACK meldete event_id gh716nq0... -> Claude hat den Termin unabhaengig ueber den Google-Kalender-Connector gefunden (28.10. 11:00-11:15, Beschreibung mit request_id). Testtermin darf Dima loeschen.

**Nachtrag 27.10.2026 10:16 (Claude) Termin per Text/Sprache (JACK_TUNE_TERMINTEXT)**
- jack_termin_parse.erkenne(): Tag (heute/morgen/uebermorgen/Wochentag/am TT.MM.) + Uhrzeit (um elf, um 11 Uhr, 9:30, halb/viertel nach/vor) noetig; ausgeloest nur wenn Satz mit Tag beginnt oder Termin/Kalender/eintragen vorkommt; Fragen ignoriert. 1-6 Uhr ohne morgens/frueh/nachts -> Nachmittag. Dauer 1 h. Zeitzone per zoneinfo (pip tzdata 2026.5 auf dem Honor installiert; ohne tzdata kein Vorschlag).
- Telegram handle() direkt nach S1 und Sprach-Handler nach S1: erkannter Termin -> jack_termin.vorschlag(..., send_kb) -> Knopf. Eingetragen erst nach Dimas Ja.
- Bekannte Grenze: "Ich muss morgen um elf zur Werkstatt" wird NICHT erkannt (beginnt nicht mit Tag, kein Termin-Wort) -> "Termin morgen um elf Werkstatt" sagen. Unsinnige Saetze wie "Morgen um elf bin ich muede" koennen einen Knopf erzeugen -> Abbrechen.

**Nachtrag 27.10.2026 10:22:** Feldtest Dima "Stelle mir einen Termin fuer morgen um 16 Uhr" -> Titel war "Stelle mir fuer" (Fuellwoerter). Fix: stell/mach/leg/setz/erstell, mir/mich/uns, fuer/an, eine/neue(n) werden entfernt, sonst Titel "Termin". Eingetragener Termin per Google-Kalender-Connector auf "Termin" umbenannt. Doppelter Knopfdruck -> "Knopf nicht mehr gueltig" (Einmal-Code wirkt).

**Nachtrag 28.10.2026 (Claude) Playlist-Rettung "Musik gut" (JACK_TUNE_MUSIKGUT), Freigabe Dima 03:47 "Go"**
- Quelle: Google Takeout Teil 1 (YouTube-Wiedergabeverlauf.html, 48.712 Eintraege 19.04.2024-25.10.2026). Rest des Takeouts (146 GB) unnoetig.
- Befund: Hoerbruch ~10.08.2025 (Playlist geloescht). Auswahl: vor Bruch >= 8x gehoert UND 01.04.-10.08.2025 >= 2x -> 817 Videos, meistgehoert zuerst (Top: Tiesto Mockingbird 54x). Auswertung: ARBEITSPLATZ/BUEROS/claude/musik_gut_auswahl.py.txt -> logs/musik_gut_ids.txt (gitignored, sha 3e2470656726ddcd).
- jack_musik_gut.py (HONOR) -> Xiaomi as_root=False: schreibt ids.txt + fuell.js (deploy/xiaomi_n8n/musik_gut_fuell.js) nach Container ~n8n/yt_rettung, node holt Zugang aus n8n-Credential jackYouTube00001 (Export sofort geloescht), Token-Refresh, private Playlist "Musik gut (wiederhergestellt)", fuellt bis Quote. Zustand ~n8n/yt_rettung/state.json (pos, ok, skip, playlistId). Log logs/musik_gut.log.
- YouTube-Quote 10.000/Tag, insert = 50 -> ~190/Tag, Reset Mitternacht Pazifikzeit (08:00/09:00 Bremen). HONOR-Cron 15 9 * * * (Marker JACK_TUNE_MUSIKGUT) bis fertig, danach Zeile entfernen.
- Feldbefund: Video ohne Titel (geloescht/privat) -> 400 failedPrecondition. v2: 1x nach 4 s wiederholen, dann ueberspringen; 8 Fehler am Stueck -> Stopp.
- Grenze: Google-Freigabe im Testmodus laeuft ~03.11. ab -> danach FEHLER token; dann App in Produktion stellen oder YouTube neu verbinden.

**Nachtrag 28.10.2026 (Claude, Inventur I15, Entwurf ChatGPT):** jack_termin Pending-Datei jetzt unter fcntl-Lock (_pending_lock) fuer vorschlag und confirm, kein Telegram/n8n-Aufruf unter Lock. Live: Lock ok. Telegram neu gestartet 13:31.
