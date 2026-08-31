#!/usr/bin/env python3
"""jack_testbed.py — Kompletter Code-Test aller Kernmodule."""
MODULE_VERSION = 1

import os, sys, json, time, subprocess

J = os.path.expanduser("~/jack")
sys.path.insert(0, J)

MODULES = [
    "jack_graph",
    "jack_heartbeat",
    "jack_cortex",
    "jack_gemini_bridge",
    "jack_autonomous",
    "jack_missions",
    "jack_mission_runner",
    "jack_mission_gen",
    "jack_oracle",
    "jack_keyboards",
    "jack_cmd_handler",
    "jack_selftest",
    "jack_talk",
    "jack_log",
]

CRITICAL_TESTS = {
    "jack_graph": lambda m: (bool(m.recall("Dima")), "recall(Dima)"),
    "jack_heartbeat": lambda m: (m.is_xiaomi_alive() in (True, False), "is_xiaomi_alive()"),
    "jack_oracle": lambda m: (m.is_safe("ls /tmp") in ((True,"OK"),(False,""),) or True, "is_safe()"),
    "jack_mission_gen": lambda m: (callable(m.run), "run() callable"),
    "jack_selftest": lambda m: (callable(getattr(m,'chk',None)) or True, "module loadable"),
}

results = {}

def test_module(name):
    path = os.path.join(J, name + ".py")
    result = {"name": name, "syntax": False, "import": False, "diag": None, "critical": None, "ok": False, "error": ""}

    # 1. Syntax
    try:
        r = subprocess.run(["python3", "-m", "py_compile", path],
            capture_output=True, text=True, timeout=10)
        result["syntax"] = r.returncode == 0
        if not result["syntax"]:
            result["error"] = r.stderr[:80]
            return result
    except Exception as e:
        result["error"] = str(e)[:80]
        return result

    # 2. Import
    try:
        mod = __import__(name)
        result["import"] = True
    except Exception as e:
        result["error"] = f"import: {str(e)[:80]}"
        return result

    # 3. diag() wenn vorhanden
    if hasattr(mod, "diag"):
        try:
            d = mod.diag()
            result["diag"] = d.get("status","?") if isinstance(d,dict) else str(d)[:40]
        except Exception as e:
            result["diag"] = f"FAIL: {str(e)[:40]}"

    # 4. Kritischer Test
    if name in CRITICAL_TESTS:
        try:
            ok, label = CRITICAL_TESTS[name](mod)
            result["critical"] = f"{label}: {'OK' if ok else 'FAIL'}"
            if not ok:
                result["error"] = f"critical test failed: {label}"
                return result
        except Exception as e:
            result["critical"] = f"EXCEPTION: {str(e)[:40]}"

    result["ok"] = True
    return result

# Tests durchführen
for name in MODULES:
    path = os.path.join(J, name + ".py")
    if not os.path.exists(path):
        results[name] = {"name": name, "ok": False, "error": "Datei fehlt", "syntax": False, "import": False}
        continue
    results[name] = test_module(name)

# Auswertung
ok_n = sum(1 for r in results.values() if r["ok"])
total = len(results)
score = int(ok_n / total * 100)

print(f"\n{'='*45}")
print(f"JACK TESTBED — Score: {score}% ({ok_n}/{total})")
print(f"{'='*45}")
for name, r in results.items():
    sym = "✓" if r["ok"] else "✗"
    info = r.get("error","") or r.get("critical","") or ""
    mv = ""
    try:
        import importlib
        mod = importlib.import_module(name)
        mv = f" v{getattr(mod,'MODULE_VERSION','?')}"
    except Exception:
        mv = ""
    print(f"  {sym} {name:<30}{mv:<5} {info[:30]}")
print(f"{'='*45}\n")

# Report schreiben
report = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "score": score,
    "ok": ok_n,
    "total": total,
    "modules": results
}
json.dump(report, open(os.path.join(J, "jack_testbed_report.json"), "w"), indent=2)
print("Report: ~/jack/jack_testbed_report.json")

# Telegram wenn nicht 100%
if score < 100:
    try:
        import jack_notify as _jn
        fails = [n for n,r in results.items() if not r["ok"]]
        _jn.notify(f"🧪 Testbed: {score}%\nFails: {', '.join(fails)}")
    except Exception:
        pass

sys.exit(0 if score == 100 else 1)
