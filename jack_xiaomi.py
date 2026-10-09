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


def ssh(cmd, timeout=8):
    """JACK_TUNE_XIGATE Weg ist ein Zustand."""
    try:
        r = run_shell(cmd, as_root=True, timeout=timeout)  # JACK_TUNE_SSHROOT offizieller Weg ist Root
        if r.get("success"):
            return {"ok": True, "lage": "OK", "out": (r.get("stdout") or "")[:1500]}
        return {"ok": False, "lage": "TEMPORAER_WEG", "out": (r.get("stderr") or "")[:400]}
    except Exception as e:
        return {"ok": False, "lage": "TEMPORAER_WEG", "out": str(e)[:200]}


def lage():
    """JACK_TUNE_LAGE Akku ohne Root, WLAN und Speicher mit Root."""
    import json as _json
    bat = run_shell("termux-battery-status", as_root=False, timeout=12)
    pct = temp = "?"
    if bat.get("success"):
        try:
            b = _json.loads(bat.get("stdout") or "{}")
            pct = str(b.get("percentage", "?"))
            temp = str(b.get("temperature", "?"))
        except Exception:
            pct = (bat.get("stdout") or "")[:40]
    wifi = ssh("dumpsys wifi | grep -m1 'Wi-Fi is'", timeout=12)
    speicher = ssh("df -h /data | tail -1", timeout=12)
    w = (wifi.get("out") or "WLAN unbekannt").replace("Wi-Fi is ", "")[:40]
    s = (speicher.get("out") or "Speicher unbekannt")[:80]
    return "Xiaomi Lage: Akku " + pct + "% " + temp + "C, WLAN " + w + ", Speicher " + s

def _nummer(raw):
    n = "".join(ch for ch in str(raw) if ch.isdigit() or ch == "+")
    if len(n) < 3 or len(n) > 16:
        return ""
    return n

def wahl(nummer):
    """Oeffnet die Waehlscheibe. Waehlt nicht."""
    n = _nummer(nummer)
    if not n:
        return "Nummer ungueltig."
    r = ssh("am start -a android.intent.action.DIAL -d tel:" + n, timeout=12)
    if r.get("ok"):
        return "Waehlscheibe offen fuer " + n + ". Nicht gewaehlt."
    return "Wahl fehlgeschlagen: " + (r.get("out") or "")[:80]

def sms_vorbereiten(nummer, text):
    """Oeffnet die Nachricht. Schickt nicht."""
    n = _nummer(nummer)
    body = " ".join(str(text or "").split())[:140]
    body = "".join(ch for ch in body if ch.isalnum() or ch in " .,:-")
    if not n or not body:
        return "Nummer oder Text fehlt."
    r = ssh("am start -a android.intent.action.SENDTO -d sms:" + n + " --es sms_body '" + body + "'", timeout=12)
    if r.get("ok"):
        return "Nachricht vorbereitet an " + n + ". Nicht abgeschickt."
    return "Nachricht fehlgeschlagen: " + (r.get("out") or "")[:80]

_BR = {"fails": 0, "until": 0.0}  # JACK_TUNE_XIBREAKER


def _br_note(verbindung_ok):
    import time as _tm
    try:
        import jack_xibreaker as _xb; _xb.note(verbindung_ok)  # JACK_TUNE_XIBREAKER2
    except Exception:
        pass
    if verbindung_ok:
        _BR["fails"] = 0
        return
    _BR["fails"] += 1
    if _BR["fails"] >= 2:
        _BR["until"] = _tm.time() + 30


def _quick_ip():
    """JACK_TUNE_XIQUICK gecachte IP ohne Vorab-Check."""
    try:
        return jack_config.get_param("NETWORK", "xiaomi_ip") or ""
    except Exception:
        return ""


def _ssh_ein(ip, full_cmd, timeout):
    return subprocess.run(
        ["ssh"] + SSH_OPTS + ["-p", str(XIAOMI_SSH_PORT), f"root@{ip}", full_cmd],
        capture_output=True, text=True, timeout=timeout
    )


def run_shell(cmd, as_root=True, timeout=15):
    import time as _tm2
    if _tm2.time() < _BR["until"]:
        return {"success": False, "stdout": "", "stderr": "Xiaomi weg (Schutz 30 s)", "returncode": -2}
    try:
        import jack_xibreaker as _xb2
        if _xb2.wait() > 0:  # JACK_TUNE_XIBREAKER2
            return {"success": False, "stdout": "", "stderr": "Xiaomi weg (Schutz 30 s)", "returncode": -2}
    except Exception:
        pass
    ip = _quick_ip() or _get_xiaomi_ip()  # JACK_TUNE_XIQUICK
    full_cmd = cmd
    if as_root and not cmd.startswith("su "):
        safe = cmd.replace("'", "'\"'\"'")
        full_cmd = "su -c '" + safe + "'"  # JACK_TUNE_SSHROOT
    elif not as_root:
        full_cmd = cmd

    try:
        result = _ssh_ein(ip, full_cmd, timeout)
        if result.returncode == 255:
            _neu = _get_xiaomi_ip()
            if _neu and _neu != ip:
                result = _ssh_ein(_neu, full_cmd, timeout)
        _br_note(result.returncode != 255)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        _br_note(False)
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
        _jm.save('xiaomi_explore', summary, intent='explore', source='explorer')
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
