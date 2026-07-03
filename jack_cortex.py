#!/usr/bin/env python3
import os, time, subprocess, sqlite3, sys

sys.path.append(os.path.expanduser('~/jack'))
import jack_config

ERROR_DB = jack_config.get_param('STORAGE', 'db_path')
XIAOMI_IP = jack_config.get_param('NETWORK', 'xiaomi_ip')
XIAOMI_PORT = jack_config.get_param('NETWORK', 'xiaomi_port')
XIAOMI_DEVICE = f"{XIAOMI_IP}:{XIAOMI_PORT}"

def log_error(msg):
    if os.path.exists(ERROR_DB):
        try:
            with sqlite3.connect(ERROR_DB) as con:
                con.execute("INSERT INTO errors (module, error_type, error_msg, resolved, timestamp) VALUES ('jack_cortex', 'CORTEX_ERR', ?, 0, datetime('now'))", (msg,))
                con.commit()
        except: pass

def check_and_heal():
    ping = subprocess.run(["ping", "-c", "1", "-W", "2", XIAOMI_IP], capture_output=True)
    if ping.returncode != 0: return
    devices_res = subprocess.run(["adb", "devices"], capture_output=True, text=True)
    connected = False
    for line in devices_res.stdout.split("\n"):
        if XIAOMI_DEVICE in line and "device" in line:
            connected = True
            break
    if not connected:
        res = subprocess.run(["adb", "connect", XIAOMI_DEVICE], capture_output=True, text=True)
        if "connected to" in res.stdout.lower():
            log_error("[Cortex] ADB-Tunnel zu Xiaomi verloren. Auto-Heal erfolgreich durchgeführt.")
        else:
            log_error(f"[Cortex] ADB-Tunnel-Heilung fehlgeschlagen: {res.stderr.strip()}")
            return
    try:
        ps_res = subprocess.run(["adb", "-s", XIAOMI_DEVICE, "shell", "ps", "-A"], capture_output=True, text=True)
        if "shizuku" not in ps_res.stdout.lower():
            subprocess.run(["adb", "-s", XIAOMI_DEVICE, "shell", "sh", "/sdcard/Android/data/moe.shizuku.privileged.api/start.sh"], capture_output=True)
            log_error("[Cortex] Shizuku auf Xiaomi war inaktiv. Start-Signal via ADB gesendet.")
    except Exception as e:
        log_error(f"[Cortex] Fehler bei Shizuku-Verifikation: {str(e)}")

def main():
    my_pid = os.getpid()
    try:
        res = subprocess.run(["pgrep", "-f", "jack_cortex.py"], capture_output=True, text=True)
        for pid in res.stdout.strip().split():
            if int(pid) != my_pid: subprocess.run(["kill", "-9", pid])
    except: pass
    while True:
        try: check_and_heal()
        except Exception as e: log_error(f"[Cortex] Loop-Error: {str(e)}")
        time.sleep(60)

if __name__ == "__main__":
    main()
