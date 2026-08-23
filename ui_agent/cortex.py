#!/usr/bin/env python3
"""ui_agent/cortex.py - Ziel in Text → passenden Skill finden und ausführen."""
import sys, re
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")

from skills import list_skills, get_skill
from package_mapper import find_app
from capture import _su
from preflight import ensure_ready
from replay import run as replay_run
from ui_agent.step_guard import ensure_ready as guard_ensure_ready, run_step


def launch_app(query):
    rows = find_app(query)
    if not rows:
        return False, "App nicht im Index"
    pkg, act, label = rows[0]
    if "/" not in act:
        act = pkg + "/" + act
    elif not act.startswith(pkg):
        act = pkg + "/" + act.split("/")[-1]
    _su("am start -n " + act)
    return True, f"gestartet: {label} ({act})"

def find_skill(goal: str):
    goal = goal.lower()
    skills = list_skills()
    # einfache Keyword-Zuordnung
    mapping = [
        (["setting", "einstellung", "settings"], "open_settings_and_back"),
        (["chrome", "browser"], "open_chrome_and_home"),
    ]
    for keys, name in mapping:
        if any(k in goal for k in keys):
            return name
    # Fallback: ersten Skill mit Ähnlichkeit
    for sid, name, *_ in skills:
        if any(w in name.lower() for w in goal.split()):
            return name
    return None

def handle(goal: str, dry=False):
    print(f"=== CORTEX Ziel: {goal} ===")
    st = ensure_ready()
    print(f"Aktuell: {st.get('package')} {st.get('hash','')[:10]}")

    name = find_skill(goal)
    if name:
        print(f"Gewählter Skill: {name}")
        replay_run(name, max_steps=5, dry=dry)
        return True

    # Kein Skill → Direct-Launch aus Package-Index versuchen
    print("Kein Skill – versuche Direct-Launch …")
    ok, msg = launch_app(goal)
    print(msg)
    if ok:
        import time
        time.sleep(1.8)
        st2 = ensure_ready()
        print(f"Jetzt: {st2.get("package")} {st2.get("hash","")[:10]}")
        return True

    print("Bekannte Skills:")
    for s in list_skills():
        print(" -", s[1])
    print("→ Abbruch (kein Halluzinieren)")
    return False


def _guard_do_action(step):
    """Fuehrt einen Skill-Step aus (dict oder str)."""
    if isinstance(step, dict):
        kind = (step.get("action") or step.get("type") or step.get("op") or "").upper()
        arg = step.get("arg") or step.get("target") or step.get("pkg") or ""
    else:
        kind = str(step).upper()
        arg = ""
    if "SETTING" in kind or kind == "OPEN_SETTINGS":
        guard_su("am start -a android.settings.SETTINGS")
        return "open_settings"
    if kind in ("BACK", "INPUT_BACK") or kind.endswith("BACK"):
        guard_su("input keyevent 4")
        return "back"
    if kind in ("HOME", "INPUT_HOME"):
        guard_su("input keyevent 3")
        return "home"
    if "CHROME" in kind:
        guard_su("am start -n com.android.chrome/com.google.android.apps.chrome.Main")
        return "chrome"
    if kind.startswith("TAP") or kind == "TAP_TEXT":
        try:
            from jack_vision_selector import tap_text
            q = arg or (step.get("text") if isinstance(step, dict) else "")
            tap_text(str(q), partial=True)
        except Exception as e:
            print("tap_text fail", e)
        return "tap"
    # raw shell-ish
    if isinstance(step, dict) and step.get("cmd"):
        guard_su(str(step["cmd"]))
        return "cmd"
    print("UNBEKANNTER STEP", step)
    return "unknown"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python3 -m ui_agent.cortex \"öffne settings\"")
        print("         python3 -m ui_agent.cortex \"chrome\" --dry")
    else:
        dry = "--dry" in sys.argv
        goal = " ".join(a for a in sys.argv[1:] if a != "--dry")
        handle(goal, dry=dry)
