import sys, time, json, os, subprocess
sys.path.insert(0, '/data/data/com.termux/files/home/jack')
from jack_android import _sh, get_ui_tree, adb_setup

CMD_FILE = '/sdcard/jack_cmd.json'
RESULT_FILE = '/sdcard/jack_result.json'
LOG_FILE = '/data/data/com.termux/files/home/jack/alpha.log'

def log(msg):
    ts = time.strftime('%H:%M:%S')
    line = '[' + ts + '] ' + str(msg)
    print(line, flush=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def adb_tap(x, y):
    r = subprocess.run('adb -s 127.0.0.1:5555 shell input tap ' + str(x) + ' ' + str(y),
                       shell=True, capture_output=True, text=True)
    log('adb tap ' + str(x) + ',' + str(y) + ' rc=' + str(r.returncode))
    return r.returncode == 0

def execute(cmd):
    goal = cmd.get('goal', '')
    package = cmd.get('package', '')
    log('Auftrag: ' + goal)
    if package:
        _sh('am start -n ' + package, root=True)
        time.sleep(3)
    els = get_ui_tree()
    log('UI: ' + str(len(els)) + ' Elemente')
    words = [w.lower() for w in goal.split() if len(w) > 2]
    for e in els:
        txt = e.get('text', '')
        dsc = e.get('desc', '')
        ctr = e.get('center', (0, 0))
        haystack = (txt + ' ' + dsc).lower()
        if any(w in haystack for w in words):
            log('Gefunden: ' + txt + ' -> tippe ' + str(ctr))
            ok = adb_tap(ctr[0], ctr[1])
            time.sleep(3)
            els2 = get_ui_tree()
            first = els2[0].get('text', '') if els2 else ''
            return {'ok': ok, 'aktion': 'tap', 'koordinaten': str(ctr), 'danach': first, 'elemente': len(els2)}
    log('Kein lokaler Treffer')
    return {'ok': False, 'grund': 'Nicht gefunden', 'elemente': len(els)}

def main():
    log('JACK Node Alpha gestartet')
    adb_setup()
    log('ADB bereit')
    while True:
        try:
            if os.path.exists(CMD_FILE):
                with open(CMD_FILE) as f:
                    cmd = json.load(f)
                os.remove(CMD_FILE)
                log('CMD: ' + str(cmd))
                result = execute(cmd)
                with open(RESULT_FILE, 'w') as f:
                    json.dump(result, f)
                log('Result: ' + str(result))
        except Exception as e:
            log('FEHLER: ' + str(e))
        time.sleep(2)

main()
