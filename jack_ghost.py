import subprocess, re, xml.etree.ElementTree as ET

HOST = 'xiaomi-jack'
DUMP = '/sdcard/jack_ui.xml'

def _ssh(cmd, timeout=15):
    return subprocess.run(['ssh', HOST, cmd], capture_output=True, text=True, timeout=timeout)

def hol_xiaomi_ui():
    cmd = 'su -c "uiautomator dump ' + DUMP + '" >/dev/null 2>&1; su -c "cat ' + DUMP + '"'
    try:
        r = _ssh(cmd)
    except Exception as e:
        return 'FEHLER: ' + str(e)[:150]
    out = (r.stdout or '').strip()
    if not out.startswith('<'):
        return 'FEHLER: kein XML - ' + (out or r.stderr)[:200]
    return out

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
