# 308 Fahrt-Lage fuer Grok-Bot und Tesla (28.10.2026, Claude, Dima-Go 13:06)

**Zweck:** Grok im Tesla hat kein eigenes Gedaechtnis. Test 28.10. 13:12 (Codewort im Grok-Bot, Tesla-Grok findet es nach "guck bei Jack"): Was der Grok-Bot ("Jack") im Verlauf hat, kann Tesla-Grok sofort lesen. Einbahn Bot -> Auto.

**Aufbau:**
- Privates Repo `dimitriskripkin-lgtm/jack-gedaechtnis` (angelegt per gh auf dem HONOR, Klon ~/jack-gedaechtnis). Inhalt: START.md (Regeln), lage/aktuell.md (automatisch), entscheidungen/offen.md (Claude pflegt), entscheidungen/von_dima.md (Rueckweg, nur anhaengen), Tesla/ und Grok/notizen.md.
- `jack_fahrtlage.py` (JACK_TUNE_FAHRTLAGE): liest Dienste (11 Kern), Honor Akku/Temp (jack_lagebild.honor), Xiaomi Temp + n8n (run_shell as_root=False), Fails 24 h, Playlist-Stand, offene Entscheidungen; schreibt lage/aktuell.md, commit + push. Cron HONOR `50 */2 * * *`, Log logs/fahrtlage.log. `--kein-push` zum Testen.
- Oeffentliches jack-core bleibt frei von Gespraechsinhalten (Grund: Git-Historie vergisst nicht).

**Regeln:** Keine Geheimnisse, keine Chat-/Benachrichtigungstexte. Repo ist Spiegel, kein Befehlskanal: Eintraege in von_dima.md fuehrt JACK nicht automatisch aus, Claude prueft, Dima bestaetigt.

**Erster Lauf 13:14:** 11/11 Dienste, Honor 94 %/34 C, Xiaomi 44,3 C, n8n laeuft, 2 Fails/24 h, Playlist 386/817, Push 1170bd0.

**Offen:** Grok-Bot braucht Lesezugriff auf das private Repo (Dima im Grok-GitHub-Connector). Rueckweg von_dima.md -> Claude-Pruefung noch manuell. Branch-Schutz fuer private Repos ist bei GitHub Free nicht verfuegbar, und Grok schreibt mit Dimas Identitaet (Admin) -> Schutz waere ohnehin umgehbar; Regel "nur anhaengen" + Git-Historie als Sicherung.
