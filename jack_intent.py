#!/usr/bin/env python3
"""Erkennt Aktions-Intent in Dimas Nachrichten."""
import os, json, subprocess, sys
sys.path.insert(0, os.path.expanduser('~/jack'))

LEVEL_FILE = os.path.expanduser('~/jack/.autonomie_level')

def get_level():
    try: return int(open(LEVEL_FILE).read().strip())
    except: return 1

def set_level(n):
    open(LEVEL_FILE,'w').write(str(n))

# Intent-Patterns: keyword -> (aktion, min_level, beschreibung)
INTENTS = {
    'ssh': ('ssh_check', 1, 'SSH-Status Xiaomi pruefen'),
    'xiaomi': ('ssh_check', 1, 'Xiaomi SSH pruefen'),
    'akku': ('akku_check', 1, 'Akkustand pruefen'),
    'ram': ('ram_check', 1, 'RAM-Status pruefen'),
    'dienste': ('dienste_check', 1, 'Dienste pruefen'),
    'ollama': ('ollama_check', 1, 'Ollama-Status pruefen'),
    'temperature': ('temp_check', 1, 'Temperatur pruefen'),
    'heiß': ('temp_check', 1, 'Temperatur pruefen'),
    'heiss': ('temp_check', 1, 'Temperatur pruefen'),
    'neustart': ('restart_services', 2, 'Dienste neustarten'),
    'restart': ('restart_services', 2, 'Dienste neustarten'),
    'aufräumen': ('cleanup', 2, 'Werkstatt aufraemen'),
}

FRUSTRATIONS_SIGNALE = [
    'nervt', 'macht mich wahnsinnig', 'klappt nicht', 'geht nicht',
    'funktioniert nicht', 'kaputt', 'buggy', 'scheiß', 'wieder mal'
]

def detect(text):
    """Gibt Intent-Dict zurueck oder None."""
    t = text.lower()
    level = get_level()
    
    # Frustration + Kontext = hohe Confidence
    frustration = any(s in t for s in FRUSTRATIONS_SIGNALE)
    
    for keyword, (aktion, min_level, beschreibung) in INTENTS.items():
        if keyword in t:
            confidence = 0.9 if frustration else 0.6
            ausfuehren = level >= min_level and confidence >= 0.8
            return {
                'intent': aktion,
                'confidence': confidence,
                'beschreibung': beschreibung,
                'ausfuehren': ausfuehren,
                'level': level,
                'min_level': min_level
            }
    return None

def execute(intent_dict):
    """Fuehrt die erkannte Aktion aus."""
    aktion = intent_dict['intent']
    try:
        if aktion == 'ssh_check':
            import jack_config as _jc
            ip = _jc.get_param('NETWORK', 'xiaomi_ip')
            r = subprocess.run(['ssh','-i',os.path.expanduser('~/.ssh/id_jack'),
                '-o','BatchMode=yes','-o','StrictHostKeyChecking=no',
                '-o','ConnectTimeout=3','-p','8022',f'root@{ip}','true'],
                capture_output=True, timeout=6)
            return 'Xiaomi SSH: ' + ('OK' if r.returncode == 0 else 'nicht erreichbar')
        elif aktion == 'akku_check':
            r = subprocess.run(['termux-battery-status'], capture_output=True, text=True, timeout=10)
            d = json.loads(r.stdout)
            return f"Akku: {d.get('percentage')}% | {d.get('status')} | {d.get('temperature')}C"
        elif aktion == 'ram_check':
            avail = int([l for l in open('/proc/meminfo') if 'MemAvailable' in l][0].split()[1]) // 1024
            return f"RAM frei: {avail}MB"
        elif aktion == 'temp_check':
            import jack_thermal
            return jack_thermal.zusammenfassung() if hasattr(jack_thermal, 'zusammenfassung') else 'Temp-Check nicht verfuegbar'
        elif aktion == 'dienste_check':
            r = subprocess.run(['python3', os.path.expanduser('~/jack/jack_selftest.py')],
                capture_output=True, text=True, timeout=20)
            import re
            return re.sub(r'\x1b\[[0-9;]*m', '', r.stdout).strip()
        elif aktion == 'xiaomi_status':
            import jack_config as _jc
            ip = _jc.get_param('NETWORK', 'xiaomi_ip')
            r = subprocess.run(['ssh','-i',os.path.expanduser('~/.ssh/id_jack'),
                '-o','BatchMode=yes','-o','StrictHostKeyChecking=no',
                '-o','ConnectTimeout=3','-p','8022',f'root@{ip}','true'],
                capture_output=True, timeout=6)
            return 'Xiaomi SSH: ' + ('OK' if r.returncode == 0 else 'nicht erreichbar')
        elif aktion == 'ollama_check':
            import urllib.request
            urllib.request.urlopen('http://localhost:11434/api/tags', timeout=3)
            return 'Ollama: laeuft'
        else:
            return f'Aktion {aktion} noch nicht implementiert'
    except Exception as e:
        return f'Fehler bei {aktion}: {str(e)[:100]}'

if __name__ == '__main__':
    test = sys.argv[1] if len(sys.argv) > 1 else 'der xiaomi nervt mich'
    r = detect(test)
    print(json.dumps(r, ensure_ascii=False, indent=2) if r else 'Kein Intent erkannt')
