#!/usr/bin/env python3
import subprocess
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
import os
import sys

sys.path.insert(0, os.path.expanduser("~/jack"))
import jack_config

XIAOMI_SSH_PORT = 8022
SSH_KEY = os.path.expanduser("~/.ssh/id_jack")
SSH_OPTS = [
    "-i", SSH_KEY,
    "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=accept-new",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "ConnectTimeout=5",
    "-o", "ControlMaster=auto",
    "-o", "ControlPath="+os.path.expanduser("~/.ssh/sockets/%r@%h:%p"),
    "-o", "ControlPersist=120",
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

    try:
        import urllib.request as _ur3; _ur3.urlopen(f"http://{ip}:8022",timeout=2)
        status["reachable"]=True
    except Exception:
        status["reachable"]=False
        return status

    battery = run_shell("dumpsys battery | grep level")
    status["battery"] = battery["stdout"] if battery["success"] else "unbekannt"

    uptime = run_shell("uptime")
    status["uptime"] = uptime["stdout"] if uptime["success"] else "unbekannt"

    shizuku = run_shell("pgrep -f shizuku")
    status["shizuku_running"] = shizuku["success"] and bool(shizuku["stdout"])

    return status


def push_file_delta(local_path, remote_path):
    """Uebertraegt nur wenn lokale Datei neuer als remote (Delta Transfer)."""
    try:
        local_mtime = int(os.path.getmtime(local_path))
        r = run_shell(f"stat -c %Y {remote_path} 2>/dev/null || echo 0")
        remote_mtime = int(r['stdout'].strip() or 0)
        if local_mtime <= remote_mtime:
            return {'skipped': True, 'reason': 'remote aktuell'}
        with open(local_path,'r') as f: content = f.read()
        ok = write_file(remote_path, content)
        if ok:
            try:
                import jack_log
                jack_log.log_decision('DELTA-PUSH', local_path + ' -> ' + remote_path)
            except Exception: pass
        return {'skipped': False, 'success': ok}
    except Exception as e:
        return {'skipped': False, 'success': False, 'error': str(e)}

def explore_next():
    """Autonome Idle-Exploration: JACK schaut selbst was auf dem Xiaomi los ist."""
    import json, datetime
    results={}

    # CPU-Last
    r=run_shell('cat /proc/loadavg', as_root=True, timeout=10)
    try: results['cpu_user']='Load: '+r['stdout'].split()[0]
    except Exception: results['cpu_user']='unbekannt'

    # RAM
    r=run_shell('cat /proc/meminfo | grep MemAvailable', as_root=False, timeout=10)
    try: results['ram']=str(round(int(r['stdout'].split()[1])/1024))+'MB frei'
    except Exception: results['ram']='unbekannt'

    # Akku
    r=run_shell('cat /sys/class/power_supply/battery/capacity', as_root=True, timeout=10)
    results['battery']=r['stdout'].strip()+'%' if r['success'] and r['stdout'].strip().isdigit() else 'unbekannt'

    # Aktive App
    r=run_shell('dumpsys activity top 2>/dev/null | grep ACTIVITY | head -1', as_root=False, timeout=10)
    results['active_app']=r['stdout'].strip() if r['success'] else 'unbekannt'

    # Temperatur
    r=run_shell("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0", as_root=False, timeout=10)
    try: results['temp_c']=round(int(r['stdout'].strip())/1000,1)
    except Exception: results['temp_c']='unbekannt'

    # Disk
    r=run_shell('df /data | tail -1', as_root=False, timeout=10)
    try:
        parts=r['stdout'].split(); results['disk_used']=parts[2]+'KB used, '+parts[4]+' full'
    except Exception: results['disk_used']='unbekannt'

    results['timestamp']=datetime.datetime.now().isoformat()
    results['source']='explore_next'

    # In RAG speichern
    try:
        import jack_memory as _jm
        summary=json.dumps(results, ensure_ascii=False)
        _jm.save('xiaomi_explore', summary, intent='explore')
    except Exception as e:
        try: import jack_log; jack_log.log_decision('EXPLORE-FEHLER', str(e)[:100])
        except Exception: pass

    return results

if __name__ == "__main__":
    print("[XIAOMI] Status-Check...")
    s = get_status()
    for k, v in s.items():
        print(f"  {k}: {v}")

    print("\n[XIAOMI] Test: einfacher Shell-Befehl...")
    r = run_shell("whoami")
    print(f"  whoami -> {r['stdout']} (success={r['success']})")
