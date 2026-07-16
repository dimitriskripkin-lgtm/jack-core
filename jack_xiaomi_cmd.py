import os, json, time, subprocess

XIAOMI_IP = "10.244.147.131"
SSH_KEY = os.path.expanduser("~/.ssh/id_jack")
CMD_FILE = "/sdcard/jack_cmd.json"
RESULT_FILE = "/sdcard/jack_result.json"

APP_MAP = {
    'bluetooth': 'com.android.settings/.bluetooth.BluetoothSettings',
    'wlan': 'com.android.settings/.wifi.WifiSettings',
    'wifi': 'com.android.settings/.wifi.WifiSettings',
    'einstellungen': 'com.android.settings/.Settings',
    'whatsapp': 'com.whatsapp/.Main',
    'telefon': 'com.google.android.dialer/.DialtactsActivity',
    'kamera': 'com.android.camera2/.CameraActivity',
    'akku': 'com.android.settings/.fuelgauge.PowerUsageSummary',
}

def _ssh(cmd, timeout=15):
    r = subprocess.run(
        ["ssh", "-i", SSH_KEY, "-p", "8022",
         "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=6",
         f"u0_a0@{XIAOMI_IP}", cmd],
        capture_output=True, text=True, timeout=timeout
    )
    return r.stdout.strip(), r.returncode

def send_cmd(goal, package=None):
    if not package:
        for kw, pkg in APP_MAP.items():
            if kw in goal.lower():
                package = pkg
                break
    cmd = {"goal": goal}
    if package:
        cmd["package"] = package
    safe = json.dumps(cmd).replace("'", "")
    _ssh(f"echo '{safe}' > {CMD_FILE}")
    print(f"[xiaomi_cmd] Gesendet: {cmd}")

def wait_result(timeout=30):
    for _ in range(timeout // 2):
        time.sleep(2)
        out, rc = _ssh(f"cat {RESULT_FILE} 2>/dev/null && rm -f {RESULT_FILE}")
        if rc == 0 and out.strip().startswith("{"):
            try:
                return json.loads(out.strip())
            except Exception:
                pass
    return {"ok": False, "grund": "Timeout"}

def xiaomi(goal, package=None):
    send_cmd(goal, package)
    return wait_result()
