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
