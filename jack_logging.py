#!/usr/bin/env python3
"""Zentrales strukturiertes Logging fuer JACK.
Ersetzt bare excepts. Fehler werden sichtbar statt verschluckt."""
import os, logging, sys

LOG_DIR = os.path.expanduser('~/jack/logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'jack.log')

_fmt = logging.Formatter(
    '%(asctime)s | %(levelname)-7s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

_fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
_fh.setFormatter(_fmt)
_fh.setLevel(logging.DEBUG)

_root = logging.getLogger('jack')
if not _root.handlers:
    _root.addHandler(_fh)
    _root.setLevel(logging.DEBUG)

def get(name):
    """Holt einen Logger fuer ein Modul: log = jack_logging.get('cortex')"""
    return logging.getLogger('jack.' + name)

def fehler(modul, kontext, exc):
    """Kurzform: statt except: pass -> jack_logging.fehler('cortex','ssh check',e)"""
    get(modul).warning('%s: %s: %s', kontext, type(exc).__name__, str(exc)[:200])

def letzte(n=30, nur_fehler=False):
    """Letzte Logzeilen lesen."""
    try:
        with open(LOG_FILE, encoding='utf-8') as f:
            zeilen = f.readlines()
        if nur_fehler:
            zeilen = [z for z in zeilen if 'ERROR' in z or 'WARNING' in z]
        return ''.join(zeilen[-n:])
    except Exception:
        return '(kein Log)'

def statistik():
    """Zaehlt Fehler nach Modul."""
    try:
        from collections import Counter
        c = Counter()
        with open(LOG_FILE, encoding='utf-8') as f:
            for z in f:
                if 'WARNING' in z or 'ERROR' in z:
                    teile = z.split('|')
                    if len(teile) > 2:
                        c[teile[2].strip()] += 1
        if not c:
            return 'Keine Fehler im Log'
        return chr(10).join(m + ': ' + str(n) for m, n in c.most_common(10))
    except Exception as e:
        return 'Statistik-Fehler: ' + str(e)[:100]

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'stat':
        print(statistik())
    else:
        print(letzte(40))
