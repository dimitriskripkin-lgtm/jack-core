# 10. jack_exec.py

Gelesen 03.10.2026, Grok, live per read_file. Kein Umbau.

**Zweck:** Ausfuehrungs-Mund fuer Freitext-Befehle und UI-Saetze. Kein Mission-Act. Nimmt einen Shell-String oder einen UI-Satz, blockt ein paar harte Muster, fuehrt aus, schreibt das Ergebnis in jack_outcomes.db.

**Wer ruft:** Telegram-EXEC-Knopf und der UI-Pfad handle_ui_intent. extrahiere() zieht einen EXEC-Block aus einem Modelltext. Nicht die MCP-Whitelist.

**Funktionen:**
- pruefe(cmd): Substring-Sperre auf Zerstoer-Muster, Schluesselordner, Schluesselwort, shutdown, reboot, Geraete-Umlenkung. Laenge ueber 4000 blockt. Kein Allowlist, nur Denylist.
- _guard_ready(): optional ui_agent.step_guard.ensure_ready. Fehlt das Modul, ist das Gate fail-open.
- tap_text(query): Unlock ueber jack_xiaomi_unlock, dann jack_vision_selector.tap_text.
- run(cmd, timeout=120): tap-Prefix ohne Shell. Sonst subprocess mit bash -lc, cwd im jack-Home. Bei Xiaomi-SSH plus monkey, am, input oder uiautomator vorher Unlock. jack_observer: meckert der Beobachter und rc ist 0, wird rc auf 99 gesetzt. Output ueber 3000 Zeichen wird gekuerzt. Danach jack_outcome_tracker.log_outcome, Befehl auf 500, Output auf 1000. Tracker-Fehler werden geschluckt.
- handle_ui_intent(text): Stopp schreibt Kill-Datei und loescht Run-Datei. Forschen schreibt Run-Datei und oeffnet Chrome per SSH-su. Tippen geht an tap_text. Kein Treffer: None.
- extrahiere(text): schneidet den EXEC-Block aus einem Modelltext.

**Outcomes:** Bestaetigt. Schreiber ist jack_outcome_tracker.log_outcome, nicht exec selbst. Timeout und Exception in run() landen nicht in der DB.

**Freigabe:** Kein proposals-, shadow- oder PENDING-Pfad in dieser Datei. step_guard fail-open, wenn das Modul fehlt. Shell ist bash -lc.

**Offen:** Aufrufer in jack_telegram nicht zeilenweise nachgelesen.
