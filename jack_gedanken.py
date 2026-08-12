#!/usr/bin/env python3
"""Gedankenkette: warum JACK tut was er tut."""
import os, sqlite3, datetime
DB = os.path.expanduser('~/jack/jack_cognition.db')

def _init():
    c = sqlite3.connect(DB); c.execute('PRAGMA journal_mode=WAL')
    c.execute('''CREATE TABLE IF NOT EXISTS gedanken(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ausloeser TEXT, hypothese TEXT,
        alternativen TEXT, entscheidung TEXT, konfidenz REAL,
        ergebnis TEXT, rueckblick TEXT, quelle TEXT, ts TEXT)''')
    c.commit(); c.close()

def denke(ausloeser, hypothese, entscheidung, konfidenz=0.5, alternativen='', quelle='intent'):
    _init()
    c = sqlite3.connect(DB)
    try:
        cur = c.execute('INSERT INTO gedanken(ausloeser,hypothese,alternativen,entscheidung,konfidenz,quelle,ts) VALUES(?,?,?,?,?,?,?)',
            (str(ausloeser)[:200], str(hypothese)[:300], str(alternativen)[:200],
             str(entscheidung)[:200], float(konfidenz), quelle,
             datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        c.commit()
        return cur.lastrowid
    except Exception:
        return None
    finally:
        c.close()

def ergebnis(gid, text, war_richtig=None):
    if not gid: return
    _init()
    c = sqlite3.connect(DB)
    try:
        rb = '' if war_richtig is None else ('richtig' if war_richtig else 'falsch')
        c.execute('UPDATE gedanken SET ergebnis=?, rueckblick=? WHERE id=?', (str(text)[:300], rb, gid))
        c.commit()
    except Exception: pass
    finally: c.close()

def letzte(n=5):
    _init()
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    try:
        r = c.execute('SELECT * FROM gedanken ORDER BY id DESC LIMIT ?', (n,)).fetchall()
    finally: c.close()
    return [dict(x) for x in r]

def als_text(n=3):
    g = letzte(n)
    if not g: return 'Noch keine Gedanken protokolliert.'
    z = []
    for x in g:
        z.append(x['ts'][11:16] + ' | ' + (x['quelle'] or '?'))
        z.append('  Ausloeser: ' + (x['ausloeser'] or '?')[:90])
        z.append('  Gedacht: ' + (x['hypothese'] or '?')[:120])
        if x['alternativen']: z.append('  Alternativen: ' + x['alternativen'][:90])
        z.append('  Entschieden: ' + (x['entscheidung'] or '?')[:90] + ' (Sicherheit ' + str(round((x['konfidenz'] or 0)*100)) + '%)')
        if x['ergebnis']: z.append('  Ergebnis: ' + x['ergebnis'][:100])
        z.append('')
    return chr(10).join(z)

def statistik():
    _init()
    c = sqlite3.connect(DB)
    try:
        n = c.execute('SELECT COUNT(*) FROM gedanken').fetchone()[0]
        richtig = c.execute("SELECT COUNT(*) FROM gedanken WHERE rueckblick='richtig'").fetchone()[0]
        falsch = c.execute("SELECT COUNT(*) FROM gedanken WHERE rueckblick='falsch'").fetchone()[0]
        avg = c.execute('SELECT AVG(konfidenz) FROM gedanken').fetchone()[0] or 0
    finally: c.close()
    return ('Gedanken gesamt: ' + str(n) + chr(10) + 'Richtig: ' + str(richtig) +
            ' | Falsch: ' + str(falsch) + chr(10) + 'Durchschnittliche Sicherheit: ' + str(round(avg*100)) + '%')

if __name__ == '__main__':
    import sys
    print(statistik() if len(sys.argv)>1 and sys.argv[1]=='stat' else als_text(5))
