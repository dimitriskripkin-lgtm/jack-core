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
    # Xiaomi UI-Befehle: Screen vorher entsperren (Qwen 21.08.)
    _ui = ('monkey', 'am start', 'input ', 'uiautomator')
    if 'xiaomi-jack' in cmd and any(u in cmd for u in _ui):
        try:
            import jack_xiaomi_unlock
            _us = jack_xiaomi_unlock.ensure_unlocked()
            import jack_log; jack_log.log_decision('UNLOCK', _us, cmd[:60])
        except Exception:
            pass
    try:
        r = subprocess.run(['bash','-lc',cmd], capture_output=True,
                           text=True, timeout=timeout,
                           cwd=os.path.expanduser('~/jack'))
        out = (r.stdout or '') + (r.stderr or '')
        out = out.strip() or '(kein Output)'
        rc = r.returncode
        try:
            import jack_observer
            obs_ok, errs = jack_observer.check_output(r.stdout or '', r.stderr or '')
            if not obs_ok and rc == 0:
                rc = 99
                out = '[OBSERVER BLOCK] OS luegt mit rc=0! Fehler: ' + str(errs) + '\n\n' + out
        except Exception:
            pass
        if len(out) > 3000:
            out = out[:1500] + chr(10) + '...' + chr(10) + out[-1200:]
        try:
            import jack_log; jack_log.log_decision('EXEC', cmd[:80], 'rc=' + str(rc))
        except Exception: pass
        # Outcome-Tracking: Befehl + Ergebnis speichern (Qwen 21.08.)
        try:
            import jack_outcome_tracker
            jack_outcome_tracker.log_outcome(cmd[:500], rc, out[:1000])
        except Exception:
            pass
        return 'rc=' + str(rc) + chr(10) + out
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
