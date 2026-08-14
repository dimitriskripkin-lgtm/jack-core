#!/usr/bin/env python3
import subprocess
import json

SSH_HOST = "xiaomi-jack"

def run_remote_cmd(cmd, timeout=8):
    try:
        res = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=4", SSH_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        if res.returncode == 0:
            return True, res.stdout.strip()
        return False, res.stderr.strip()
    except Exception as e:
        return False, str(e)

def inspect_xiaomi_system():
    # Zieht echte Hardware- & Prozess-Daten via SSH
    raw_script = """
    echo "=== RAM ==="
    free -m 2>/dev/null || cat /proc/meminfo | head -n 4
    echo "=== UPTIME & LOAD ==="
    uptime
    echo "=== SPEICHER ==="
    df -h /data 2>/dev/null || df -h /
    echo "=== TOP PROZESSE (RAM) ==="
    ps -eo pid,ppid,pmem,args --sort=-pmem 2>/dev/null | head -n 6 || ps | head -n 6
    """
    success, output = run_remote_cmd(raw_script)
    if not success:
        return False, f"SSH-Fehler zu {SSH_HOST}: {output}"
    return True, output

if __name__ == "__main__":
    ok, data = inspect_xiaomi_system()
    print("[OK]" if ok else "[ERR]")
    print(data)
