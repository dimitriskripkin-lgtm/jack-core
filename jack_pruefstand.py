#!/usr/bin/env python3
"""JACK_TUNE_PRUEFSTAND Schritt 7. Liest nur, schreibt den Bericht und den Hook."""
import ast, hashlib, json, os, subprocess, time
J = "/data/data/com.termux/files/home/jack"
V = "/data/data/com.termux/files/usr/var/service"
REPORT = J + "/reports/pruefstand.json"
HOOK = J + "/.git/hooks/pre-commit"
SV = ["jack_telegram","jack_cortex","jack_waechter","jack_autolearn","jack_publisher","jack_focus_monitor","jack_missions","jack_mcp","cloudflared","jack_qwen"]
IMPORTS = ["jack_telegram","jack_cortex","jack_autonomous","jack_autolearn_loop","jack_focus_monitor","jack_mission_runner","jack_missions","jack_mcp_server"]

def sh(cmd, t=8):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=t)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:
        return 1, str(e)[:160]

def allowed_names(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="ignore").read())
    except Exception as e:
        return [], str(e)[:120]
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "ALLOWED":
                    try:
                        val = node.value
                        if isinstance(val, ast.Call) and getattr(val.func, "id", "") == "set" and val.args:
                            val = val.args[0]
                        return sorted(ast.literal_eval(val)), ""
                    except Exception as e:
                        return [], str(e)[:120]
    return [], "ALLOWED nicht gefunden"

def sv_state(name):
    rc, out = sh(["sv", "status", name], 6)
    if out.startswith("run:"):
        return "run", out[:80]
    if "file does not exist" in out:
        return "fehlt", out[:80]
    return "down", out[:80]

def hb_age(name):
    p = os.path.join(J, ".heartbeat_" + name)
    if not os.path.isfile(p):
        return None
    try:
        return round(time.time() - float(open(p).read().strip()), 1)
    except Exception:
        return None

def imports():
    rows = []
    for name in IMPORTS:
        rc, out = sh(["python3", "-c", "import " + name], 8)
        if rc == 0:
            rows.append({"name": name, "ok": True})
        else:
            rows.append({"name": name, "ok": False, "err": (out or "timeout")[:140]})
    return rows

def reading():
    rows = []
    rows.append({"act": "file_exists", "target": ".ollama_lock", "ok": os.path.isfile(J + "/.ollama_lock")})
    rows.append({"act": "file_exists", "target": "missions/STOP", "ok": not os.path.isfile(J + "/missions/STOP"), "note": "Kill-Switch offen ist Soll"})
    rc, out = sh(["git", "log", "-1", "--format=%h %ci %s"], 8)
    rows.append({"act": "diag", "target": "git_head", "ok": rc == 0, "out": out[:140]})
    return rows

def secrets_staged():
    rc, out = sh(["git", "diff", "--cached", "--name-only"], 8)
    bad = []
    for name in out.splitlines():
        low = name.lower()
        if name.endswith("config.ini") or ".jack_mcp_token" in name or low.endswith(".env"):
            bad.append(name)
    return bad

def install_hook():
    body = """#!/data/data/com.termux/files/usr/bin/sh
# JACK_TUNE_PRUEFSTAND secrets
git diff --cached --name-only | grep -E 'config.ini|\\.jack_mcp_token|\\.env$' && echo 'PRUEFSTAND: Secrets nicht committen' && exit 1
git diff --cached -U0 | grep -E 'JACK_MCP_TO''KEN=|ghp_|sk-[A-Za-z0-9]{20}' && echo 'PRUEFSTAND: Token-Muster im Commit' && exit 1
exit 0
"""
    os.makedirs(os.path.dirname(HOOK), exist_ok=True)
    open(HOOK, "w").write(body)
    os.chmod(HOOK, 0o700)
    return os.path.isfile(HOOK)

def main():
    os.makedirs(J + "/reports", exist_ok=True)
    dienste = []
    for name in SV:
        st, raw = sv_state(name)
        age = hb_age(name)
        dienste.append({"name": name, "sv": st, "hb_s": age, "hb_ok": age is not None and age < 900, "raw": raw})
    run_allowed, run_err = allowed_names(J + "/jack_mission_runner.py")
    mcp_allowed, mcp_err = allowed_names(J + "/jack_mcp_server.py")
    only_run = sorted(set(run_allowed) - set(mcp_allowed))
    only_mcp = sorted(set(mcp_allowed) - set(run_allowed))
    report = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "marke": "JACK_TUNE_PRUEFSTAND",
        "imports": imports(),
        "lesen": reading(),
        "dienste": dienste,
        "focus_monitor_beat_im_code": "beat(" in open(J + "/jack_focus_monitor.py", encoding="utf-8", errors="ignore").read(),
        "allowed": {
            "runner_n": len(run_allowed),
            "mcp_n": len(mcp_allowed),
            "runner_err": run_err,
            "mcp_err": mcp_err,
            "nur_runner": only_run,
            "nur_mcp": only_mcp,
            "gleich": run_allowed == mcp_allowed and not run_err and not mcp_err,
        },
        "secrets_staged": secrets_staged(),
        "hook": install_hook(),
    }
    open(REPORT, "w").write(json.dumps(report, ensure_ascii=False, indent=2))
    print(REPORT)
    print("imports", sum(1 for x in report["imports"] if x["ok"]), "/", len(report["imports"]))
    print("sv_run", sum(1 for x in dienste if x["sv"] == "run"), "/", len(dienste))
    print("allowed_gleich", report["allowed"]["gleich"], "runner", report["allowed"]["runner_n"], "mcp", report["allowed"]["mcp_n"])
    print("focus_beat", report["focus_monitor_beat_im_code"])

if __name__ == "__main__":
    main()
