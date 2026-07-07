#!/usr/bin/env python3
import subprocess
import os
import sys

sys.path.insert(0, os.path.expanduser("~/jack"))
import jack_config

XIAOMI_SSH_PORT = 8022
SSH_KEY = os.path.expanduser("~/.ssh/id_jack")
SSH_OPTS = [
    "-i", SSH_KEY,
    "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=no",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "ConnectTimeout=5",
]


def _get_xiaomi_ip():
    try:
        sys.path.insert(0, os.path.expanduser("~/jack"))
        from jack_cortex import find_xiaomi
        return find_xiaomi()
    except Exception:
        return jack_config.get_param("NETWORK", "xiaomi_ip")


def run_shell(cmd, as_root=True, timeout=15):
    ip = _get_xiaomi_ip()
    full_cmd = f"su -c '{cmd}'" if as_root else cmd

    try:
        result = subprocess.run(
            ["ssh"] + SSH_OPTS + ["-p", str(XIAOMI_SSH_PORT), f"root@{ip}", full_cmd],
            capture_output=True, text=True, timeout=timeout
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def read_file(path):
    result = run_shell(f"cat {path}")
    return result["stdout"] if result["success"] else None


def write_file(path, content):
    ip = _get_xiaomi_ip()
    try:
        result = subprocess.run(
            ["ssh"] + SSH_OPTS + ["-p", str(XIAOMI_SSH_PORT), f"root@{ip}",
             f"su -c \"cat > {path}\""],
            input=content, capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0
    except Exception:
        return False


def get_status():
    ip = _get_xiaomi_ip()
    status = {"ip": ip, "reachable": False}

    ping = subprocess.run(["ping", "-c", "1", "-W", "2", ip], capture_output=True)
    status["reachable"] = ping.returncode == 0
    if not status["reachable"]:
        return status

    battery = run_shell("dumpsys battery | grep level")
    status["battery"] = battery["stdout"] if battery["success"] else "unbekannt"

    uptime = run_shell("uptime")
    status["uptime"] = uptime["stdout"] if uptime["success"] else "unbekannt"

    shizuku = run_shell("pgrep -f shizuku")
    status["shizuku_running"] = shizuku["success"] and bool(shizuku["stdout"])

    return status


if __name__ == "__main__":
    print("[XIAOMI] Status-Check...")
    s = get_status()
    for k, v in s.items():
        print(f"  {k}: {v}")

    print("\n[XIAOMI] Test: einfacher Shell-Befehl...")
    r = run_shell("whoami")
    print(f"  whoami -> {r['stdout']} (success={r['success']})")
