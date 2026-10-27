# 305 Klingel: Telegram bei neuer ChatGPT-Post (26.10.2026)

**Was:** jack_klingel.py (JACK_TUNE_KLINGEL), Cron alle 5 Min. Liest nur ARBEITSPLATZ/BUEROS/claude/eingang.md ab dem letzten Stand (logs/.klingel_state.json: inode+Groesse). Neue Ueberschrift mit chatgpt -> eine Telegram-Meldung ueber jack_tg_send (quelle klingel, wichtig) mit bis zu 3 Titelzeilen.
**Warum:** Dima muss nicht raten, wann er Claude "Schau in den Briefkasten" sagen soll. Erster kleiner Agenten-Schritt, Dima bleibt Schalter.
**Regeln:** Erstlauf/Rotation des Eingangs: nur merken, nicht klingeln. Sendefehler: Stand bleibt, naechster Lauf versucht erneut. Posts von Claude klingeln nicht.
**Aus:** ~/jack/.klingel_off. Rueckbau: Cron-Zeile entfernen (Backup logs/crontab_vor_klingel_20261026.txt), Skript ins Attic.
**Test:** lokal 4/4 (Init, Klingel, Ruhe, Claude-Post), live 26.10. 07:59 gesendet (Chatlog quelle klingel).

**Nachtrag 26.10.2026 09:33 (JACK_TUNE_KLINGEL2)**
Klingel in beide Richtungen: auch Post von Claude in BUEROS/chatgpt/eingang.md (Status logs/.klingel_state_chatgpt.json) -> "Sag ChatGPT: Schau in deinen Briefkasten". Titel = Kopfzeile, Auto-Kopf "<zeit> claude" wird uebersprungen. Dima-Wunsch 09:31.
