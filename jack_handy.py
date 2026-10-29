#!/usr/bin/env python3
"""JACK_TUNE_HANDY (Kap 298) + JACK_TUNE_HANDYHONOR (Kap 301, 22.10.2026): Timer und Medien, Intent/Shell zuerst (Kap 291).
geraet='honor' (Standard: Spotify im LKW laeuft auf dem Honor) ueber Shizuku/rish mit Datei-Ausgabe
(jack_lagebild._rish, weil rish-stdout Daten verliert; rish laeuft in Diensten/Missionen, nicht in Cron).
geraet='xiaomi' ueber jack_xiaomi.run_shell (root, Schutzpfad).
timer(sekunden, text) : SET_TIMER-Intent ohne UI, Beleg = neue Uhr-Benachrichtigung.
medien(aktion)        : cmd media_session dispatch, Beleg = PlaybackState der aktiven Sitzung. 'status' = nur lesen.
telegram(text)        : /timer 10 [Text] | /timer 90s | /timer 1h | /musik pause|play|weiter|zurueck|status  (+ 'xiaomi')
CLI: python3 jack_handy.py timer 300 Nudeln [--xiaomi] | python3 jack_handy.py medien status [--xiaomi]
"""
import json, re, sys, time

MODULE_VERSION = '2026-10-22'
MEDIEN = {'play': 'play', 'pause': 'pause', 'umschalten': 'play-pause', 'weiter': 'next', 'zurueck': 'previous'}
ALIAS = {'stop': 'pause', 'stopp': 'pause', 'aus': 'pause', 'an': 'play', 'los': 'play', 'start': 'play',
         'weiterspielen': 'play', 'next': 'weiter', 'naechster': 'weiter', 'nächster': 'weiter', 'skip': 'weiter',
         'vor': 'weiter', 'zurück': 'zurueck', 'back': 'zurueck', 'toggle': 'umschalten'}
NAMEN = {'1': 'gestoppt', '2': 'pausiert', '3': 'spielt'}
UHR = {'honor': 'deskclock', 'xiaomi': 'com.android.deskclock'}


def _sh(cmd, timeout=15, geraet='honor'):
    if geraet == 'honor':
        import jack_lagebild
        rc, out = jack_lagebild._rish(cmd, timeout)
        return rc == 0, (out or '')
    import jack_xiaomi
    r = jack_xiaomi.run_shell(cmd, as_root=True, timeout=timeout)
    return bool(r.get('success')), (r.get('stdout') or '')


def _entsperren():
    try:
        import jack_xiaomi_unlock
        return str(jack_xiaomi_unlock.ensure_unlocked())
    except Exception as e:
        return 'UNLOCK_FEHLER ' + type(e).__name__


def _uhr_titel(geraet):
    _, out = _sh('dumpsys notification --noredact 2>/dev/null | grep -A40 "pkg=[a-z.]*%s" '
                 '| grep -o "android.title=String ([^)]*)"' % UHR[geraet], 10, geraet)
    return re.findall(r'\(([^)]*)\)', out)


JACK = '/data/data/com.termux/files/home/jack'
TIMERLOG = JACK + '/logs/handy_timer.jsonl'


def klingeln(text='JACK'):
    """JACK_TUNE_JACKTIMER (Kap 301): Ablauf eines JACK-Timers. Telegram (wichtig, nie gepuffert), Vibration, Ansage."""
    import subprocess
    text = re.sub(r'[^\w äöüÄÖÜß.-]', '', str(text))[:30] or 'JACK'
    fehler = []
    try:
        import jack_tg_send
        jack_tg_send.send('⏰ Timer abgelaufen: %s' % text, wichtig=True, quelle='handy')
    except Exception as e:
        fehler.append('telegram ' + type(e).__name__)
    for cmd in (['termux-vibrate', '-f', '-d', '1500'], ['termux-tts-speak', 'Timer %s ist abgelaufen' % text]):
        try:
            subprocess.run(cmd, timeout=30, capture_output=True)
        except Exception as e:
            fehler.append(cmd[0] + ' ' + type(e).__name__)
    _timerlog({'ev': 'klingelt', 'text': text, 'fehler': fehler})
    return {'ok': not fehler, 'fehler': fehler}


def _timerlog(d):
    try:
        d = dict(d, ts=time.strftime('%Y-%m-%d %H:%M:%S'))
        with open(TIMERLOG, 'a') as fh:
            fh.write(json.dumps(d, ensure_ascii=False) + '\n')
    except OSError:
        pass


def _jack_timer(sekunden, text):
    """Honor-Uhr ignoriert SET_TIMER-Laenge (gemessen 22.10.: oeffnet Timer-Seite mit 00:00:00).
    Deshalb zaehlt JACK selbst: eigener Prozess (neue Sitzung, ueberlebt Neustart von jack_telegram)."""
    import subprocess
    p = subprocess.Popen(['sh', '-c', 'sleep %d; exec python3 %s/jack_handy.py klingeln "$0"' % (sekunden, JACK), text],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True, cwd=JACK)
    um = time.strftime('%H:%M', time.localtime(time.time() + sekunden))
    _timerlog({'ev': 'gestellt', 'text': text, 'sek': sekunden, 'um': um, 'pid': p.pid})
    return {'ok': p.poll() is None, 'beleg': ['JACK-Timer pid %d, klingelt um %s' % (p.pid, um)],
            'geraet': 'honor', 'art': 'jack'}


def timer(sekunden, text='JACK', geraet='honor'):
    if type(sekunden) is not int or not 5 <= sekunden <= 6 * 3600:
        return {'ok': False, 'grund': 'Sekunden 5..21600'}
    text = re.sub(r'[^\w äöüÄÖÜß.-]', '', str(text))[:30] or 'JACK'
    if geraet == 'honor':
        return _jack_timer(sekunden, text)
    u = _entsperren() if geraet == 'xiaomi' else '-'
    vorher = _uhr_titel(geraet)
    ok, _ = _sh('am start -a android.intent.action.SET_TIMER --ei android.intent.extra.alarm.LENGTH %d '
                '--es android.intent.extra.alarm.MESSAGE "%s" --ez android.intent.extra.alarm.SKIP_UI true '
                '>/dev/null 2>&1; echo OK' % (sekunden, text), 15, geraet)
    time.sleep(2)
    nachher = _uhr_titel(geraet)
    neu = [b for b in nachher if b not in vorher]
    if not neu and len(nachher) > len(vorher):
        neu = nachher[-1:]
    r = {'ok': ok and bool(neu), 'beleg': (neu or nachher)[:2], 'geraet': geraet, 'entsperrt': u}
    if not r['ok']:
        r['grund'] = 'keine neue Uhr-Benachrichtigung' + (' (es lief schon ein Timer)' if vorher else '')
    return r


def _lage(geraet):
    """(App, Zustand, Tasten-App) in EINEM Aufruf. Honor schreibt state=PAUSED(2), Xiaomi state=2.
    Tasten-App = 'Media button session is <pkg>/...': dorthin geht dispatch (gemessen 22.10.: Claude-Vorlesen
    schnappt sich die Taste, dann erreicht /musik pause Spotify nicht)."""
    _, out = _sh('dumpsys media_session 2>/dev/null | grep -m40 -E "^ +package=|state=PlaybackState|Media button session is"',
                 10, geraet)
    cur, app, z = None, None, None
    m = re.search(r'Media button session is ([\w.]+)', out)
    taste = m.group(1) if m else None
    paare = []
    for zeile in out.splitlines():
        m = re.search(r'package=(\S+)', zeile)
        if m:
            cur = m.group(1)
            continue
        m = re.search(r'state=PlaybackState \{state=(?:[A-Z_]+\()?(\d+)', zeile)
        if m and cur and not cur.startswith(('com.android.server', 'com.anthropic.claude')):
            paare.append((cur, m.group(1)))  # JACK_TUNE_MUSIKAPP: Claude-Vorlesen ist kein Musikplayer
    for bevorzugt in ('com.spotify.music', 'com.google.android.apps.youtube.music', 'com.google.android.youtube'):
        for a, s in paare:
            if a == bevorzugt:
                return a, s, taste
    if paare:
        app, z = paare[0]
    return app, z, taste


def _zustand(geraet):
    app, z, _ = _lage(geraet)
    return app, z


def medien(aktion, geraet='honor'):
    aktion = ALIAS.get(aktion, aktion)
    if aktion == 'status':
        app, z = _zustand(geraet)
        if not app:
            return {'ok': False, 'grund': 'keine aktive Medien-App (z. B. Spotify erst starten)', 'geraet': geraet}
        return {'ok': True, 'app': app, 'zustand': NAMEN.get(z, 'unbekannt(%s)' % z), 'geraet': geraet}
    if aktion not in MEDIEN:
        return {'ok': False, 'grund': 'erlaubt: ' + ', '.join(list(MEDIEN) + ['status'])}
    app0, z0, taste = _lage(geraet)
    if geraet == 'honor' and app0 and taste and taste != app0 and 'youtube' in taste:
        # JACK_TUNE_MUSIKTASTE (29.10.2026, Kap 301, ersetzt MUSIKVORNE): YouTube (Morphe) haelt die Medientaste
        # auch gestoppt. Gemessen: force-stop YouTube -> Taste frei -> dispatch pause/play erreicht Spotify.
        # Nie, wenn YouTube gerade spielt.
        _, yt = _sh('dumpsys media_session 2>/dev/null | grep -A20 "package=%s" | grep -m1 "state=PlaybackState"' % taste,
                    10, geraet)
        if not re.search(r'state=(?:PLAYING\(3\)|3(?!\d))', yt or ''):
            _sh('am force-stop %s' % taste, 10, geraet)
            time.sleep(0.8)
    _sh('cmd media_session dispatch %s >/dev/null 2>&1' % MEDIEN[aktion], 10, geraet)
    erwartet = {'play': '3', 'pause': '2'}.get(aktion)
    app, z = None, None
    for warte in (0.3, 0.5, 0.7):  # JACK_TUNE_HANDYFAST: kurz pollen statt fest 1,2 s warten
        time.sleep(warte)
        app, z, _ = _lage(geraet)
        if erwartet is None or z == erwartet:
            break
    if not app:
        return {'ok': False, 'grund': 'keine aktive Medien-App (z. B. Spotify erst starten)', 'geraet': geraet}
    if erwartet:
        ok = z == erwartet
    elif aktion == 'umschalten':
        ok = z is not None and z != z0
    else:
        ok = z == '3'  # weiter/zurueck: ehrlich nur, wenn danach etwas spielt
    r = {'ok': ok, 'app': app, 'zustand': NAMEN.get(z, 'unbekannt(%s)' % z), 'geraet': geraet, 'taste': taste}
    if not ok and taste and taste != app:
        r['grund'] = 'Medientaste lag bei %s, nicht bei %s' % (taste, app)
    return r


def _dauer(s):
    if s % 3600 == 0:
        return '%d h' % (s // 3600)
    if s % 60 == 0:
        return '%d Min' % (s // 60)
    return '%d s' % s


def parse_timer(rest):
    """'10' -> 600, '90s' -> 90, '1h Pause' -> 3600. Ohne Einheit = Minuten. Gibt (sek, text) oder None."""
    m = re.match(r'(\d+(?:[.,]\d+)?)\s*(sekunden|sek|s|minuten|min|m|stunden|std|h)?(?![a-zäöüß])\s*(.*)$',
                 rest.strip(), re.I)
    if not m:
        return None
    n = float(m.group(1).replace(',', '.'))
    u = (m.group(2) or 'm').lower()
    f = 1 if u in ('s', 'sek', 'sekunden') else 3600 if u in ('h', 'std', 'stunden') else 60
    return int(round(n * f)), (m.group(3) or '').strip()


def frei(text):
    """JACK_TUNE_MUSIKWORTE (29.10.2026, Kap 301): Freitext -> '/musik play|pause|weiter|zurueck' oder None."""
    t = str(text or '').lower()
    for a, b in (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss')):
        t = t.replace(a, b)
    t = ' '.join(re.findall(r'[a-z0-9]+', t))
    geraet = ' xiaomi' if re.search(r'\bxiaomi\b', t) else ''
    t = re.sub(r'\s*\b(?:auf |am )?(?:dem )?(?:honor|xiaomi|handy)\b', '', t).strip()
    t = re.sub(r'^(?:jack )?(?:bitte )?(?:(?:mach|mache|spring|springe|geh|gehe|schalt|schalte|spiel|spiele) )?(?:mal )?(?:die )?', '', t)
    t = re.sub(r'(?: bitte| mal| jetzt)+$', '', t).strip()
    if not t or len(t.split()) > 6:
        return None
    m = r'(?:spotify|musik)'
    n = r'(?:lied|song|titel|track)'
    regeln = (
        ('weiter', (r'(?:%s )?(?:zum |zu dem )?(?:das )?naechste[nrs]? %s' % (m, n),
                    r'(?:%s )?(?:ein(?:en)? )?%s (?:weiter|vor|nach vorne|vorwaerts|ueberspringen)' % (m, n),
                    r'%s (?:vor|nach vorne|vorwaerts|skip|next|naechster|naechstes|ueberspringen)' % m,
                    r'(?:skip|next)')),
        ('zurueck', (r'(?:%s )?(?:zum |zu dem )?(?:das )?(?:vorherige[nrs]?|letzte[nrs]?) %s' % (m, n),
                     r'(?:%s )?(?:ein(?:en)? )?%s (?:zurueck|davor|nochmal)' % (m, n),
                     r'%s (?:zurueck|back|vorheriges|vorheriger)' % m)),
        ('pause', (r'%s (?:pause|pausieren|aus|ausmachen|stop|stopp|anhalten)' % m,)),
        ('play', (r'%s (?:play|an|anmachen|los|start|starten|abspielen|weiter|weiterspielen|fortsetzen)' % m,)),
    )
    for aktion, muster in regeln:
        if any(re.fullmatch(p, t) for p in muster):
            return '/musik ' + aktion + geraet
    return None


def telegram(text):
    t = str(text).strip()
    geraet = 'xiaomi' if re.search(r'(?i)\bxiaomi\b', t) else 'honor'
    t = re.sub(r'(?i)\s*\bxiaomi\b', '', t).strip()
    low = t.lower()
    name = geraet.capitalize()
    if low.startswith('/timer'):
        p = parse_timer(t[6:])
        if not p:
            return 'Syntax: /timer 10 [Text] (Minuten) | /timer 90s | /timer 1h | am Ende "xiaomi" fuer das Xiaomi'
        sek, txt = p
        r = timer(sek, txt or 'JACK', geraet)
        if r.get('ok'):
            return 'Timer %s auf dem %s gesetzt. Beleg: %s' % (_dauer(sek), name, ', '.join(r.get('beleg') or []))
        return 'Timer %s auf dem %s NICHT bestaetigt: %s' % (_dauer(sek), name, r.get('grund', '?'))
    if low.startswith('/musik'):
        a = (low[6:].strip().split() or ['status'])[0]
        r = medien(a, geraet)
        if r.get('ok'):
            return 'Musik %s auf dem %s: %s (%s).' % (a, name, r.get('zustand'), r.get('app'))
        if r.get('app'):
            return 'Musik %s auf dem %s nicht bestaetigt, Zustand jetzt: %s (%s).%s' % (
                a, name, r.get('zustand'), r.get('app'), (' ' + r['grund'] + '.') if r.get('grund') else '')
        return 'Musik %s auf dem %s: %s' % (a, name, r.get('grund', '?'))
    return None


if __name__ == '__main__':
    a = [x for x in sys.argv[1:] if x != '--xiaomi']
    g = 'xiaomi' if '--xiaomi' in sys.argv else 'honor'
    if a and a[0] == 'timer':
        print(json.dumps(timer(int(a[1]), ' '.join(a[2:]) or 'JACK', g), ensure_ascii=False))
    elif a and a[0] == 'medien':
        print(json.dumps(medien(a[1] if len(a) > 1 else 'status', g), ensure_ascii=False))
    elif a and a[0] == 'klingeln':
        print(json.dumps(klingeln(' '.join(a[1:]) or 'JACK'), ensure_ascii=False))
    elif a and a[0] == 'telegram':
        print(telegram(' '.join(a[1:])))
    else:
        print(__doc__)
