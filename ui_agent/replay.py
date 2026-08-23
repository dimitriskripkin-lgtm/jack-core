#!/usr/bin/env python3
"""ui_agent/replay.py - Skill anzeigen und vorsichtig ausführen."""
import sys, time
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")

from skills import get_skill, list_skills
from preflight import ensure_ready
from capture import capture, _su
from logger import log_transition
from action import tap_text
from ui_agent.step_guard import run_step, su as guard_su, ensure_ready as guard_ready

def show(name):
    s = get_skill(name)
    if not s:
        print("Skill nicht gefunden:", name)
        return
    print("=== Skill:", name, "===")
    print("Start:", s["start_hash"][:12], "Ende:", s["end_hash"][:12], "Schritte:", len(s["steps"]))
    for i, st in enumerate(s["steps"], 1):
        print(f"  {i:2d}. {st.get('action','?'):12} {str(st.get('target',''))[:28]:28} → {st.get('pkg','')}")
    st = ensure_ready()
    print("Aktuell:", st.get("package"), st.get("hash","")[:10])

def do_step(action, target):
    action = (action or "").upper()
    target = str(target or "")
    if action in ("BACK",) or target.upper() == "BACK":
        _su("input keyevent 4")
        return True, "BACK"
    if action in ("HOME",) or target.upper() == "HOME":
        _su("input keyevent 3")
        return True, "HOME"
    if action in ("OPEN", "OPEN_SEARCH") or target.upper() in ("SETTINGS", "CHROME"):
        if "SETTING" in target.upper():
            _su("am start -a android.settings.SETTINGS")
            return True, "OPEN_SETTINGS"
        if "CHROME" in target.upper():
            _su("am start -n com.android.chrome/com.google.android.apps.chrome.Main")
            return True, "OPEN_CHROME"
        if target.startswith("http") or "SEARCH" in action:
            _su("am start -a android.intent.action.VIEW -d " + target)
            return True, "OPEN_URL"
        return False, "open_unbekannt"
    # normaler Text-Tap
    if target and target.lower() not in ("manual", "user_action", ""):
        res = tap_text(target)
        return res.get("ok", False), res.get("msg", "")
    return False, "skip"


def _guard_exec_step(step):
    """Ein Skill-Step ausfuehren (dict) — action+target wie do_step."""
    if not isinstance(step, dict):
        step = {"action": str(step)}
    action = (step.get("action") or step.get("type") or step.get("op") or "").upper()
    target = str(step.get("target") or step.get("text") or step.get("query") or step.get("arg") or "")
    tu = target.upper()
    # BACK / HOME
    if action in ("BACK",) or tu == "BACK":
        guard_su("input keyevent 4")
        return
    if action in ("HOME",) or tu == "HOME":
        guard_su("input keyevent 3")
        return
    # OPEN *
    if action in ("OPEN", "OPEN_SEARCH", "OPEN_SETTINGS") or "SETTING" in tu:
        if "SETTING" in tu or action == "OPEN_SETTINGS":
            guard_su("am start -a android.settings.SETTINGS")
            return
        if "CHROME" in tu:
            guard_su("am start -n com.android.chrome/com.google.android.apps.chrome.Main")
            return
        if target.startswith("http") or "SEARCH" in action:
            guard_su("am start -a android.intent.action.VIEW -d " + target)
            return
    if "CHROME" in action:
        guard_su("am start -n com.android.chrome/com.google.android.apps.chrome.Main")
        return
    # Text-Tap
    if target and tu not in ("MANUAL", "USER_ACTION", ""):
        try:
            from jack_vision_selector import tap_text
            ok, msg = tap_text(target, partial=True)
            print("   tap_text:", ok, msg)
        except Exception as e:
            # fallback capture.tap_text API
            try:
                from action import tap_text as tt
                r = tt(target)
                print("   action.tap_text:", r)
            except Exception as e2:
                raise RuntimeError("tap fail %s / %s" % (e, e2))
        return
    if step.get("shell"):
        guard_su(str(step["shell"]))
        return
    raise RuntimeError("guard cannot exec step: %r" % step)


def run(name, max_steps=5, dry=False):
    s = get_skill(name)
    if not s:
        print("Skill nicht gefunden")
        return
    mode = "DRY" if dry else "LIVE"
    print(f"=== REPLAY {name} ({mode}, max {max_steps}) ===")
    st = ensure_ready()
    print("Start bei", st.get("package"), st.get("hash","")[:10])

    for i, step in enumerate(s["steps"][:max_steps], 1):
        before = capture()
        action = step.get("action") or "user_action"
        target = str(step.get("target") or "manual")
        print(f"\n[{i}] {action} | {target[:40]} (pkg={step.get('pkg')})")

        did = False
        msg = "dry"
        if not dry:
            did, msg = do_step(action, target)
            print("   ", msg)
            time.sleep(1.5)
        else:
            time.sleep(0.5)

        after = capture()
        success = after.get("hash") != before.get("hash")
        log_transition(before["hash"], f"replay:{action}", target, after["hash"], success,
                       {"pkg": after.get("package"), "skill": name, "dry": dry, "did": did})
        print(f"    {before['hash'][:8]} → {after['hash'][:8]} success={success}")

        if after.get("hash","").startswith(s["end_hash"][:8]) and i > 1:
            print("→ Ziel-Hash erreicht")
            break
        if i >= 2 and not success and not dry:
            print("→ kein Fortschritt, stoppe")
            break

    print("\n=== REPLAY Ende ===")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Skills:", [r[1] for r in list_skills()])
        print("  show | dry | run <name>")
    elif sys.argv[1] == "show":
        show(sys.argv[2] if len(sys.argv)>2 else "open_settings_and_back")
    elif sys.argv[1] == "dry":
        run(sys.argv[2] if len(sys.argv)>2 else "open_settings_and_back", dry=True)
    elif sys.argv[1] == "run":
        run(sys.argv[2] if len(sys.argv)>2 else "open_settings_and_back", dry=False)
    else:
        show(sys.argv[1])


def run_guarded(name, max_steps=5, dry=False):
    """Skill abspielen mit step_guard (Preflight, WARUM, Rollback)."""
    from skills import get_skill
    skill = get_skill(name)
    if not skill:
        print("Skill nicht gefunden:", name)
        return False
    # skill kann (id, name, plan_json, ...) oder dict sein
    steps = []
    if isinstance(skill, dict):
        steps = skill.get("steps") or skill.get("plan") or []
        if isinstance(steps, str):
            import json
            try:
                steps = json.loads(steps).get("steps", [])
            except Exception:
                steps = []
    else:
        # tuple row
        plan = None
        for item in skill:
            if isinstance(item, str) and item.strip().startswith("{"):
                plan = item
                break
            if isinstance(item, (list, dict)):
                plan = item
                break
        if isinstance(plan, str):
            import json
            try:
                plan = json.loads(plan)
            except Exception:
                plan = {}
        if isinstance(plan, dict):
            steps = plan.get("steps") or []
        elif isinstance(plan, list):
            steps = plan
    print(f"=== REPLAY_GUARDED {name} steps={len(steps)} dry={dry} ===")
    st = guard_ready("skill_start")
    print("Start", st.get("package"), st.get("hash", "")[:10])
    if dry:
        for i, s in enumerate(steps[:max_steps], 1):
            print(f"[dry {i}]", s)
        return True
    ok_all = True
    for i, step in enumerate(steps[:max_steps], 1):
        why = "Skill %s Schritt %d: %s" % (name, i, step)
        def _act(s=step):
            _guard_exec_step(s)
        try:
            ok, b, a = run_step("%s_%d" % (name, i), _act, why=why, expect_change=True)
        except Exception as e:
            print("STEP_ERR", e)
            ok, b, a = False, {}, {}
        print("[%d] ok=%s %s -> %s" % (i, ok, b.get("package"), a.get("package")))
        if not ok:
            ok_all = False
            print("→ Stop")
            break
    print("=== REPLAY_GUARDED Ende", ok_all)
    return ok_all
