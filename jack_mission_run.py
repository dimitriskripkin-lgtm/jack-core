#!/usr/bin/env python3
"""Aktive Mission -> plan_in -> overmind client -> result."""
import json, subprocess, sys, time
from pathlib import Path

H = Path("/data/data/com.termux/files/home/jack")
mission_path = H / "jack_mission_active.json"
plan_path = H / "jack_overmind_plan_in.json"
result_path = H / "jack_overmind_result.json"

def main():
    if not mission_path.is_file():
        print("NO_MISSION"); return 1
    m = json.loads(mission_path.read_text())
    # FAIL-CLOSED: forbidden muss explizit gesetzt sein
    forbidden = m.get("forbidden")
    if forbidden is None:
        print("FAIL_CLOSED: forbidden field missing")
        return 2
    plan = {
        "teacher": m.get("teacher") or "file",
        "goal": m.get("goal") or m.get("title") or "",
        "actions": m.get("steps") or [],
        "notes": "mission:" + str(m.get("id")),
        "forbidden": forbidden,
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
    oks, fails = [], []
    if result_path.is_file():
        res = json.loads(result_path.read_text())
        results = res.get("results") or []
        oks = [x.get("ok") for x in results]
        fails = [x.get("id") for x in results if not x.get("ok")]
        print("DONE_ALL", all(oks) if oks else False, "N", len(oks))
        if fails:
            print("FAIL_IDS", fails)
        # DB-Log
        try:
            import sqlite3
            con = sqlite3.connect(str(H / "jack_missions.db"))
            con.execute(
                "INSERT INTO missions (aufgabe, typ, status, prioritaet, erstellt, beendet, ergebnis, versuche) VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(m.get("goal") or m.get("title") or m.get("id")),
                    "overmind",
                    "done" if oks and all(oks) else "fail",
                    int(m.get("priority") or 5),
                    int(time.time()),
                    int(time.time()),
                    (str(fails)[:200] if fails else "ok"),
                    1,
                ),
            )
            con.commit()
            con.close()
        except Exception as e:
            print("DB_LOG_FAIL", e)
    return r.returncode

if __name__ == "__main__":
    sys.exit(main())
