# 308 Fahrt-Lage fuer Grok-Bot und Tesla (28.10.2026, Claude, Dima-Go 13:06)

**Zweck:** Grok im Tesla hat kein eigenes Gedaechtnis. Test 28.10. 13:12 (Codewort im Grok-Bot, Tesla-Grok findet es nach "guck bei Jack"): Was der Grok-Bot ("Jack") im Verlauf hat, kann Tesla-Grok sofort lesen. Einbahn Bot -> Auto.

**Aufbau:**
- Privates Repo `dimitriskripkin-lgtm/jack-gedaechtnis` (angelegt per gh auf dem HONOR, Klon ~/jack-gedaechtnis). Inhalt: START.md (Regeln), lage/aktuell.md (automatisch), entscheidungen/offen.md (Claude pflegt), entscheidungen/von_dima.md (Rueckweg, nur anhaengen), Tesla/ und Grok/notizen.md.
- `jack_fahrtlage.py` (JACK_TUNE_FAHRTLAGE): liest Dienste (11 Kern), Honor Akku/Temp (jack_lagebild.honor), Xiaomi Temp + n8n (run_shell as_root=False), Fails 24 h, Playlist-Stand, offene Entscheidungen; schreibt lage/aktuell.md, commit + push. Cron HONOR `50 */2 * * *`, Log logs/fahrtlage.log. `--kein-push` zum Testen.
- Oeffentliches jack-core bleibt frei von Gespraechsinhalten (Grund: Git-Historie vergisst nicht).

**Regeln:** Keine Geheimnisse, keine Chat-/Benachrichtigungstexte. Repo ist Spiegel, kein Befehlskanal: Eintraege in von_dima.md fuehrt JACK nicht automatisch aus, Claude prueft, Dima bestaetigt.

**Erster Lauf 13:14:** 11/11 Dienste, Honor 94 %/34 C, Xiaomi 44,3 C, n8n laeuft, 2 Fails/24 h, Playlist 386/817, Push 1170bd0.

**Offen:** Grok-Bot braucht Lesezugriff auf das private Repo (Dima im Grok-GitHub-Connector). Rueckweg von_dima.md -> Claude-Pruefung noch manuell. Branch-Schutz fuer private Repos ist bei GitHub Free nicht verfuegbar, und Grok schreibt mit Dimas Identitaet (Admin) -> Schutz waere ohnehin umgehbar; Regel "nur anhaengen" + Git-Historie als Sicherung.

**Nachtrag 28.10.2026 14:27 (Claude, Dima-Go 14:22) Grok-Briefkasten JACK_TUNE_GROKBRIEF**
- Grok legt NUR NEUE Dateien in jack-gedaechtnis/auftraege/<id>.md an (typ: frage|hinweis|vorschlag, text max 500, Format auftraege/LIESMICH.txt). jack_fahrtlage (Cron 2 h) holt per git pull --rebase, meldet max 3 je Lauf: hinweis ueber jack_tg_send, frage/vorschlag per send_keyboard mit Knopf ga:ja|nein:<nonce> (128 Bit, 48 h, logs/grok_pending.json 0600, Lock).
- jack_telegram.handle_callback ga: -> jack_fahrtlage.antwort (nur Dimas Privatchat, Einmal-Code) -> status/<id>.json -> commit/push. Ein gemeinsamer Git-Lock logs/.gedaechtnis_git.lock fuer Cron und Knopf. Antwort ist NUR Antwort, JACK fuehrt nichts aus.
- Lagebild jetzt mit Fail-Acts (Name x Anzahl) und Zahl offener Grok-Fragen.
- E2E 14:25-14:26: Testfrage 2026-10-28_000 -> Knopf bei Dima -> Ja -> status antwort=ja, auf GitHub bestaetigt (2b460b3). Gleichzeitiger Grok-Commit wurde per rebase sauber eingemischt.
