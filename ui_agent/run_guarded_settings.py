#!/usr/bin/env python3
"""Beispiel: Settings oeffnen mit Preflight, WARUM, Beweis, Rollback."""
import time
from ui_agent.step_guard import ensure_ready, run_step, su, log

def main():
    st = ensure_ready("start")
    print("START", st.get("package"), st.get("hash", "")[:10], st.get("texts", [])[:5])

    def open_settings():
        su("am start -a android.settings.SETTINGS")

    ok1, b1, a1 = run_step(
        "open_settings",
        open_settings,
        why="Systemeinstellungen oeffnen um UI-Pfad zu pruefen",
        expect_change=True,
    )
    print("STEP1", ok1, a1.get("package"), a1.get("hash", "")[:10])

    def go_back():
        su("input keyevent 4")

    ok2, b2, a2 = run_step(
        "back_home",
        go_back,
        why="Zurueck, Settings nicht offen lassen",
        expect_change=True,
    )
    print("STEP2", ok2, a2.get("package"), a2.get("hash", "")[:10])
    print("ENDE ok=", ok1 and ok2)

if __name__ == "__main__":
    main()
