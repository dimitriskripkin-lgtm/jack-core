"""Xiaomi Screen-Unlock vor UI-Befehlen (Qwen 21.08.)
Kein Passwort: Wake + Swipe-Up reicht (von Dima bestaetigt)."""
import subprocess, time

SSH = ['ssh', 'xiaomi-jack']

def _su(cmd, timeout=10):
    try:
        r = subprocess.run(SSH + ['su', '-c', cmd], capture_output=True, text=True, timeout=timeout)
        return (r.stdout or '') + (r.stderr or '')
    except Exception:
        return ''

def wakefulness():
    out = _su("dumpsys power | grep mWakefulness")
    for line in out.splitlines():
        if 'mWakefulness=' in line:
            return line.split('=', 1)[1].strip()
    return 'UNKNOWN'

def keyguard_showing():
    out = _su("dumpsys window | grep isKeyguardShowing")
    if 'isKeyguardShowing=' not in out:
        return True  # JACK_TUNE_KEYGUARDCLOSED (17.10.2026): unbekannt heisst gesperrt, nicht blind weiter
    return 'isKeyguardShowing=true' in out

def unlock_sequence():
    _su("input keyevent 224")
    time.sleep(0.8)
    _su("input swipe 540 2000 540 1000 300")
    time.sleep(0.5)

def ensure_unlocked():
    # JACK_TUNE_UNLOCKVERIFY (17.10.2026): Arena C4/P07 brach ab, weil der Swipe einmal nicht griff
    # und nichts nachgeprueft wurde. Jetzt: bis zu 2 Sequenzen, danach je bis 3 s auf das Ende des Keyguards warten.
    wf = wakefulness()
    locked = keyguard_showing()
    if wf == 'Awake' and not locked:
        return 'SCHON_ENTSPERRT'
    for versuch in (1, 2):
        unlock_sequence()
        for _ in range(6):
            if not keyguard_showing():
                return 'ENTSPERRT_von_' + wf + ('_locked' if locked else '_unlocked') + ('' if versuch == 1 else '_versuch2')
            time.sleep(0.5)
    return 'NOCH_GESPERRT_von_' + wf
