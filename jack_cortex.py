#!/usr/bin/env python3
import os, time, subprocess, sqlite3, sys

sys.path.append(os.path.expanduser('~/jack'))
import jack_config

ERROR_DB = jack_config.get_param('STORAGE', 'db_path')
XIAOMI_IP = jack_config.get_param('NETWORK', 'xiaomi_ip')
XIAOMI_SSH_PORT = 8022
SSH_FAIL_COUNT = 0
SSH_FAIL_THRESHOLD = 3
SSH_ERR_COUNT = 0

def log_status(msg):
    print('[Cortex-Status] ' + str(msg))

def log_error(msg):
    import inspect, linecache
    if os.path.exists(ERROR_DB):
        try:
            frame = inspect.currentframe().f_back
            file_path = frame.f_code.co_filename
            line_num = frame.f_lineno
            context = linecache.getline(file_path, line_num).strip()
            with sqlite3.connect(ERROR_DB) as con:
                con.execute("INSERT INTO errors (module, error_type, error_msg, file_path, line_num, context, resolved, timestamp) VALUES ('jack_cortex', 'CORTEX_ERR', ?, ?, ?, ?, 0, datetime('now'))", (msg, file_path, line_num, context))
                con.commit()
        except: pass



def _ssh_ok(ip):
    try:
        r = subprocess.run(
            ["ssh","-i",os.path.expanduser("~/.ssh/id_jack"),"-o","BatchMode=yes",
             "-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=/dev/null",
             "-o","ConnectTimeout=3","-p",str(XIAOMI_SSH_PORT),f"root@{ip}","true"],
            capture_output=True, timeout=6)
        return r.returncode == 0
    except Exception:
        return False


def find_xiaomi():
    cache_file = os.path.expanduser("~/jack/.last_xiaomi_ip")
    known = jack_config.get_param('NETWORK', 'xiaomi_ip')
    if _ssh_ok(known):
        with open(cache_file,"w") as f: f.write(known)
        return known
    if os.path.exists(cache_file):
        try:
            cached = open(cache_file).read().strip()
            if cached and cached != known and _ssh_ok(cached):
                return cached
        except Exception:
            pass
    for i in range(2, 255):
        ip = f"10.244.147.{i}"
        if ip == known:
            continue
        if _ssh_ok(ip):
            with open(cache_file,"w") as f: f.write(ip)
            log_error(f"[Cortex] Xiaomi auf neuer IP gefunden: {ip}")
            return ip
    return known


def check_and_heal():
    global SSH_FAIL_COUNT, SSH_ERR_COUNT
    
    global XIAOMI_IP
    XIAOMI_IP = find_xiaomi()
    ping = subprocess.run(["ping", "-c", "1", "-W", "2", XIAOMI_IP], capture_output=True)
    if ping.returncode != 0:
        SSH_FAIL_COUNT += 1
        if SSH_FAIL_COUNT == 1 or SSH_FAIL_COUNT % 5 == 0:
            log_status(f"[Cortex] Xiaomi nicht erreichbar (Ping {SSH_FAIL_COUNT}x fehlgeschlagen)")
        
        if SSH_FAIL_COUNT >= SSH_FAIL_THRESHOLD:
            log_status(f"[Cortex] Versuche WiFi-Recovery auf Xiaomi (Fail #{SSH_FAIL_COUNT})")
            try:
                recovery = subprocess.run(
                    ["ssh", "-i", os.path.expanduser("~/.ssh/id_jack"), "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", "-p", str(XIAOMI_SSH_PORT), f"root@{XIAOMI_IP}", 
                     "su -c 'svc wifi disable; sleep 3; svc wifi enable'"],
                    capture_output=True, text=True, timeout=25
                )
                if recovery.returncode == 0:
                    log_status("[Cortex] WiFi-Recovery erfolgreich")
                    SSH_FAIL_COUNT = 0
                else:
                    log_status(f"[Cortex] WiFi-Recovery fehlgeschlagen: {recovery.stderr.strip()}")
            except Exception as e:
                log_status(f"[Cortex] WiFi-Recovery Exception: {str(e)}")
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
            SSH_ERR_COUNT += 1
            if SSH_ERR_COUNT == 1 or SSH_ERR_COUNT % 30 == 0:
                log_error(f"[Cortex] SSH-Fehler (#{SSH_ERR_COUNT}): {ssh_test.stderr.strip()}")
            return
        SSH_ERR_COUNT = 0
    except subprocess.TimeoutExpired:
        SSH_ERR_COUNT += 1
        if SSH_ERR_COUNT == 1 or SSH_ERR_COUNT % 30 == 0:
            log_error(f"[Cortex] SSH-Timeout (#{SSH_ERR_COUNT})")
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
