#!/usr/bin/env python3
"""SSH ok -> ADB-TCP an -> adb connect. Return 0 nur bei status device."""
import subprocess, sys
IP, PORT = "10.229.239.131", "5555"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack"]

def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:
        return 1, str(e)

def main():
    rc, out = run(SSH + ["echo", "SSH_OK"])
    if rc != 0 or "SSH_OK" not in out:
        print("FAIL_SSH", out[:200]); return 1
    print("SSH_OK")
    en = "su -c 'setprop service.adb.tcp.port %s; settings put global adb_wifi_enabled 1 2>/dev/null; stop adbd; start adbd; sleep 1; getprop service.adb.tcp.port'" % PORT
    _, o2 = run(SSH + [en], timeout=25)
    print("ENABLE", o2[:200])
    run(["adb", "kill-server"], timeout=10)
    run(["adb", "start-server"], timeout=10)
    run(["adb", "disconnect", "%s:%s" % (IP, PORT)], timeout=8)
    _, c = run(["adb", "connect", "%s:%s" % (IP, PORT)], timeout=12)
    print("CONNECT", c)
    _, dev = run(["adb", "devices"], timeout=8)
    print("DEVICES", dev)
    lines = [ln for ln in dev.splitlines() if IP in ln]
    ok = any(ln.split()[1] == "device" for ln in lines if len(ln.split()) >= 2)
    # BLOCK P1: Zähler + unauthorized
    count_path = "/data/data/com.termux/files/home/jack/.adb_heal_count"
    try:
        n = int(open(count_path).read().strip() or "0")
    except Exception:
        n = 0
    n += 1
    open(count_path, "w").write(str(n))
    if "unauthorized" in (dev or "").lower() or "unauthorized" in (c or "").lower():
        print("UNAUTHORIZED_POPUP")
        print("RESULT FAIL unauthorized")
        return 3
    print("RESULT", "OK" if ok else "FAIL", "count", n)
    return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(main())
