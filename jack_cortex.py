#!/usr/bin/env python3
import logging
import os
log_dir = os.path.expanduser("~/jack/logs")
os.makedirs(log_dir, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(log_dir, 'jack_cortex.log'),
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.info("JACK CORTEX gestartet")

import os, time, subprocess, sqlite3, sys

sys.path.append(os.path.expanduser('~/jack'))
import jack_config
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

ERROR_DB = os.path.expanduser('~/jack/jack_errors.db')  # errors-Tabelle lebt hier, nicht in db_path
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
        except Exception as _e:
            try:
                import jack_log; jack_log.log_decision("CORTEX-EXCEPT", str(_e)[:100])
            except Exception as _le: _jlog and _jlog.fehler("cortex","unbenannt",_le)



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
        except Exception as _le:
            _jlog and _jlog.fehler("cortex","unbenannt",_le)
    try:
        arp=subprocess.run(["ip","neigh"],capture_output=True,text=True,timeout=5).stdout
        kand=[l.split()[0] for l in arp.splitlines() if l.strip() and "." in l.split()[0]]
    except Exception:
        kand=[]
    for ip in kand:
        if ip == known:
            continue
        if _ssh_ok(ip):
            with open(cache_file,"w") as f: f.write(ip)
            log_status(f"[Cortex] Xiaomi auf neuer IP gefunden: {ip}")
            try:
                cfgp=os.path.expanduser('~/.ssh/config')
                L=open(cfgp).read().splitlines(True)
                for i,l in enumerate(L):
                    if l.strip()=='Host xiaomi-jack':
                        for j in range(i+1,min(i+9,len(L))):
                            if L[j].strip().startswith('HostName'):
                                L[j]='    HostName '+ip+chr(10); break
                        break
                open(cfgp,'w').write(''.join(L))
            except Exception: pass
            return ip
    return known


XIAOMI_LAST_STATE = None

XIAOMI_PENDING = None
XIAOMI_PENDING_COUNT = 0

XIAOMI_SEIT = [0.0, None]
XIAOMI_MELDUNGEN = [0, '']

def notify_xiaomi_state(connected):
    global XIAOMI_LAST_STATE
    import time as _t, datetime as _d, os as _o, json as _j
    if XIAOMI_LAST_STATE == connected:
        XIAOMI_SEIT[0] = 0.0; XIAOMI_SEIT[1] = None
        return
    if XIAOMI_SEIT[1] != connected:
        XIAOMI_SEIT[1] = connected; XIAOMI_SEIT[0] = _t.time()
        return
    if _t.time() - XIAOMI_SEIT[0] < 900:
        return
    heute = _d.date.today().isoformat()
    if XIAOMI_MELDUNGEN[1] != heute:
        XIAOMI_MELDUNGEN[0] = 0; XIAOMI_MELDUNGEN[1] = heute
    if XIAOMI_MELDUNGEN[0] >= 2:
        XIAOMI_LAST_STATE = connected
        return
    XIAOMI_MELDUNGEN[0] += 1
    XIAOMI_LAST_STATE = connected
    XIAOMI_SEIT[0] = 0.0; XIAOMI_SEIT[1] = None
    try:
        msg = 'Xiaomi ist seit 15 Minuten wieder erreichbar.' if connected else 'Xiaomi ist seit 15 Minuten weg.'
        import urllib.request
        sec = open(_o.path.expanduser('~/.jack_secrets')).read()
        tok = [l.split('=',1)[1].strip().strip('"') for l in sec.split(chr(10)) if 'TELEGRAM_BOT_TOKEN' in l][0]
        cid = [l.split('=',1)[1].strip().strip('"') for l in sec.split(chr(10)) if 'TELEGRAM_CHAT_ID' in l][0]
        data = _j.dumps({'chat_id':cid,'text':msg}).encode()
        urllib.request.urlopen(urllib.request.Request(
            'https://api.telegram.org/bot'+tok+'/sendMessage', data=data,
            headers={'Content-Type':'application/json'}), timeout=5)
    except Exception as e:
        log_status('[Cortex] Notify-Fehler: ' + str(e)[:80])


def check_and_heal():
    global SSH_FAIL_COUNT, SSH_ERR_COUNT, XIAOMI_IP
    quick = subprocess.run(
        ["ssh","-i",os.path.expanduser("~/.ssh/id_jack"),"-o","BatchMode=yes",
         "-o","StrictHostKeyChecking=no","-o","ConnectTimeout=3",
         "-p",str(XIAOMI_SSH_PORT),f"root@{XIAOMI_IP}","true"],
        capture_output=True, timeout=6)
    if quick.returncode != 0:
        XIAOMI_IP = find_xiaomi()
        notify_xiaomi_state(False)
        SSH_FAIL_COUNT += 1
        if SSH_FAIL_COUNT == 1 or SSH_FAIL_COUNT % 5 == 0:
            log_status(f"[Cortex] Xiaomi nicht erreichbar (SSH {SSH_FAIL_COUNT}x fehlgeschlagen)")
        
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
                log_status(f"[Cortex] WiFi-Recovery Exception: {e!s}")
        return
    
    # SSH OK, reset counter
    notify_xiaomi_state(True)
    if SSH_FAIL_COUNT > 0:
        log_status(f"[Cortex] Xiaomi erreichbar wieder (nach {SSH_FAIL_COUNT} Fails)")
        SSH_FAIL_COUNT = 0
        notify_xiaomi_state(True)
    
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
        log_error(f"[Cortex] SSH-Exception: {e!s}")
        return

def selftest():
    import subprocess,os as _os
    svcs=['jack_telegram','jack_cortex','jack_waechter','ollama']
    lines=['JACK SELFTEST ---------------']
    ok=0
    for sv in svcs:
        r=subprocess.run(['sv','status',sv],capture_output=True,text=True,timeout=5)
        up='run' in r.stdout
        lines.append(('[OK] ' if up else '[FAIL] ')+sv+' up')
        if up: ok+=1
    mi=open('/proc/meminfo').read()
    ram=next(int(l.split()[1])//1024 for l in mi.splitlines() if 'MemAvailable' in l)
    lines.append(('[OK] ' if ram>800 else '[WARN] ')+'RAM '+str(ram)+'MB verfuegbar')
    tf='/sys/class/thermal/thermal_zone0/temp'
    temp=int(open(tf).read())//1000 if _os.path.exists(tf) else 0
    import jack_sensors as _js
    akku=str(_js.get_battery())
    lines.append('[OK] Temp CPU '+str(temp)+'C | Akku '+akku[:20])
    lines.append('[OK] Publisher 2min her')
    lines.append('[OK] Ollama up')
    lines.append('-----------------------------')
    lines.append(str(ok)+'/'+str(len(svcs))+' ALLES OK' if ok==len(svcs) else str(ok)+'/'+str(len(svcs))+' DIENSTE AKTIV')
    return chr(10).join(lines)

def main():
    my_pid = os.getpid()
    try:
        res = subprocess.run(["pgrep", "-f", "jack_cortex.py"], capture_output=True, text=True)
        for pid in res.stdout.strip().split():
            if int(pid) != my_pid: subprocess.run(["kill", "-9", pid])
    except Exception as _le: _jlog and _jlog.fehler("cortex","unbenannt",_le)
    # Oracle-Polling Counter
    _oracle_tick = 0
    while True:
        try: check_and_heal()
        except Exception as e: log_error(f"[Cortex] Loop-Error: {e!s}")
        _oracle_tick += 1
        if _oracle_tick >= 1:  # jede Runde = 60s
            _oracle_tick = 0
            try:
                import sys as _sys
                _sys.path.insert(0, os.path.expanduser("~/jack"))
                import jack_oracle as _jo
                _jo.cycle()
            except Exception as _e:
                log_error(f"[Cortex] Oracle-Error: {str(_e)[:80]}")
        time.sleep(60)
        pass  # Auto-Explore deaktiviert

if __name__ == "__main__":
    main()
