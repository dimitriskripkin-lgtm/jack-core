#!/usr/bin/env python3
"""JACK Intent-Engine: erkennt Aktionswuensche in natuerlicher Sprache.
Hybrid: Keywords zuerst (instant), Gemini-Semantik als Fallback (praezise).
Lernt aus Historie welche Aktionen Dima wann will."""
import os, json, subprocess, sys, sqlite3, datetime, re
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
sys.path.insert(0, os.path.expanduser('~/jack'))

H = os.path.expanduser('~/jack')
LEVEL_FILE = os.path.join(H, '.autonomie_level')
INTENT_DB = os.path.join(H, 'jack_intent.db')

# ---------- Autonomie-Level ----------
LEVEL_NAMEN = {
    1: 'nur fragen (keine Aktion ohne Bestaetigung)',
    2: 'lesen erlaubt (Status, Sensoren, Xiaomi lesen)',
    3: 'schreiben erlaubt (Dienste neustarten, Xiaomi steuern)',
    4: 'vollautonom (handelt selbst, meldet danach)'
}

def get_level():
    try: return int(open(LEVEL_FILE).read().strip())
    except: return 1

def set_level(n):
    open(LEVEL_FILE, 'w').write(str(n))

# ---------- DB fuer Intent-Historie ----------
def _init_db():
    con = sqlite3.connect(INTENT_DB)
    con.execute('''CREATE TABLE IF NOT EXISTS intents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT, intent TEXT, methode TEXT,
        confidence REAL, ausgefuehrt INTEGER,
        ergebnis TEXT, ts TEXT, stunde INTEGER)''')
    con.commit(); con.close()

def _log_intent(text, intent, methode, conf, ausgefuehrt, ergebnis):
    try:
        _init_db()
        con = sqlite3.connect(INTENT_DB)
        now = datetime.datetime.now()
        con.execute('INSERT INTO intents (text,intent,methode,confidence,ausgefuehrt,ergebnis,ts,stunde) VALUES (?,?,?,?,?,?,?,?)',
            (text[:200], intent, methode, conf, 1 if ausgefuehrt else 0,
             str(ergebnis)[:300], now.strftime('%Y-%m-%d %H:%M:%S'), now.hour))
        con.commit(); con.close()
    except Exception as _le:
        _jlog and _jlog.fehler("intent", "unbenannt", _le)

def historie(limit=10):
    try:
        _init_db()
        con = sqlite3.connect(INTENT_DB)
        con.row_factory = sqlite3.Row
        rows = con.execute('SELECT * FROM intents ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []

def muster_analyse():
    """Findet heraus welche Intents zu welcher Tageszeit haeufig sind."""
    try:
        _init_db()
        con = sqlite3.connect(INTENT_DB)
        rows = con.execute('''SELECT intent, stunde, COUNT(*) as n FROM intents
            WHERE ausgefuehrt=1 GROUP BY intent, stunde HAVING n >= 3
            ORDER BY n DESC LIMIT 5''').fetchall()
        con.close()
        return [{'intent': r[0], 'stunde': r[1], 'anzahl': r[2]} for r in rows]
    except Exception:
        return []

# ---------- Aktions-Katalog ----------
AKTIONEN = {
    'ssh_check':        {'level': 2, 'text': 'Xiaomi SSH pruefen'},
    'akku_check':       {'level': 2, 'text': 'Akkustand pruefen'},
    'ram_check':        {'level': 2, 'text': 'RAM pruefen'},
    'temp_check':       {'level': 2, 'text': 'Temperatur pruefen'},
    'dienste_check':    {'level': 2, 'text': 'Alle Dienste pruefen'},
    'ollama_check':     {'level': 2, 'text': 'Ollama pruefen'},
    'fehler_check':     {'level': 2, 'text': 'Offene Fehler zeigen'},
    'standort_check':   {'level': 2, 'text': 'Standort abrufen'},
    'dienst_neustart':  {'level': 3, 'text': 'Toten Dienst neustarten'},
    'xiaomi_wake':      {'level': 3, 'text': 'Xiaomi WiFi neustarten'},
    'werkstatt_leeren': {'level': 3, 'text': 'Werkstatt aufraeumen'},
    'proaktiv_check':  {'level': 3, 'text': 'Proaktiver System + Xiaomi Check'},
}

KEYWORDS = {
    'ssh_check':      ['ssh', 'xiaomi', 'slave', 'zweites handy'],
    'akku_check':     ['akku', 'batterie', 'ladung', 'prozent'],
    'ram_check':      ['ram', 'speicher', 'arbeitsspeicher', 'memory'],
    'temp_check':     ['temperatur', 'heiss', 'heiß', 'warm', 'grad', 'thermal'],
    'dienste_check':  ['dienste', 'services', 'laeuft alles', 'läuft alles', 'systemcheck', 'system check', 'selftest'],
    'ollama_check':   ['ollama', 'lokales modell', 'llama'],
    'fehler_check':   ['fehler', 'errors', 'bugs', 'was ist kaputt'],
    'standort_check': ['standort', 'wo bin ich', 'position', 'gps'],
    'dienst_neustart':['neustart', 'restart', 'starte neu', 'reboot dienst'],
    'xiaomi_wake':    ['xiaomi wecken', 'wifi neustart', 'xiaomi neustarten'],
    'proaktiv_check': ['sei proaktiv','proaktiv','optimier','was kannst du','leg los','mach was','schau mal','check alles','guck ob','first mission','erste mission','was willst du','was wuerdest du','mach einfach','fang an','jetzt los','tu was'],
}

FRUST = ['nervt', 'wahnsinnig', 'klappt nicht', 'geht nicht', 'funktioniert nicht',
         'kaputt', 'buggy', 'scheiss', 'scheiß', 'wieder mal', 'schon wieder',
         'macht mucken', 'spinnt', 'macht probleme']

FRAGE = ['?', 'wie ', 'was ', 'check', 'pruef', 'prüf', 'zeig', 'schau', 'guck',
         'ist ', 'sind ', 'laeuft', 'läuft', 'mach ', 'kannst du']

# ---------- Erkennung ----------
def _keyword_detect(text):
    t = text.lower()
    frust = any(s in t for s in FRUST)
    frage = any(s in t for s in FRAGE)
    # Direkte Bestaetigungsfragen: "ist es verbunden", "laeuft es", "wie ist der status"
    bestaetigung = any(s in t for s in ['ist es', 'ist er', 'laeuft es', 'laeuft er', 'wie ist', 'status', 'verbunden'])
    treffer = []
    HIGH_CONF=['proaktiv_check','dienst_neustart','xiaomi_wake']
    for aktion, keys in KEYWORDS.items():
        for k in keys:
            if k in t:
                conf = 0.75 if aktion in HIGH_CONF else 0.5
                if frust: conf += 0.35
                if frage: conf += 0.25
                treffer.append((aktion, min(conf, 0.95), k))
                break
    if not treffer:
        return None
    treffer.sort(key=lambda x: -x[1])
    aktion, conf, key = treffer[0]
    return {'intent': aktion, 'confidence': round(conf, 2), 'methode': 'keyword', 'match': key}

def _gemini_detect(text):
    """Semantische Erkennung wenn Keywords nichts finden."""
    try:
        import jack_gemini_bridge
        liste = ', '.join(AKTIONEN.keys())
        prompt = (
            "Du bist ein Intent-Klassifikator fuer ein Android-KI-System.\n"
            f"Moegliche Aktionen: {liste}, keine\n\n"
            "Analysiere ob der Nutzer eine dieser Aktionen ausgefuehrt haben moechte.\n"
            "Nur wenn es klar erkennbar ist. Bei Smalltalk, persoenlichen Fragen "
            "oder allgemeinem Gespraech: keine.\n\n"
            "Antworte NUR mit JSON, nichts anderes:\n"
            '{"intent":"aktion_oder_keine","confidence":0.0-1.0}\n\n'
            f"NUTZER: {text}"
        )
        ans = jack_gemini_bridge.ask_gemini(prompt)
        if not ans: return None
        m = re.search(r'\{[^}]+\}', ans)
        if not m: return None
        d = json.loads(m.group(0))
        if d.get('intent') in ('keine', None, '') or d.get('intent') not in AKTIONEN:
            return None
        return {'intent': d['intent'], 'confidence': float(d.get('confidence', 0.5)),
                'methode': 'gemini', 'match': 'semantisch'}
    except Exception:
        return None

def _klingt_nach_aktion(text):
    """Grober Vorfilter damit wir nicht bei jedem Smalltalk Gemini fragen."""
    t = text.lower()
    if len(t) < 8: return False
    return any(s in t for s in FRAGE) or any(s in t for s in FRUST)

def detect(text, gemini_fallback=True):
    """Hauptfunktion. Gibt Intent-Dict zurueck oder None."""
    level = get_level()
    r = _keyword_detect(text)
    if not r and gemini_fallback and _klingt_nach_aktion(text):
        r = _gemini_detect(text)
    if not r:
        return None
    aktion = r['intent']
    meta = AKTIONEN.get(aktion, {'level': 4, 'text': aktion})
    min_level = meta['level']
    conf = r['confidence']

    # Level 4 = handelt selbst ab confidence 0.6
    # Level 2-3 = handelt bei hoher confidence, fragt sonst
    if level >= 4:
        auto = conf >= 0.6 and level >= min_level
        fragen = False
    elif level >= min_level:
        auto = conf >= 0.60
        fragen = 0.50 <= conf < 0.60
    else:
        auto = False
        fragen = False

    return {
        'intent': aktion,
        'beschreibung': meta['text'],
        'confidence': conf,
        'methode': r['methode'],
        'match': r.get('match', ''),
        'level': level,
        'min_level': min_level,
        'ausfuehren': auto,
        'nachfragen': fragen
    }

# ---------- Ausfuehrung ----------
def _ssh(cmd, timeout=10):
    import jack_config as _jc
    ip = _jc.get_param('NETWORK', 'xiaomi_ip')
    return subprocess.run(['ssh','-i',os.path.expanduser('~/.ssh/id_jack'),
        '-o','BatchMode=yes','-o','StrictHostKeyChecking=no',
        '-o','ConnectTimeout=4','-p','8022',f'root@{ip}',cmd],
        capture_output=True, text=True, timeout=timeout)

def execute(d):
    _gid = None
    try:
        import jack_gedanken as _gd
        if isinstance(d, dict):
            _gid = _gd.denke(
                ausloeser=d.get('_text','?'),
                hypothese='Erkannt via ' + d.get('methode','?') + ' (Match: ' + str(d.get('match','')) + ')',
                entscheidung=d.get('intent','?'),
                konfidenz=d.get('confidence',0.5),
                alternativen='nachfragen statt handeln' if d.get('nachfragen') else '',
                quelle='intent')
    except Exception: pass
    """Fuehrt Aktion aus, loggt Ergebnis."""
    aktion = d['intent'] if isinstance(d, dict) else d
    erg = ''
    try:
        if aktion == 'ssh_check':
            r = _ssh('true', 8)
            erg = 'Xiaomi SSH: ' + ('erreichbar' if r.returncode == 0 else 'nicht erreichbar')
        elif aktion == 'akku_check':
            r = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=12)
            b = json.loads(r.stdout)
            erg = f"Akku {b.get('percentage')}% | {b.get('status')} | {b.get('temperature')}C"
        elif aktion == 'ram_check':
            mi = {l.split(':')[0]: int(l.split()[1])//1024 for l in open('/proc/meminfo') if ':' in l}
            erg = f"RAM frei {mi.get('MemAvailable',0)}MB von {mi.get('MemTotal',0)}MB | Swap frei {mi.get('SwapFree',0)}MB"
        elif aktion == 'temp_check':
            mx, name = 0, ''
            for z in os.listdir('/sys/class/thermal'):
                try:
                    tp = open(f'/sys/class/thermal/{z}/type').read().strip()
                    if any(x in tp for x in ('trip','lvl','vbat')): continue
                    raw = int(open(f'/sys/class/thermal/{z}/temp').read())
                    if raw < 0: continue
                    g = raw/1000 if raw > 1000 else float(raw)
                    if g > mx: mx, name = g, tp
                except Exception: pass
            erg = f"Max {mx:.1f}C ({name})"
        elif aktion == 'dienste_check':
            r = subprocess.run(['python3', os.path.join(H,'jack_selftest.py')],
                capture_output=True, text=True, timeout=25)
            erg = re.sub(r'\x1b\[[0-9;]*m', '', r.stdout).strip()
        elif aktion == 'ollama_check':
            import urllib.request
            d2 = json.loads(urllib.request.urlopen('http://localhost:11434/api/tags', timeout=5).read())
            namen = [m['name'] for m in d2.get('models', [])]
            erg = 'Ollama laeuft | Modelle: ' + ', '.join(namen)
        elif aktion == 'fehler_check':
            con = sqlite3.connect(os.path.join(H,'jack_errors.db'))
            rows = con.execute("SELECT error_msg, timestamp FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 5").fetchall()
            con.close()
            erg = 'Keine offenen Fehler' if not rows else chr(10).join(f"[{r[1][:16]}] {r[0][:70]}" for r in rows)
        elif aktion == 'standort_check':
            import jack_sensors
            loc = jack_sensors.get_location()
            erg = f"{loc.get('latitude')}, {loc.get('longitude')}" if 'error' not in loc else str(loc['error'])
        elif aktion == 'dienst_neustart':
            P = os.environ.get('PREFIX','/data/data/com.termux/files/usr')
            tot = []
            for s in ('jack_cortex','jack_telegram','jack_waechter','ollama'):
                st = subprocess.run(['sv','status',f'{P}/var/service/{s}'], capture_output=True, text=True, timeout=8)
                if 'run:' not in st.stdout:
                    subprocess.run(['sv','up',f'{P}/var/service/{s}'], capture_output=True, timeout=10)
                    tot.append(s)
            erg = ('Neugestartet: ' + ', '.join(tot)) if tot else 'Alle Dienste laufen bereits'
        elif aktion == 'xiaomi_wake':
            r = _ssh("su -c 'svc wifi disable; sleep 3; svc wifi enable'", 30)
            erg = 'Xiaomi WiFi neugestartet' if r.returncode == 0 else 'Xiaomi nicht erreichbar'
        elif aktion == 'proaktiv_check':
            import jack_gemini_bridge as _jgb
            s=_jgb.collect_status()
            lines=[f"System: {'OK' if s.get('alle_ok') else 'PROBLEM'} | RAM: {s.get('ram_frei_mb','?')}MB | Temp: {s.get('temp_cpu','?')}C"]
            try:
                import jack_xiaomi as _jx; xr=_jx.explore_next()
                lines.append(f"Xiaomi: RAM {xr.get('ram','?')} | Akku {xr.get('battery','?')} | Load {xr.get('cpu_user','?')} | Temp {xr.get('temp_c','?')}C")
            except Exception as xe: lines.append(f"Xiaomi: {xe}")
            try:
                import jack_log; lines.append("Log: "+jack_log.recent(2))
            except Exception: pass
            erg=chr(10).join(lines)
        elif aktion == 'werkstatt_leeren':
            w = os.path.expanduser('~/jack_werkstatt')
            n = len([f for f in os.listdir(w)]) if os.path.isdir(w) else 0
            erg = f'Werkstatt hat {n} Dateien (Loeschen nur manuell, Sicherheit)'
        else:
            erg = f'Aktion {aktion} unbekannt'
    except Exception as e:
        erg = f'Fehler bei {aktion}: {str(e)[:150]}'

    try:
        import jack_gedanken as _gd2
        _gd2.ergebnis(_gid, erg, 'fehler' not in str(erg).lower())
    except Exception: pass
    if isinstance(d, dict):
        _log_intent(d.get('_text',''), aktion, d.get('methode','?'),
                    d.get('confidence',0), True, erg)
    return erg

if __name__ == '__main__':
    t = ' '.join(sys.argv[1:]) or 'der xiaomi nervt schon wieder'
    d = detect(t)
    print(json.dumps(d, ensure_ascii=False, indent=2) if d else 'Kein Intent')
    if d and (d['ausfuehren'] or d['nachfragen']):
        print('---'); print(execute(d))
