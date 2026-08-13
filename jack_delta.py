#!/usr/bin/env python3
"""Nur Veraenderungen in den Kontext - nicht bei jeder Nachricht denselben Status."""
import os, json, datetime
H = os.path.expanduser('~/jack')
SNAP = os.path.join(H, '.delta_snapshot')
ERWAEHNT = os.path.join(H, '.delta_erwaehnt')

def _lade(pfad, default):
    try: return json.load(open(pfad))
    except Exception: return default

def _speichere(pfad, obj):
    try: json.dump(obj, open(pfad,'w'))
    except Exception: pass

def _messe():
    d = {}
    try:
        d['ram'] = int([l for l in open('/proc/meminfo') if 'MemAvailable' in l][0].split()[1])//1024
    except Exception: pass
    try:
        mx = 0
        for z in os.listdir('/sys/class/thermal'):
            try:
                tp = open('/sys/class/thermal/'+z+'/type').read().strip()
                if any(x in tp for x in ('trip','lvl','vbat')): continue
                rv = int(open('/sys/class/thermal/'+z+'/temp').read())
                if rv < 0: continue
                g = rv/1000 if rv > 1000 else float(rv)
                if g > mx: mx = g
            except Exception: pass
        d['temp'] = round(mx,1)
    except Exception: pass
    try:
        import sqlite3
        c = sqlite3.connect(os.path.join(H,'jack_errors.db'))
        d['fehler'] = c.execute('SELECT COUNT(*) FROM errors WHERE resolved=0').fetchone()[0]
        c.close()
    except Exception: pass
    try:
        import subprocess
        b = json.loads(subprocess.run(['termux-battery-status'],capture_output=True,text=True,timeout=8).stdout)
        d['akku'] = b.get('percentage'); d['laden'] = b.get('status')
    except Exception: pass
    try:
        import subprocess as sp
        P = os.environ.get('PREFIX','/data/data/com.termux/files/usr')
        tot = []
        for s in ('jack_cortex','jack_telegram','jack_waechter','ollama'):
            r = sp.run(['sv','status',P+'/var/service/'+s],capture_output=True,text=True,timeout=3)
            if 'run:' not in r.stdout: tot.append(s)
        d['tote_dienste'] = tot
    except Exception: pass
    return d

def delta_text():
    """Nur was sich geaendert hat. Leerer String wenn nichts Neues."""
    alt = _lade(SNAP, {})
    neu = _messe()
    _speichere(SNAP, neu)
    if not alt:
        return ''
    z = []
    if 'ram' in alt and 'ram' in neu and abs(neu['ram']-alt['ram']) > 700:
        richtung = 'gestiegen' if neu['ram'] > alt['ram'] else 'gefallen'
        z.append('RAM ' + richtung + ' auf ' + str(neu['ram']) + 'MB (vorher ' + str(alt['ram']) + 'MB)')
    if 'temp' in alt and 'temp' in neu and abs(neu['temp']-alt['temp']) > 8:
        z.append('Temperatur jetzt ' + str(neu['temp']) + 'C (vorher ' + str(alt['temp']) + 'C)')
    if 'fehler' in alt and 'fehler' in neu and neu['fehler'] != alt['fehler']:
        z.append('Offene Fehler: ' + str(alt['fehler']) + ' -> ' + str(neu['fehler']))
    if 'akku' in alt and 'akku' in neu:
        if alt.get('laden') != neu.get('laden'):
            z.append('Akku-Status: ' + str(neu.get('laden')))
        elif abs((neu['akku'] or 0)-(alt['akku'] or 0)) > 20:
            z.append('Akku bei ' + str(neu['akku']) + '%')
    at, nt = set(alt.get('tote_dienste',[])), set(neu.get('tote_dienste',[]))
    if nt - at:
        z.append('Dienst ausgefallen: ' + ', '.join(nt-at))
    if at - nt:
        z.append('Dienst wieder da: ' + ', '.join(at-nt))
    if not z:
        return ''
    return 'SEIT DER LETZTEN NACHRICHT GEAENDERT:' + chr(10) + chr(10).join('- '+x for x in z)

def basis_kurz():
    """Minimaler Zustand - nur auf Nachfrage relevant, nicht als Dauerbericht."""
    n = _lade(SNAP, {}) or _messe()
    teile = []
    if 'ram' in n: teile.append('RAM ' + str(n['ram']) + 'MB frei')
    if 'temp' in n: teile.append(str(n['temp']) + 'C')
    if 'akku' in n: teile.append('Akku ' + str(n['akku']) + '%')
    if n.get('tote_dienste'): teile.append('TOT: ' + ','.join(n['tote_dienste']))
    return ' | '.join(teile)

def merke_erwaehnt(themen):
    e = _lade(ERWAEHNT, [])
    e = (e + list(themen))[-12:]
    _speichere(ERWAEHNT, e)

def gesperrt():
    """Themen die JACK zuletzt schon erwaehnt hat."""
    from collections import Counter
    e = _lade(ERWAEHNT, [])
    c = Counter(e[-6:])
    return [k for k,v in c.items() if v >= 2]

def themen_aus_text(txt):
    t = (txt or '').lower()
    gefunden = []
    for wort, thema in (('ram','ram'),('speicher','ram'),('temperatur','temp'),('grad','temp'),
                        ('warm','temp'),('heiss','temp'),('xiaomi','xiaomi'),('akku','akku'),
                        ('dienst','dienste'),('fehler','fehler')):
        if wort in t and thema not in gefunden:
            gefunden.append(thema)
    return gefunden

def sperr_hinweis():
    g = gesperrt()
    if not g:
        return ''
    return ('NICHT NOCHMAL ANSPRECHEN (hast du zuletzt schon gesagt): ' + ', '.join(g) +
            '. Nur erwaehnen wenn Dima ausdruecklich danach fragt oder sich etwas geaendert hat.')

if __name__ == '__main__':
    print('DELTA:'); print(delta_text() or '(nichts geaendert)')
    print(); print('BASIS: ' + basis_kurz())
    print('GESPERRT: ' + str(gesperrt()))
