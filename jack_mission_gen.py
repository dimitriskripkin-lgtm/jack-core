#!/usr/bin/env python3
"""jack_mission_gen.py — JACK generiert Fix-Missions aus fail/-Einträgen."""
MODULE_VERSION = 1

import os, json, time, re

J = os.path.expanduser("~/jack")
FAIL = os.path.join(J, "missions", "fail")
PEND = os.path.join(J, "missions", "pending")
DONE = os.path.join(J, "missions", "done")
GEN_LOG = os.path.join(J, "missions", "gen.log")

# Muster → Fix-Strategie
STRATEGIES = [
    {
        "name": "bare_except",
        "match": lambda m: m.get("act") == "grep_count" and m.get("pattern") == "    except Exception:" and m.get("expect_max") == 0,
        "build": lambda m: {
            "typ": "fix", "act": "sed_replace", "staged": True,
            "file": m["file"],
            "old": "    except Exception:",
            "new": "    except Exception:",
            "verify_act": "grep_count",
            "verify_pattern": "    except Exception:",
            "verify_expect_max": 0,
            "cat": "quality_autofix"
        }
    },
    {
        "name": "hardcoded_path",
        "match": lambda m: m.get("act") == "grep_count" and "/data/data/com.termux/files/home/jack/" in str(m.get("pattern","")),
        "build": lambda m: None  # zu komplex für auto-fix, nur loggen
    },
    {
        "name": "module_version_missing",
        "match": lambda m: m.get("act") == "grep_count" and m.get("pattern") == "MODULE_VERSION" and m.get("expect_min") == 1,
        "build": lambda m: {
            "typ": "fix", "act": "sed_replace", "staged": True,
            "file": m["file"],
            "old": "#!/usr/bin/env python3\n",
            "new": "#!/usr/bin/env python3\nMODULE_VERSION = 1\n",
            "verify_act": "grep_count",
            "verify_pattern": "MODULE_VERSION",
            "verify_expect_max": 999,
            "cat": "version_autofix"
        }
    },
]

def _log(msg):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    with open(GEN_LOG, "a") as f:
        f.write(f"{ts} {msg}\n")

def _notify(msg):
    try:
        import jack_notify as _jn
        _jn.notify(msg)
    except Exception:
        pass

def run():
    if not os.path.exists(FAIL):
        return 0

    generated = 0
    for fname in os.listdir(FAIL):
        if not fname.endswith(".json"):
            continue
        try:
            m = json.load(open(os.path.join(FAIL, fname)))
            mission_id = m.get("id", fname.replace(".json",""))

            for strategy in STRATEGIES:
                if not strategy["match"](m):
                    continue

                fix = strategy["build"](m)
                if fix is None:
                    _log(f"SKIP {mission_id}: {strategy['name']} zu komplex")
                    break

                fix_id = f"gen_{mission_id}_{strategy['name']}"
                fix["id"] = fix_id

                # Nicht nochmal generieren wenn schon in pending/done
                already = (
                    os.path.exists(os.path.join(PEND, f"{fix_id}.json")) or
                    os.path.exists(os.path.join(DONE, f"{fix_id}.json"))
                )
                if already:
                    _log(f"SKIP {fix_id}: bereits vorhanden")
                    break

                # Fix-Mission schreiben
                path = os.path.join(PEND, f"{fix_id}.json")
                open(path, "w").write(json.dumps(fix))
                _log(f"GEN {fix_id}: {strategy['name']} für {m.get('file','?')}")
                _notify(f"🤖 JACK generiert Fix:\n{fix_id}\n{strategy['name']} in {os.path.basename(m.get('file','?'))}")
                generated += 1
                break

        except Exception as e:
            _log(f"ERROR {fname}: {str(e)[:80]}")

    return generated

def _generate_trainer_mission():
    """Wenn keine pending-Missions mehr → Trainer-Mission generieren."""
    import os
    PEND = os.path.join(os.path.expanduser("~/jack"), "missions", "pending")
    DONE = os.path.join(os.path.expanduser("~/jack"), "missions", "done")
    pending_count = len([f for f in os.listdir(PEND) if f.endswith(".json")]) if os.path.exists(PEND) else 0
    if pending_count > 0:
        return  # noch was zu tun
    # Trainer-Mission schreiben
    mid = f"trainer_{int(__import__('time').time())}"
    mission = {
        "id": mid,
        "typ": "check",
        "act": "mtime_fresh",
        "file": "~/jack/trainer.log",
        "max_age_s": 86400,
        "expect": "PASS",
        "cat": "trainer"
    }
    path = os.path.join(PEND, f"{mid}.json")
    import json
    open(path, "w").write(json.dumps(mission))
    _log(f"Trainer-Mission generiert: {mid}")

if __name__ == "__main__":
    n = run()
    print(f"jack_mission_gen: {n} Fix-Missions generiert")
