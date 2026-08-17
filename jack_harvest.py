#!/usr/bin/env python3
"""JACK Chat-Harvester: liest per Vision KI-Chat-Verlaeufe aus Chrome.
SICHERHEIT: NUR Screenshot + Swipe. NIEMALS Taps. Stop via ~/jack/.harvest_stop.
Daten -> jack_harvest.db (gitignored, NIE im Publisher)."""
import os, sys, json, time, sqlite3, hashlib, subprocess
sys.path.insert(0, os.path.expanduser('~/jack'))
import jack_vision

DB = os.path.expanduser('~/jack/jack_harvest.db')
STOP = os.path.expanduser('~/jack/.harvest_stop')

def _init():
    con = sqlite3.connect(DB, timeout=5)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("""CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        quelle TEXT, sprecher TEXT, text TEXT,
        hash TEXT UNIQUE, ts TEXT DEFAULT (datetime('now')))""")
    con.execute("""CREATE TABLE IF NOT EXISTS dima_fakten(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fakt TEXT UNIQUE, quelle TEXT, ts TEXT DEFAULT (datetime('now')))""")
    con.commit(); con.close()

def _chrome_im_fokus():
    try:
        r = subprocess.run("ssh -o ConnectTimeout=4 xiaomi-jack \"su -c 'dumpsys window' | grep mCurrentFocus\"",
                           shell=True, capture_output=True, text=True, timeout=10)
        return 'chrome' in r.stdout.lower()
    except Exception:
        return False

def _swipe(richtung='alt'):
    if richtung == 'alt':
        cmd = 'input swipe 540 700 540 1900 400'
    else:
        cmd = 'input swipe 540 1900 540 700 400'
    subprocess.run(f"ssh -o ConnectTimeout=4 xiaomi-jack \"su -c '{cmd}'\"",
                   shell=True, capture_output=True, timeout=10)

def _speichere(quelle, eintraege):
    con = sqlite3.connect(DB, timeout=5)
    neu = 0
    for e in eintraege:
        t = str(e.get('text', '')).strip()
        if len(t) < 3: continue
        h = hashlib.md5((quelle + '|' + t).encode()).hexdigest()
        try:
            con.execute("INSERT INTO chats(quelle,sprecher,text,hash) VALUES (?,?,?,?)",
                        (quelle, str(e.get('sprecher', '?'))[:10], t[:4000], h))
            neu += 1
        except sqlite3.IntegrityError:
            pass
    con.commit(); con.close()
    return neu

PROMPT = ("Du siehst einen Chat-Verlauf zwischen einem Menschen und einer KI. "
          "Extrahiere ALLEN sichtbaren Nachrichtentext wortgetreu. "
          "Antworte NUR mit einem JSON-Array, keine Backticks, kein Kommentar: "
          '[{"sprecher":"mensch","text":"..."},{"sprecher":"ki","text":"..."}] '
          "Ignoriere UI-Elemente wie Buttons, Uhrzeiten, Menues.")

def harvest(quelle='unbekannt', runden=20, richtung='alt', status_fn=None):
    _init()
    if os.path.exists(STOP): os.remove(STOP)
    if not _chrome_im_fokus():
        return {'ok': False, 'grund': 'Chrome nicht im Vordergrund auf dem Xiaomi. Erst Chat oeffnen.'}
    gesamt_neu = 0; letzter_hash = ''
    for r in range(1, runden + 1):
        if os.path.exists(STOP):
            return {'ok': True, 'runden': r-1, 'neu': gesamt_neu, 'grund': 'per Stop-Datei beendet'}
        if not _chrome_im_fokus():
            return {'ok': False, 'runden': r-1, 'neu': gesamt_neu, 'grund': 'Chrome verlassen - Abbruch'}
        try:
            b64 = jack_vision.get_screen_b64(max_px=1080, quality=80)
        except Exception as e:
            return {'ok': False, 'runden': r-1, 'neu': gesamt_neu, 'grund': 'Screenshot: ' + str(e)[:80]}
        h = hashlib.md5(b64[:5000].encode()).hexdigest()
        if h == letzter_hash:
            return {'ok': True, 'runden': r-1, 'neu': gesamt_neu, 'grund': 'Verlaufsende erreicht (Screen unveraendert)'}
        letzter_hash = h
        antwort = jack_vision.vision_ask(PROMPT, b64=b64)
        if antwort.startswith('[BUDGET]') or antwort.startswith('[FEHLER'):
            return {'ok': False, 'runden': r-1, 'neu': gesamt_neu, 'grund': antwort[:100]}
        try:
            clean = antwort.replace('```json', '').replace('```', '').strip()
            daten = json.loads(clean)
            neu = _speichere(quelle, daten if isinstance(daten, list) else [])
            gesamt_neu += neu
            if status_fn and r % 5 == 0:
                status_fn(f'Harvest {quelle}: Runde {r}/{runden}, {gesamt_neu} neue Eintraege')
        except Exception:
            pass
        _swipe(richtung)
        time.sleep(1.5)
    return {'ok': True, 'runden': runden, 'neu': gesamt_neu, 'grund': 'Runden-Limit erreicht'}

def status():
    _init()
    con = sqlite3.connect(DB, timeout=5)
    rows = con.execute("SELECT quelle, COUNT(*) FROM chats GROUP BY quelle").fetchall()
    fakten = con.execute("SELECT COUNT(*) FROM dima_fakten").fetchone()[0]
    con.close()
    z = ['Harvest-Bestand:'] + [f'  {q}: {n} Eintraege' for q, n in rows] + [f'Destillierte Fakten: {fakten}']
    return chr(10).join(z) if rows else 'Harvest-DB leer.'

if __name__ == '__main__':
    q = sys.argv[1] if len(sys.argv) > 1 else 'test'
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    print(json.dumps(harvest(q, n), ensure_ascii=False))
