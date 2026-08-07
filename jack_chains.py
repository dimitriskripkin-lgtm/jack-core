#!/usr/bin/env python3
import os, sys, json, sqlite3, datetime, time
sys.path.insert(0, os.path.expanduser('~/jack'))
import jack_intent

H = os.path.expanduser('~/jack')
CHAIN_DB = os.path.join(H, 'jack_chains.db')

KETTEN = {
    'xiaomi_reparieren': {'beschreibung': 'Xiaomi pruefen, WiFi neustarten wenn noetig', 'level': 3,
        'schritte': [{'aktion': 'ssh_check', 'wenn': None}, {'aktion': 'xiaomi_wake', 'wenn': 'enthaelt:nicht erreichbar'}, {'aktion': 'ssh_check', 'wenn': None}]},
    'system_vollcheck': {'beschreibung': 'Dienste, RAM, Temp, Akku, Xiaomi, Fehler', 'level': 2,
        'schritte': [{'aktion': 'dienste_check', 'wenn': None}, {'aktion': 'ram_check', 'wenn': None}, {'aktion': 'temp_check', 'wenn': None}, {'aktion': 'akku_check', 'wenn': None}, {'aktion': 'ssh_check', 'wenn': None}, {'aktion': 'fehler_check', 'wenn': None}]},
    'notfall_recovery': {'beschreibung': 'Tote Dienste neustarten dann Vollcheck', 'level': 3,
        'schritte': [{'aktion': 'dienst_neustart', 'wenn': None}, {'aktion': 'dienste_check', 'wenn': None}]},
    'morgen_briefing': {'beschreibung': 'Morgen-Status: Dienste, Akku, Temp', 'level': 2,
        'schritte': [{'aktion': 'dienste_check', 'wenn': None}, {'aktion': 'akku_check', 'wenn': None}, {'aktion': 'temp_check', 'wenn': None}]},
}

def _init_db():
    con = sqlite3.connect(CHAIN_DB)
    con.execute('CREATE TABLE IF NOT EXISTS laeufe (id INTEGER PRIMARY KEY AUTOINCREMENT, kette TEXT, schritte_ok INTEGER, ergebnis TEXT, dauer REAL, ts TEXT)')
    con.commit(); con.close()

def _bedingung(wenn, letztes):
    if wenn is None: return True
    if letztes is None: return False
    e = str(letztes).lower()
    if wenn.startswith('enthaelt:'): return wenn[9:] in e
    if wenn == 'fehler': return 'fehler' in e or 'nicht erreichbar' in e
    return True

def run(name):
    if name not in KETTEN: return {'ok': False, 'text': 'Unbekannte Kette: ' + name}
    k = KETTEN[name]
    if jack_intent.get_level() < k['level']:
        return {'ok': False, 'text': 'Level ' + str(k['level']) + ' noetig. /level ' + str(k['level'])}
    t0 = time.time()
    zeilen = ['Kette: ' + k['beschreibung'], '']
    letztes = None
    ok = 0
    for i, s in enumerate(k['schritte'], 1):
        if not _bedingung(s.get('wenn'), letztes): continue
        try:
            erg = jack_intent.execute({'intent': s['aktion'], 'methode': 'chain', 'confidence': 1.0, '_text': name})
            letztes = erg
            zeilen.append(str(i) + '. ' + str(erg).replace(chr(10), ' | ')[:150])
            ok += 1
        except Exception as e:
            zeilen.append(str(i) + '. FEHLER: ' + str(e)[:80])
            letztes = 'fehler'
    dauer = round(time.time() - t0, 1)
    zeilen.append('Dauer: ' + str(dauer) + 's')
    text = chr(10).join(zeilen)
    try:
        _init_db()
        con = sqlite3.connect(CHAIN_DB)
        con.execute('INSERT INTO laeufe (kette,schritte_ok,ergebnis,dauer,ts) VALUES (?,?,?,?,?)',
            (name, ok, text[:800], dauer, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        con.commit(); con.close()
    except Exception: pass
    return {'ok': True, 'text': text, 'schritte': ok, 'dauer': dauer}

def liste():
    lvl = jack_intent.get_level()
    out = ['Verfuegbare Ketten:', '']
    for n, k in KETTEN.items():
        mark = '' if lvl >= k['level'] else ' (Level ' + str(k['level']) + ' noetig)'
        out.append('/kette ' + n + mark)
        out.append('   ' + k['beschreibung'])
    return chr(10).join(out)

def historie(limit=5):
    try:
        _init_db()
        con = sqlite3.connect(CHAIN_DB)
        rows = con.execute('SELECT kette,schritte_ok,dauer,ts FROM laeufe ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        con.close()
        return [{'kette': r[0], 'schritte': r[1], 'dauer': r[2], 'ts': r[3]} for r in rows]
    except Exception: return []

if __name__ == '__main__':
    n = sys.argv[1] if len(sys.argv) > 1 else None
    print(liste() if not n else run(n)['text'])
