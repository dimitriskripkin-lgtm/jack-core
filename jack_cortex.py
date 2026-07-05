#!/usr/bin/env python3
import os, time, subprocess, sqlite3, sys

sys.path.append(os.path.expanduser('~/jack'))
import jack_config

ERROR_DB = jack_config.get_param('STORAGE', 'db_path')
XIAOMI_IP = jack_config.get_param('NETWORK', 'xiaomi_ip')
XIAOMI_SSH_PORT = 8022

def log_error(msg):
    if os.path.exists(ERROR_DB):
        try:
            with sqlite3.connect(ERROR_DB) as con:
                con.execute("INSERT INTO errors (module, error_type, error_msg, resolved, timestamp) VALUES ('jack_cortex', 'CORTEX_ERR', ?, 0, datetime('now'))", (msg,))
                con.commit()
        except: pass

def check_and_heal():
    ping = subprocess.run(["ping", "-c", "1", "-W", "2", XIAOMI_IP], capture_output=True)
    if ping.returncode != 0:
        log_error(f"[Cortex] Xiaomi nicht erreichbar (Ping fehlgeschlagen, IP {XIAOMI_IP})")
        return
    
    # SSH statt ADB - zuverlässiger und stabiler
    try:
        ssh_test = subprocess.run(
            ["ssh", "-p", str(XIAOMI_SSH_PORT), "-o", "ConnectTimeout=3", f"root@{XIAOMI_IP}", "whoami"],
            capture_output=True, text=True, timeout=5
        )
        if ssh_test.returncode != 0:
            log_error(f"[Cortex] SSH-Verbindung zu Xiaomi fehlgeschlagen: {ssh_test.stderr.strip()}")
            return
    except subprocess.TimeoutExpired:
        log_error("[Cortex] SSH-Timeout zu Xiaomi")
        return
    except Exception as e:
        log_error(f"[Cortex] SSH-Fehler: {str(e)}")
        return
    
    # Shizuku verifizieren
    try:
        shizuku_res = subprocess.run(
            ["ssh", "-p", str(XIAOMI_SSH_PORT), f"root@{XIAOMI_IP}", "pgrep", "-f", "shizuku"],
            capture_output=True, text=True, timeout=5
        )
        if shizuku_res.returncode != 0:
            log_error("[Cortex] Shizuku auf Xiaomi läuft nicht")
    except Exception as e:
        log_error(f"[Cortex] Shizuku-Check fehlgeschlagen: {str(e)}")

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
