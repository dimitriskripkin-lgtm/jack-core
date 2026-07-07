#!/usr/bin/env python3
import os, time, subprocess, sqlite3, sys

sys.path.append(os.path.expanduser('~/jack'))
import jack_config

ERROR_DB = jack_config.get_param('STORAGE', 'db_path')
XIAOMI_IP = jack_config.get_param('NETWORK', 'xiaomi_ip')
XIAOMI_SSH_PORT = 8022
SSH_FAIL_COUNT = 0
SSH_FAIL_THRESHOLD = 3

def log_error(msg):
    if os.path.exists(ERROR_DB):
        try:
            with sqlite3.connect(ERROR_DB) as con:
                con.execute("INSERT INTO errors (module, error_type, error_msg, resolved, timestamp) VALUES ('jack_cortex', 'CORTEX_ERR', ?, 0, datetime('now'))", (msg,))
                con.commit()
        except: pass



def find_xiaomi():
    import socket
    import os

    cache_file = os.path.expanduser("~/jack/.last_xiaomi_ip")

    # Cache-Hit-First: zuletzt erfolgreiche IP zuerst probieren, spart den vollen Scan
    if os.path.exists(cache_file):
        try:
            cached_ip = open(cache_file).read().strip()
            if cached_ip:
                s = socket.create_connection((cached_ip, 8022), timeout=0.3)
                s.close()
                return cached_ip
        except Exception:
            pass

    # Cache-Miss oder keine Cache-Datei: vollen Scan im verifizierten Subnetz
    subnet_prefix = "10.234.166"
    for i in range(2, 255):
        ip = f"{subnet_prefix}.{i}"
        try:
            s = socket.create_connection((ip, 8022), timeout=0.2)
            s.close()
            with open(cache_file, "w") as f:
                f.write(ip)
            return ip
        except (socket.timeout, ConnectionRefusedError, OSError):
            continue
    return XIAOMI_IP



def check_and_heal():
    global SSH_FAIL_COUNT
    
    global XIAOMI_IP
    XIAOMI_IP = find_xiaomi()
    ping = subprocess.run(["ping", "-c", "1", "-W", "2", XIAOMI_IP], capture_output=True)
    if ping.returncode != 0:
        SSH_FAIL_COUNT += 1
        if SSH_FAIL_COUNT == 1 or SSH_FAIL_COUNT % 5 == 0:
            log_error(f"[Cortex] Xiaomi nicht erreichbar (Ping {SSH_FAIL_COUNT}x fehlgeschlagen)")
        
        if SSH_FAIL_COUNT >= SSH_FAIL_THRESHOLD:
            log_error(f"[Cortex] Versuche WiFi-Recovery auf Xiaomi (Fail #{SSH_FAIL_COUNT})")
            try:
                recovery = subprocess.run(
                    ["ssh", "-i", os.path.expanduser("~/.ssh/id_jack"), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-p", str(XIAOMI_SSH_PORT), f"root@{XIAOMI_IP}", 
                     "su -c 'svc wifi disable; sleep 3; svc wifi enable'"],
                    capture_output=True, text=True, timeout=15
                )
                if recovery.returncode == 0:
                    log_error("[Cortex] WiFi-Recovery erfolgreich")
                    SSH_FAIL_COUNT = 0
                else:
                    log_error(f"[Cortex] WiFi-Recovery fehlgeschlagen: {recovery.stderr.strip()}")
            except Exception as e:
                log_error(f"[Cortex] WiFi-Recovery Exception: {str(e)}")
        return
    
    # Ping OK, reset counter
    if SSH_FAIL_COUNT > 0:
        log_error(f"[Cortex] Xiaomi erreichbar wieder (nach {SSH_FAIL_COUNT} Fails)")
        SSH_FAIL_COUNT = 0
    
    # SSH Test
    try:
        ssh_test = subprocess.run(
            ["ssh", "-i", os.path.expanduser("~/.ssh/id_jack"), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-p", str(XIAOMI_SSH_PORT), "-o", "ConnectTimeout=3", f"root@{XIAOMI_IP}", "su -c 'whoami'"],
            capture_output=True, text=True, timeout=5
        )
        if ssh_test.returncode != 0:
            log_error(f"[Cortex] SSH-Fehler: {ssh_test.stderr.strip()}")
            return
    except subprocess.TimeoutExpired:
        log_error("[Cortex] SSH-Timeout")
        return
    except Exception as e:
        log_error(f"[Cortex] SSH-Exception: {str(e)}")
        return

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
