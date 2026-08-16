import subprocess, os, re

BLOCK = ['rm -rf /', 'mkfs', 'dd if=', ':(){', 'chmod -R 777 /',
         'id_jack', '.ssh/', 'api_key', 'API_KEY',
         'shutdown', 'reboot', '> /dev/sd']

def pruefe(cmd):
    low = cmd.lower()
    for b in BLOCK:
        if b.lower() in low:
            return False, 'BLOCKIERT: ' + b
    if len(cmd) > 4000:
        return False, 'BLOCKIERT: zu lang'
    return True, 'OK'

def run(cmd, timeout=120):
    ok, msg = pruefe(cmd)
    if not ok:
        return msg
    try:
        r = subprocess.run(['bash','-lc',cmd], capture_output=True,
                           text=True, timeout=timeout,
                           cwd=os.path.expanduser('~/jack'))
        out = (r.stdout or '') + (r.stderr or '')
        out = out.strip() or '(kein Output)'
        if len(out) > 3000:
            out = out[:1500] + chr(10) + '...' + chr(10) + out[-1200:]
        try:
            import jack_log; jack_log.log_decision('EXEC', cmd[:80], 'rc=' + str(r.returncode))
        except Exception: pass
        return 'rc=' + str(r.returncode) + chr(10) + out
    except subprocess.TimeoutExpired:
        return 'TIMEOUT nach ' + str(timeout) + 's'
    except Exception as e:
        return 'Fehler: ' + str(e)[:200]

def extrahiere(text):
    O='[[EXEC]]'
    C='[[/EXEC]]'
    i=text.find(O)
    j=text.rfind(C)
    if i<0 or j<0 or j<=i: return None
    return text[i+len(O):j].strip()
