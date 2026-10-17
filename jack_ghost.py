import subprocess, re, xml.etree.ElementTree as ET

HOST = 'xiaomi-jack'
DUMP = '/sdcard/jack_ui.xml'

def _ssh(cmd, timeout=15):
    return subprocess.run(['ssh', HOST, cmd], capture_output=True, text=True, timeout=timeout)

def hol_xiaomi_ui(versuche=3):
    # JACK_TUNE_GHOSTFRESH: kein veralteter Dump, wenn uiautomator scheitert (Arena C2 T01)
    # JACK_TUNE_GHOSTRETRY (17.10.2026): uiautomator wird bei schnell aufeinander folgenden Dumps
    # gelegentlich abgeschossen (Exit 137, gemessen). Dann leer -> bis zu 3 Versuche mit Pause.
    import time as _t
    try:
        open('/data/data/com.termux/files/home/jack/.ui_busy', 'w').close()  # JACK_TUNE_UIBUSY: Fokus-Monitor dumpt dann nicht dazwischen
    except Exception:
        pass
    cmd = 'su -c "rm -f ' + DUMP + '; uiautomator dump ' + DUMP + '" >/dev/null 2>&1; su -c "cat ' + DUMP + '"'
    grund = ''
    for i in range(max(1, versuche)):
        if i:
            _t.sleep(1.0 + 0.5 * i)
        try:
            r = _ssh(cmd)
        except Exception as e:
            grund = 'FEHLER: ' + str(e)[:150]
            continue
        out = (r.stdout or '').strip()
        if out.startswith('<'):
            return out
        grund = 'FEHLER: kein XML - ' + (out or r.stderr)[:200]
    return grund

def _mitte(bounds):
    m = re.findall(r'-?[0-9]+', bounds or '')
    if len(m) != 4:
        return None
    x1, y1, x2, y2 = [int(v) for v in m]
    return (x1 + x2) // 2, (y1 + y2) // 2

def finde_element(xml_string, suchtext=''):
    if not xml_string or not xml_string.startswith('<'):
        return []
    try:
        root = ET.fromstring(xml_string)
    except Exception:
        return []
    s = (suchtext or '').lower()
    treffer = []
    for n in root.iter('node'):
        t = n.get('text', '') or ''
        d = n.get('content-desc', '') or ''
        if s and s not in t.lower() and s not in d.lower():
            continue
        if not s and n.get('clickable') != 'true':
            continue
        pos = _mitte(n.get('bounds', ''))
        if not pos:
            continue
        treffer.append({'text': t or d, 'klasse': n.get('class', ''), 'x': pos[0], 'y': pos[1]})
    return treffer

def tap_xiaomi(x, y):
    try:
        r = _ssh('su -c "input tap ' + str(int(x)) + ' ' + str(int(y)) + '"')
        return 'Tap ' + str(x) + ',' + str(y) + ' rc=' + str(r.returncode)
    except Exception as e:
        return 'FEHLER: ' + str(e)[:150]

if __name__ == '__main__':
    xml = hol_xiaomi_ui()
    if xml.startswith('FEHLER'):
        print(xml)
    else:
        print('XML Laenge:', len(xml))
        tr = finde_element(xml, '')
        print('Klickbare Elemente:', len(tr))
        for e in tr[:3]:
            print(e)
