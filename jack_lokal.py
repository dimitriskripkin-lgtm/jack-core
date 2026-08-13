#!/usr/bin/env python3
"""Lokale Inferenz mit harten Guards: RAM, Temperatur, Timeout.
Modell-agnostisch - nimmt was da ist, bestes zuerst."""
import os, json, time, urllib.request

OLLAMA = 'http://localhost:11434'
CFG = os.path.expanduser('~/jack/.lokal_modell')

KANDIDATEN = [
    ('gemma4:e4b', 4200), ('gemma4:e2b', 2600), ('gemma4', 2600),
    ('gemma3n:e4b', 4200), ('gemma3n:e2b', 2600),
    ('gemma3:4b', 3000), ('gemma3:1b', 900),
    ('llama3.2:3b', 2200), ('llama3.2', 2200),
    ('qwen2.5:3b', 2200), ('phi3', 2300),
]

RAM_RESERVE = 1500
TEMP_MAX = 72

def _ram_frei():
    try:
        return int([l for l in open('/proc/meminfo') if 'MemAvailable' in l][0].split()[1])//1024
    except Exception:
        return 0

def _temp():
    mx = 0
    try:
        for z in os.listdir('/sys/class/thermal'):
            try:
                tp = open('/sys/class/thermal/'+z+'/type').read().strip()
                if any(x in tp for x in ('trip','lvl','vbat')): continue
                rv = int(open('/sys/class/thermal/'+z+'/temp').read())
                if rv < 0: continue
                g = rv/1000 if rv > 1000 else float(rv)
                if g > mx: mx = g
            except Exception: pass
    except Exception: pass
    return mx

def installiert():
    try:
        with urllib.request.urlopen(OLLAMA+'/api/tags', timeout=5) as r:
            return [m['name'] for m in json.loads(r.read()).get('models',[])]
    except Exception:
        return []

def waehle():
    """Bestes installiertes Modell das ins RAM passt."""
    da = installiert()
    frei = _ram_frei()
    for name, bedarf in KANDIDATEN:
        for inst in da:
            if inst == name or inst.startswith(name+':') or inst.split(':')[0] == name:
                if frei - bedarf >= RAM_RESERVE:
                    return inst, bedarf
    return None, 0

def aktiv():
    try:
        return open(CFG).read().strip() or None
    except Exception:
        m, _ = waehle()
        if m:
            try: open(CFG,'w').write(m)
            except Exception: pass
        return m

def setze(name):
    try:
        open(CFG,'w').write(name); return True
    except Exception:
        return False

VERBOTEN = ('code_pruefen','code_validieren','syntax_check','sicherheit')

def bereit():
    """(ok, grund) - warum lokal gerade nicht geht."""
    m = aktiv()
    if not m:
        return False, 'kein passendes Modell installiert oder RAM zu knapp'
    frei = _ram_frei()
    if frei < RAM_RESERVE + 800:
        return False, 'nur ' + str(frei) + 'MB RAM frei'
    t = _temp()
    if t > TEMP_MAX:
        return False, 'zu heiss: ' + str(round(t,1)) + 'C'
    return True, m

def frage(prompt, aufgabe='allgemein', timeout=90, max_tokens=350, temp=0.3):
    """Lokale Inferenz. Gibt (text, fehler) zurueck."""
    if aufgabe in VERBOTEN:
        return None, 'Lokales Modell darf Code nicht validieren - Regel'
    ok, info = bereit()
    if not ok:
        return None, info
    payload = json.dumps({
        'model': info, 'prompt': prompt, 'stream': False,
        'keep_alive': '2m',
        'options': {'num_predict': max_tokens, 'temperature': temp}
    }).encode()
    t0 = time.time()
    try:
        req = urllib.request.Request(OLLAMA+'/api/generate', data=payload,
            headers={'Content-Type':'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            antwort = json.loads(r.read()).get('response','').strip()
        dauer = round(time.time()-t0,1)
        try:
            import jack_log
            jack_log.log_decision('LOKAL-INFERENZ', info + ' | ' + aufgabe + ' | ' + str(dauer) + 's | ' + str(round(_temp(),1)) + 'C')
        except Exception: pass
        return antwort, None
    except Exception as e:
        return None, str(e)[:120]

def status():
    m = aktiv()
    ok, info = bereit()
    z = ['Lokales Modell: ' + (m or 'keins')]
    z.append('Bereit: ' + ('ja' if ok else 'nein - ' + str(info)))
    z.append('RAM frei: ' + str(_ram_frei()) + 'MB | Temp: ' + str(round(_temp(),1)) + 'C')
    da = installiert()
    if da: z.append('Installiert: ' + ', '.join(da[:5]))
    return chr(10).join(z)

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2 and sys.argv[1] == 'frage':
        a, e = frage(' '.join(sys.argv[2:]))
        print(a if a else 'FEHLER: ' + str(e))
    else:
        print(status())
