# 15. jack_planner.py

Gelesen 03.10.2026, Grok. Kein Umbau.

**Zweck:** Plan-Schritte auf dem Xiaomi ausfuehren. SSH, Tap, App, Keyevent, Warten, UI-Check, Home, Text, Chrome-Suche.

**Funktionen:** step_exec, step_tap, step_find_and_tap, step_open_app, step_keyevent, step_wait, step_ui_check, step_home, step_input_text, step_ui_text, step_chrome_search, run_plan(plan, send_fn).

**Freigabe:** Kein eigenes Gate in den gelesenen Zeilen. run_plan fuehrt die Schritte der Reihe nach. Wer den Plan baut, liegt ausserhalb.

**Offen:** Ob Telegram den PLAN-Block noch an run_plan gibt. Nicht in dieser Runde am Dispatcher nachgelesen.
