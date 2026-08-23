#!/usr/bin/env python3
"""Fallback: Skills mit step_guard abspielen."""
from ui_agent.step_guard import ensure_ready, run_step, guard_su if False else None
from ui_agent.step_guard import su as guard_su, run_step, ensure_ready

def replay_open_settings_and_back(dry=False):
    st = ensure_ready("skill_start")
    print("START", st.get("package"), st.get("hash","")[:10])
    if dry:
        print("DRY — keine Aktionen")
        return True
    def open_settings():
        guard_su("am start -a android.settings.SETTINGS")
    ok1, _, a1 = run_step("open_settings", open_settings, why="Settings oeffnen (Skill)", expect_change=True)
    def go_back():
        guard_su("input keyevent 4")
    ok2, _, a2 = run_step("back", go_back, why="Zurueck zum Launcher", expect_change=True)
    print("SKILL_ENDE", ok1 and ok2, a2.get("package"))
    return ok1 and ok2

if __name__ == "__main__":
    replay_open_settings_and_back()
