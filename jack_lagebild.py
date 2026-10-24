#!/usr/bin/env python3
"""JACK_TUNE_LAGEBILD (Kap 292): Ein Aufruf, Lagebild beider Geraete. NUR LESEN.
Honor ueber Shizuku (rish, uid 2000), Xiaomi ueber ssh xiaomi-jack + su.
Datenschutz: Benachrichtigungen nur als Paketname + Anzahl, nie Titel/Text.
Fahrmodus: aktives Bluetooth-Audiogeraet des Honor beginnt mit MBUX / MB Bluetooth.
Zustand in ~/jack/.fahrmodus (json). Aufruf: python3 jack_lagebild.py [--fahrmodus]
"""
import json, os, re, subprocess, sys, time

J = os.path.expanduser('~/jack')
FAHR_DATEI = os.path.join(J, '.fahrmodus')
LKW_MUSTER = re.compile(r'^(MBUX\b|MB Bluetooth\b)', re.I)
MODULE_VERSION = '2026-10-21b'


def _run(cmd, timeout=12):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        return 124, ''
    except OSError as e:
        return 127, str(e)


def _rish(cmd, timeout=12):
    """rish-stdout verliert Daten (gemessen 21.10.: gleiche Abfrage 0-21 Treffer).
    Deshalb schreibt die Shizuku-Shell in eine Datei im gemeinsamen Speicher, Termux liest sie
    und loescht sie sofort (Inhalt kann privat sein)."""
    f = '/sdcard/Download/.jack_rish_%d.txt' % os.getpid()
    lokal = '/storage/emulated/0/Download/' + os.path.basename(f)
    t = '/data/local/tmp/' + os.path.basename(f)  # JACK_TUNE_RISHTMP (Kap 301): cmd-Dienste (am broadcast, appops) melden 'Failed transaction', wenn sie direkt nach /sdcard schreiben
    rc, _ = _run(['rish', '-c', '( %s ) </dev/null > %s 2>&1; cat %s > %s; rm -f %s' % (cmd, t, t, f, t)], timeout)
    try:
        with open(lokal, errors='replace') as fh:
            out = fh.read()
    except OSError:
        out = ''
    finally:
        try:
            os.remove(lokal)
        except OSError:
            pass
    return rc, out


def _xi(script, timeout=20):
    """Xiaomi ueber den JACK-Schutzpfad (jack_xiaomi.run_shell: Breaker, IP-Wechsel, su-Quoting)."""
    try:
        import jack_xiaomi
        r = jack_xiaomi.run_shell(script, as_root=True, timeout=timeout)
        return (0 if r.get('success') else (r.get('returncode') or 1)), (r.get('stdout') or '')
    except Exception as e:
        return 127, str(e)


def honor_bluetooth():
    rc, out = _rish('dumpsys bluetooth_manager', 15)
    if rc != 0 or not out:
        return {'ok': False, 'grund': 'rish rc=%s' % rc}
    namen = {}
    for m in re.finditer(r'^\s+(XX:XX:XX:XX:[0-9A-F:]{5}) \[[^\]]*\]\[[^\]]*\] (.+)$', out, re.M):
        namen[m.group(1)] = m.group(2).strip()
    aktiv = None
    m = re.search(r'mActiveDevice: (XX:XX:XX:XX:[0-9A-F:]{5})', out)
    if m:
        aktiv = m.group(1)
    an = bool(re.search(r'^\s+State: ON', out, re.M))
    name = namen.get(aktiv) if aktiv else None
    return {'ok': True, 'an': an, 'aktiv': name, 'gekoppelt': len(namen)}


def honor():
    d = {'bluetooth': honor_bluetooth()}
    rc, out = _rish('dumpsys battery', 8)
    lv = re.search(r'level: (\d+)', out or '')
    tp = re.search(r'temperature: (\d+)', out or '')
    d['akku'] = int(lv.group(1)) if lv else None
    d['temp_c'] = int(tp.group(1)) / 10 if tp else None
    rc, out = _rish('dumpsys window', 8)
    fm = re.search(r'mCurrentFocus=Window\{\S+ \S+ ([^}\s/]+)', out or '')
    d['vordergrund'] = fm.group(1) if fm else None
    return d


# Kein Temp-Dump mehr (Review ChatGPT A19): ueber sshd duerfen Pipes direkt filtern,
# der volle Benachrichtigungstext verlaesst dumpsys nie.
XI_SCRIPT = (
    'echo S1; dumpsys window 2>/dev/null | grep -m1 -o "isKeyguardShowing=[a-z]*"; '
    'dumpsys window 2>/dev/null | grep -m1 mCurrentFocus; '
    'echo S2; dumpsys battery 2>/dev/null | grep -E "^ *(level|temperature|status):"; '
    'echo S3; dumpsys notification 2>/dev/null | grep -o "pkg=[a-zA-Z0-9_.]*" | sort | uniq -c | sort -rn | head -8; '
    'echo S4 LOGERR $(logcat -d -t 400 *:E 2>/dev/null | wc -l); '
    'echo S5 IP $(ip -4 addr show wlan0 | grep -o "inet [0-9.]*")'
)
TEILE = ('S1', 'S2', 'S3', 'S4', 'S5')


def xiaomi():
    rc, out = _xi(XI_SCRIPT)
    if rc != 0 and not out:
        return {'ok': False, 'status': 'FEHLT', 'grund': 'xiaomi rc=%s' % rc}
    fehlend = [t for t in TEILE if not re.search(r'^' + t + r'\b', out, re.M)]
    d = {'ok': not fehlend, 'status': 'OK' if not fehlend else 'TEILWEISE', 'fehlend': fehlend}
    m = re.search(r'isKeyguardShowing=(\w+)', out); d['gesperrt'] = (m.group(1) == 'true') if m else None
    m = re.search(r'mCurrentFocus=Window\{\S+ \S+ ([^}\s/]+)', out); d['vordergrund'] = m.group(1) if m else None
    m = re.search(r'level: (\d+)', out); d['akku'] = int(m.group(1)) if m else None
    m = re.search(r'temperature: (\d+)', out); d['temp_c'] = int(m.group(1)) / 10 if m else None
    d['benachrichtigungen'] = {p: int(n) for n, p in re.findall(r'^\s*(\d+) pkg=(\S+)', out, re.M)}
    m = re.search(r'LOGERR (\d+)', out); d['log_fehler_400'] = int(m.group(1)) if m else None
    m = re.search(r'IP inet ([0-9.]+)', out); d['ip'] = m.group(1) if m else None
    return d


def fahrmodus(bt=None):
    bt = bt or honor_bluetooth()
    jetzt = int(time.time())
    alt = {}
    try:
        with open(FAHR_DATEI) as f:
            alt = json.load(f)
    except (OSError, ValueError):
        alt = {}
    if not bt.get('ok'):
        return dict(alt, unsicher=True)  # nie raten: alten Zustand behalten
    aktiv = bool(bt.get('aktiv') and LKW_MUSTER.match(bt['aktiv']))
    neu = {'aktiv': aktiv, 'geraet': bt.get('aktiv') if aktiv else None,
           'seit': alt.get('seit') if alt.get('aktiv') == aktiv else jetzt, 'geprueft': jetzt}
    tmp = FAHR_DATEI + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(neu, f)
    os.replace(tmp, FAHR_DATEI)
    neu['wechsel'] = alt.get('aktiv') != aktiv
    return neu


def lagebild():
    h = honor()
    return {'zeit': time.strftime('%Y-%m-%d %H:%M:%S'), 'honor': h, 'xiaomi': xiaomi(),
            'fahrmodus': fahrmodus(h['bluetooth'])}


if __name__ == '__main__':
    if '--fahrmodus' in sys.argv:
        print(json.dumps(fahrmodus(), ensure_ascii=False))
    else:
        print(json.dumps(lagebild(), ensure_ascii=False, indent=1))
