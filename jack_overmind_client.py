#!/usr/bin/env python3
"""
Overmind-Client: State lesen -> Teacher (mock|file|api later) -> Aktionen vorschlagen.
Ausfuehrung nur ueber erlaubte Hooks, kein blinder Shell.
"""
import json, os, subprocess, sys

H = "/data/data/com.termux/files/home/jack"
STATE = H + "/jack_overmind_state.json"
PLAN = H + "/jack_overmind_plan.json"
RESULT = H + "/jack_overmind_result.json"

def load_state():
    import jack_overmind_state as s
    path, st = s.collect()
    return st


def file_teacher(state):
    """Plan aus jack_overmind_plan_in.json — von Grok/Dima gelegt."""
    path = H + "/jack_overmind_plan_in.json"
    if not os.path.isfile(path):
        return None
    try:
        plan = json.load(open(path))
        plan["teacher"] = plan.get("teacher") or "file"
        return plan
    except Exception as e:
        return {"teacher": "file_error", "goal": "none", "actions": [], "notes": str(e)[:200]}

def mock_teacher(state):

    """Ersetzt spaeter API. Liefert Maschinenplan."""
    actions = []
    if not state.get("ssh_xiaomi"):
        actions.append({"id": "ssh_check", "cmd_type": "ssh_check", "why": "Xiaomi SSH tot"})
    if not state.get("adb_device") and state.get("ssh_xiaomi"):
        actions.append({"id": "adb_heal", "cmd_type": "adb_heal", "why": "ADB nicht device"})
    if not actions:
        actions.append({"id": "status", "cmd_type": "status", "why": "Alles grundgruenn — Status reporten"})
    return {
        "teacher": "mock",
        "goal": "stabilize_link",
        "actions": actions[:5],
        "notes": "Mock-Plan. Spaeter Grok/xAI API.",
    }

def execute_plan(plan):
    results = []
    for a in plan.get("actions") or []:
        ctype = a.get("cmd_type")
        r = {"id": a.get("id"), "cmd_type": ctype, "ok": False, "out": ""}
        try:
            if ctype == "adb_heal":
                p = subprocess.run(
                    ["python3", H + "/jack_adb_heal.py"],
                    capture_output=True, text=True, timeout=90,
                )
                r["out"] = ((p.stdout or "") + (p.stderr or ""))[:500]
                r["ok"] = p.returncode == 0 and "RESULT OK" in r["out"]
            elif ctype == "ssh_check":
                p = subprocess.run(
                    ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", "xiaomi-jack", "echo", "SSH_OK"],
                    capture_output=True, text=True, timeout=10,
                )
                r["out"] = ((p.stdout or "") + (p.stderr or ""))[:200]
                r["ok"] = "SSH_OK" in r["out"]
            elif ctype == "status":
                r["out"] = json.dumps({
                    "ssh": a.get("why"),
                    "hint": "ok",
                }, ensure_ascii=False)
                r["ok"] = True
            else:
                r["out"] = "skip_unknown_type"
        except Exception as e:
            r["out"] = str(e)[:200]
        results.append(r)
    return results

def main():
    state = load_state()
    plan = file_teacher(state) or mock_teacher(state)
    open(PLAN, "w").write(json.dumps(plan, indent=2, ensure_ascii=False))
    results = execute_plan(plan)
    out = {"ts": state.get("ts"), "plan": plan, "results": results}
    open(RESULT, "w").write(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False)[:1200])
    return 0 if all(x.get("ok") for x in results) else 1

if __name__ == "__main__":
    sys.exit(main())
