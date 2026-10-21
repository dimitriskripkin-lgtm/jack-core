#!/usr/bin/env python3
"""JACK_TUNE_HANDY (Kap 298): Alltags-Skills auf dem Xiaomi, Intent/Shell zuerst (Kap 291).
timer(sekunden, text) : SET_TIMER-Intent ohne UI, Beleg = Uhr-Benachrichtigung "Timer laeuft".
medien(aktion)        : cmd media_session dispatch, Beleg = PlaybackState der aktiven Sitzung.
Nur ueber jack_xiaomi.run_shell (Schutzpfad). Aufruf: python3 jack_handy.py timer 300 Nudeln
"""
import json, re, sys, time

MODULE_VERSION = '2026-10-21'
MEDIEN = {'play': 'play', 'pause': 'pause', 'umschalten': 'play-pause', 'weiter': 'next', 'zurueck': 'previous'}


def _sh(cmd, timeout=15):
    import jack_xiaomi
    r = jack_xiaomi.run_shell(cmd, as_root=True, timeout=timeout)
    return bool(r.get('success')), (r.get('stdout') or '')


def _entsperren():
    try:
        import jack_xiaomi_unlock
        return str(jack_xiaomi_unlock.ensure_unlocked())
    except Exception as e:
        return 'UNLOCK_FEHLER ' + type(e).__name__


def timer(sekunden, text='JACK'):
    if type(sekunden) is not int or not 5 <= sekunden <= 6 * 3600:
        return {'ok': False, 'grund': 'Sekunden 5..21600'}
    text = re.sub(r'[^\w äöüÄÖÜß.-]', '', str(text))[:30] or 'JACK'
    u = _entsperren()
    ok, _ = _sh('am start -a android.intent.action.SET_TIMER --ei android.intent.extra.alarm.LENGTH %d '
                '--es android.intent.extra.alarm.MESSAGE "%s" --ez android.intent.extra.alarm.SKIP_UI true '
                '>/dev/null 2>&1; echo OK' % (sekunden, text))
    time.sleep(2)
    _, out = _sh('dumpsys notification --noredact 2>/dev/null | grep -A40 "pkg=com.android.deskclock" '
                 '| grep -o "android.title=String ([^)]*)"', 10)
    beleg = re.findall(r'\(([^)]*)\)', out)
    laeuft = any('Timer' in b for b in beleg)
    return {'ok': ok and laeuft, 'beleg': beleg[:2], 'entsperrt': u}


def medien(aktion):
    if aktion not in MEDIEN:
        return {'ok': False, 'grund': 'erlaubt: ' + ', '.join(MEDIEN)}
    _sh('cmd media_session dispatch %s >/dev/null 2>&1' % MEDIEN[aktion])
    time.sleep(1.2)
    _, out = _sh('dumpsys media_session 2>/dev/null | grep -m6 -E "^ +package=|state=PlaybackState"', 10)
    pakete = re.findall(r'package=(\S+)', out)
    zustand = re.findall(r'state=PlaybackState \{state=(\d+)', out)
    nutz = [p for p in pakete if not p.startswith('com.android.server')]
    if not nutz:
        return {'ok': False, 'grund': 'keine aktive Medien-App (z. B. Spotify erst starten)'}
    namen = {'2': 'pausiert', '3': 'spielt', '1': 'gestoppt'}
    erwartet = {'play': '3', 'pause': '2'}.get(aktion)
    z0 = zustand[0] if zustand else None
    # Ehrlich: ok nur, wenn der gemessene Zustand zur Aktion passt (bei weiter/zurueck: es spielt)
    ok = (z0 == erwartet) if erwartet else (z0 == '3')
    return {'ok': ok, 'app': nutz[0], 'zustand': namen.get(z0, 'unbekannt(%s)' % z0)}


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'timer':
        print(json.dumps(timer(int(a[1]), ' '.join(a[2:]) or 'JACK'), ensure_ascii=False))
    elif a and a[0] == 'medien':
        print(json.dumps(medien(a[1]), ensure_ascii=False))
    else:
        print(__doc__)
