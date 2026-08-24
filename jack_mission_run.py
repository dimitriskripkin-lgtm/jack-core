#!/usr/bin/env python3
"""Aktive Mission -> plan_in -> overmind client -> result."""
import json, subprocess, sys
from pathlib import Path

H = Path("/data/data/com.termux/files/home/jack")
mission_path = H / "jack_mission_active.json"
plan_path = H / "jack_overmind_plan_in.json"
result_path = H / "jack_overmind_result.json"

def main():
    if not mission_path.is_file():
        print("NO_MISSION"); return 1
    m = json.loads(mission_path.read_text())
    plan = {
        "teacher": m.get("teacher") or "file",
        "goal": m.get("goal") or m.get("title") or "",
        "actions": m.get("steps") or [],
        "notes": "mission:" + str(m.get("id")),
    }
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    r = subprocess.run(
        [sys.executable, str(H / "jack_overmind_client.py")],
        capture_output=True, text=True, timeout=180,
    )
    out = ((r.stdout or "") + (r.stderr or "")).strip()
    print(out[:2000])
    try:
        plan_path.unlink()
    except Exception:
        pass
    if result_path.is_file():
        res = json.loads(result_path.read_text())
        oks = [x.get("ok") for x in res.get("results") or []]
        # DONE_LINE
        print("DONE_ALL", all(oks) if oks else False, "N", len(oks))
        fails = [x.get("id") for x in res.get("results") or [] if not x.get("ok")]
        if fails:
            print("FAIL_IDS", fails)

    return r.returncode

if __name__ == "__main__":
    sys.exit(main())
