#!/usr/bin/env python3
"""Wenn SSH geht: Wireless-ADB auf Xiaomi per Root an, dann adb connect testen."""
import subprocess, os, sys

IP = "10.58.220.131"
PORT = "5555"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack"]

def sh(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()
    except Exception as e:
        return 1, str(e)

def main():
    rc, out = sh(SSH + ["echo", "SSH_OK"])
    if rc != 0 or "SSH_OK" not in out:
        print("FAIL SSH:", out[:200])
        return 1
    print("SSH OK")
    enable = (
        "su -c 'setprop service.adb.tcp.port %s; "
        "settings put global adb_wifi_enabled 1 2>/dev/null; "
        "stop adbd 2>/dev/null; start adbd 2>/dev/null; "
        "getprop service.adb.tcp.port; echo HEAL_DONE'"
    ) % PORT
    rc2, out2 = sh(SSH + [enable], timeout=20)
    print("ENABLE", out2[:300])
    subprocess.run(["adb", "connect", "%s:%s" % (IP, PORT)], capture_output=True, text=True, timeout=10)
    rc3, out3 = sh(["adb", "devices"])
    print("ADB", out3)
    ok = (IP in out3 and "device" in out3)
    print("RESULT", "OK" if ok else "NO_DEVICE")
    return 0 if ok else 2

if __name__ == "__main__":
    sys.exit(main())
