#!/usr/bin/env python3
"""JACK_TUNE_TASKER (Kap 295): Tasker auf dem Xiaomi ausloesen und Quittung abholen.
Hin:  am broadcast -a net.dinglisch.android.tasker.ACTION_TASK -e task_name <NAME> (root, ueber jack_xiaomi).
Rueck: Tasker schreibt /sdcard/Tasker/JACK/outbox/<praefix>_<ms>.json, JACK liest und loescht.
Nur Tasks aus ERLAUBT. Ergebnis "result":"DONE" ist Taskers Aussage, kein Beweis der Wirkung.
Aufruf: python3 jack_tasker.py JACK_TEST_DATEI
"""
import json, re, sys, time

OUTBOX = '/sdcard/Tasker/JACK/outbox'
ERLAUBT = {'JACK_TEST_DATEI': 'datei', 'JACK_TEST_VIBRA': 'vibra'}
MODULE_VERSION = '2026-10-21'


def _sh(cmd, timeout=15):
    import jack_xiaomi
    r = jack_xiaomi.run_shell(cmd, as_root=True, timeout=timeout)
    return bool(r.get('success')), (r.get('stdout') or '')


def run_task(name, warte=8.0):
    if name not in ERLAUBT:
        return {'ok': False, 'grund': 'Task nicht erlaubt: %s' % name}
    praefix = ERLAUBT[name]
    start_ms = int(time.time() * 1000) - 2000  # Uhrversatz Honor/Xiaomi abfedern
    ok, out = _sh('am broadcast -a net.dinglisch.android.tasker.ACTION_TASK -e task_name %s >/dev/null 2>&1; echo SENT' % name)
    if not ok or 'SENT' not in out:
        return {'ok': False, 'grund': 'Broadcast fehlgeschlagen'}
    ende = time.time() + warte
    while time.time() < ende:
        time.sleep(1.0)
        ok, out = _sh('ls %s 2>/dev/null' % OUTBOX, 8)
        treffer = sorted(f for f in out.split() if re.fullmatch(praefix + r'_(\d+)\.json', f)
                         and int(re.search(r'_(\d+)\.', f).group(1)) >= start_ms)
        if treffer:
            f = treffer[-1]
            ok, inhalt = _sh('cat %s/%s && rm -f %s/%s' % (OUTBOX, f, OUTBOX, f), 8)
            try:
                q = json.loads(inhalt)
            except ValueError:
                return {'ok': False, 'grund': 'Quittung unlesbar', 'datei': f}
            return {'ok': q.get('result') == 'DONE', 'quittung': q, 'sekunden': round(time.time() - (ende - warte), 1)}
    return {'ok': False, 'grund': 'keine Quittung in %.0f s' % warte}


def aufraeumen(alter_s=3600):
    """Alte Quittungen loeschen (z. B. aus Tests)."""
    grenze = int((time.time() - alter_s) * 1000)
    ok, out = _sh('ls %s 2>/dev/null' % OUTBOX, 8)
    alt = [f for f in out.split() if re.search(r'_(\d+)\.json$', f) and int(re.search(r'_(\d+)\.', f).group(1)) < grenze]
    if alt:
        _sh('cd %s && rm -f %s' % (OUTBOX, ' '.join(alt)), 8)
    return len(alt)


if __name__ == '__main__':
    print(json.dumps(run_task(sys.argv[1] if len(sys.argv) > 1 else 'JACK_TEST_DATEI'), ensure_ascii=False))
