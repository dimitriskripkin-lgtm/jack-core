#!/usr/bin/env python3
"""Episodisches Gedaechtnis: Momente statt Datenpunkte."""
import os, sqlite3, datetime, json
DB = os.path.expanduser('~/jack/jack_memory.db')
LUECKE = 1800

def _init():
    c = sqlite3.connect(DB); c.execute('PRAGMA journal_mode=WAL')
    c.execute('''CREATE TABLE IF NOT EXISTS episoden(
        id INTEGER PRIMARY KEY AUTOINCREMENT, titel TEXT, thema TEXT,
        stimmung TEXT, geloest INTEGER DEFAULT 0, wichtig INTEGER DEFAULT 0,
        start_ts TEXT, end_ts TEXT, zusammenfassung TEXT,
        n_eintraege INTEGER, erstellt TEXT, zuletzt_erwaehnt TEXT)''')
    c.commit(); c.close()

def _roh_gruppen():
    _init()
    c = sqlite3.connect(DB)
    try:
        last = c.execute('SELECT MAX(end_ts) FROM episoden').fetchone()[0] or '2000-01-01'
        rows = c.execute('SELECT cmd,result,timestamp FROM memory WHERE timestamp > ? ORDER BY timestamp',(last,)).fetchall()
    finally:
        c.close()
    gruppen, akt, prev = [], [], None
    for cmd, res, ts in rows:
        try: t = datetime.datetime.strptime(ts[:19], '%Y-%m-%d %H:%M:%S')
        except Exception: continue
        if prev and (t - prev).total_seconds() > LUECKE and akt:
            gruppen.append(akt); akt = []
        akt.append((cmd, res, ts)); prev = t
    if len(akt) >= 2: gruppen.append(akt)
    return [g for g in gruppen if len(g) >= 2]

def _bewerte(gruppe):
    import jack_gemini_bridge as gb
    txt = chr(10).join('Dima: '+ (c or '')[:150] + ' | JACK: ' + (r or '')[:150] for c,r,_ in gruppe[:12])
    p = ('Fasse diese Interaktion als Episode zusammen. Antworte NUR mit JSON:'+chr(10)
         +'{"titel":"kurzer titel max 8 woerter","thema":"xiaomi|voice|memory|code|system|persoenlich|sonstiges",'
         +'"stimmung":"frustriert|neutral|produktiv|durchbruch","geloest":true/false,"wichtig":true/false,'
         +'"zusammenfassung":"2 saetze was passiert ist"}'+chr(10)+chr(10)+txt)
    try:
        a = gb.ask_gemini(p) or ''
        import re
        m = re.search(r'\{.*\}', a, re.DOTALL)
        return json.loads(m.group(0)) if m else None
    except Exception:
        return None

def bilde(max_neu=3):
    _init(); neu = 0
    for g in _roh_gruppen()[:max_neu]:
        b = _bewerte(g)
        if not b: continue
        c = sqlite3.connect(DB)
        try:
            c.execute('INSERT INTO episoden(titel,thema,stimmung,geloest,wichtig,start_ts,end_ts,zusammenfassung,n_eintraege,erstellt) VALUES(?,?,?,?,?,?,?,?,?,?)',
                (b.get('titel','?')[:80], b.get('thema','sonstiges'), b.get('stimmung','neutral'),
                 1 if b.get('geloest') else 0, 1 if b.get('wichtig') else 0,
                 g[0][2], g[-1][2], b.get('zusammenfassung','')[:400], len(g),
                 datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            c.commit()
        finally:
            c.close()
        neu += 1
    return neu

def offene(tage_min=2):
    _init()
    grenze = (datetime.datetime.now()-datetime.timedelta(days=tage_min)).strftime('%Y-%m-%d %H:%M:%S')
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    try:
        r = c.execute('SELECT * FROM episoden WHERE geloest=0 AND end_ts < ? ORDER BY wichtig DESC, end_ts DESC LIMIT 5',(grenze,)).fetchall()
    finally:
        c.close()
    return [dict(x) for x in r]

def zu_thema(thema, limit=3):
    _init()
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    try:
        r = c.execute('SELECT * FROM episoden WHERE thema=? ORDER BY end_ts DESC LIMIT ?',(thema,limit)).fetchall()
    finally:
        c.close()
    return [dict(x) for x in r]

def letzte(n=5):
    _init()
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row
    try:
        r = c.execute('SELECT * FROM episoden ORDER BY end_ts DESC LIMIT ?',(n,)).fetchall()
    finally:
        c.close()
    return [dict(x) for x in r]

def als_text(n=4):
    e = letzte(n)
    if not e: return ''
    z = ['Was zuletzt passiert ist (deine Episoden):']
    for x in e:
        st = {'frustriert':'zaeh','durchbruch':'grosser Schritt','produktiv':'lief gut','neutral':''}.get(x['stimmung'],'')
        mark = ' [OFFEN]' if not x['geloest'] else ''
        z.append('- ' + x['end_ts'][:10] + ' ' + x['titel'] + (' (' + st + ')' if st else '') + mark)
        if x['wichtig'] and x['zusammenfassung']:
            z.append('  ' + x['zusammenfassung'][:150])
    return chr(10).join(z)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'bilde':
        print('Neue Episoden: ' + str(bilde()))
    else:
        print(als_text(6) or 'Noch keine Episoden')
