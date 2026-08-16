import json,os,time,subprocess,sys
sys.path.insert(0,os.path.expanduser('~/jack'))

def _ssh(cmd,t=15):
    return subprocess.run(['ssh','xiaomi-jack',cmd],capture_output=True,text=True,timeout=t)

def step_exec(p):
    import jack_exec as je
    return je.run(p['cmd'],p.get('timeout',30))

def step_tap(p):
    import jack_ghost as jg
    return jg.tap_xiaomi(p['x'],p['y'])

def step_find_and_tap(p):
    import jack_ghost as jg
    xml=jg.hol_xiaomi_ui()
    tr=jg.finde_element(xml,p['text'])
    if not tr: return 'NICHT_GEFUNDEN: '+p['text']
    e=tr[0]
    return jg.tap_xiaomi(e['x'],e['y'])+' auf '+e['text'][:40]

def step_open_app(p):
    subprocess.run(['ssh','xiaomi-jack',"su -c 'monkey -p "+p['paket']+" 1'"],capture_output=True,timeout=10)
    time.sleep(2)
    return 'App '+p['paket']+' geoeffnet'

def step_keyevent(p):
    _ssh("su -c 'input keyevent "+str(p['keycode'])+"'")
    return 'keyevent '+str(p['keycode'])

def step_wait(p):
    time.sleep(float(p['seconds']))
    return 'Gewartet '+str(p['seconds'])+'s'

def step_ui_check(p):
    import jack_ghost as jg
    xml=jg.hol_xiaomi_ui()
    tr=jg.finde_element(xml,p['text'])
    if tr: return 'GEFUNDEN: '+p['text']+' bei ('+str(tr[0]['x'])+','+str(tr[0]['y'])+')'
    return 'NICHT_DA: '+p['text']

def step_home(p):
    import jack_ghost as jg
    jg.tap_xiaomi(540,2310)
    return 'Home'

STEPS={'exec':step_exec,'tap':step_tap,'find_and_tap':step_find_and_tap,
    'open_app':step_open_app,'keyevent':step_keyevent,'wait':step_wait,
    'ui_check':step_ui_check,'home':step_home}

def run_plan(plan,send_fn=None):
    name=plan.get('name','Plan')
    steps=plan.get('steps',[])
    if send_fn: send_fn('Starte: '+name+' ('+str(len(steps))+' Schritte)')
    results=[]
    for i,step in enumerate(steps):
        typ=step.get('type','')
        desc=step.get('desc',typ)
        try:
            fn=STEPS.get(typ)
            r=str(fn(step)) if fn else 'UNBEKANNT: '+typ
        except Exception as e:
            r='FEHLER: '+str(e)[:120]
        results.append({'n':i+1,'typ':typ,'r':r})
        abort=step.get('abort_on_fail') and ('FEHLER' in r or 'NICHT_GEFUNDEN' in r)
        msg='['+str(i+1)+'/'+str(len(steps))+'] '+desc+': '+r[:150]
        if send_fn: send_fn(msg)
        if abort:
            if send_fn: send_fn('Abgebrochen nach Schritt '+str(i+1))
            return results
        time.sleep(step.get('delay',0.8))
    if send_fn: send_fn('Fertig: '+name)
    return results
