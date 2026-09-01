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

def step_input_text(p):
    import time
    txt=str(p.get('text',''))
    _ssh('su -c "input keyevent 123"')
    time.sleep(0.3)
    _ssh('su -c "input keyevent 28 28"')
    time.sleep(0.3)
    safe=txt.replace(' ','%s').replace('&','and').replace('?','')
    _ssh('su -c "input text '+safe+'"')
    time.sleep(0.3)
    return 'Eingabe: '+txt[:40]

def step_ui_text(p):
    import jack_ghost as jg
    xml=jg.hol_xiaomi_ui()
    import xml.etree.ElementTree as ET
    try: root=ET.fromstring(xml)
    except Exception: return 'XML-Fehler'
    words=[n.get('text','') for n in root.iter('node') if n.get('text','').strip()]
    return ' | '.join(words[:20])[:500]

def step_chrome_search(p):
    import subprocess as _sp, time, jack_ghost as jg, xml.etree.ElementTree as ET
    q=p.get('query','').replace(' ','+')
    url='https://www.google.com/search?q='+q if not p.get('url') else p.get('url')
    cmd="su -c 'am start -n com.android.chrome/com.google.android.apps.chrome.Main -a android.intent.action.VIEW -d \"" +url+"\"'"
    _sp.run(['ssh','xiaomi-jack',cmd],capture_output=True,timeout=12)
    time.sleep(p.get('wait',5))
    xml=jg.hol_xiaomi_ui()
    try:
        root=ET.fromstring(xml)
        words=[n.get('text','') for n in root.iter('node') if n.get('text','').strip()]
        return ' | '.join(words[:25])[:600]
    except Exception: return 'XML-Fehler'

STEPS={'exec':step_exec,'tap':step_tap,'find_and_tap':step_find_and_tap,
    'open_app':step_open_app,'keyevent':step_keyevent,'wait':step_wait,
    'ui_check':step_ui_check,'home':step_home,
    'input_text':step_input_text,'ui_text':step_ui_text,'chrome_search':step_chrome_search}

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
        import time as _t
        results.append({'n':i+1,'typ':typ,'desc':desc,'r':r,'ts':int(_t.time())})
        abort=step.get('abort_on_fail') and ('FEHLER' in r or 'NICHT_GEFUNDEN' in r)
        msg='['+str(i+1)+'/'+str(len(steps))+'] '+desc+': '+r[:150]
        if send_fn: send_fn(msg)
        if abort:
            if send_fn: send_fn('Abgebrochen nach Schritt '+str(i+1))
            return results
        time.sleep(step.get('delay',0.8))
    try:
        import jack_outcome,importlib
        importlib.reload(jack_outcome)
        rec=jack_outcome.evaluate(plan,results)
        if send_fn: send_fn(jack_outcome.fmt(rec))
        if rec.get('outcome')=='SUCCESS':
            try:
                import jack_skill_lib as _sk
                _sk.record_run(name, True)
                skill=_sk.get(name)
                if not skill:
                    _sk.save(name, plan, 'Auto-gespeichert nach erstem Erfolg')
                    if send_fn: send_fn('Skill gespeichert: '+name+' [CANDIDATE]')
                else:
                    if send_fn: send_fn('Skill: '+name+' ['+skill['state']+'] '+str(skill['successes'])+'/'+str(skill['executions'])+' Erfolge')
            except Exception: pass
    except Exception as _oe:
        if send_fn: send_fn('Fertig: '+name)
    return results
