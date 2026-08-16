import subprocess, os, time, json, sys
sys.path.insert(0, os.path.expanduser('~/jack'))

APPS_FILE=os.path.expanduser('~/jack/xiaomi_app_map.json')

def scan_apps():
    r=subprocess.run(['ssh','xiaomi-jack',"su -c 'pm list packages -3 2>/dev/null'"],capture_output=True,text=True,timeout=20)
    pkgs=[l.replace('package:','').strip() for l in r.stdout.splitlines() if l.startswith('package:')]
    if not pkgs:
        r2=subprocess.run(['ssh','xiaomi-jack','pm list packages -3 2>/dev/null'],capture_output=True,text=True,timeout=20)
        pkgs=[l.replace('package:','').strip() for l in r2.stdout.splitlines() if l.startswith('package:')]
    if not pkgs:
        r2=subprocess.run(['ssh','xiaomi-jack','pm list packages -3 2>/dev/null'],capture_output=True,text=True,timeout=20)
        pkgs=[l.replace('package:','').strip() for l in r2.stdout.splitlines() if l.startswith('package:')]
    return pkgs

def explore_app(paket, timeout=12):
    import jack_ghost as jg
    try:
        subprocess.run(['ssh','xiaomi-jack',"su -c 'monkey -p "+paket+" 1'"],capture_output=True,timeout=10)
        time.sleep(3)
        xml=jg.hol_xiaomi_ui()
        if not xml.startswith('<'): return None
        import xml.etree.ElementTree as ET
        root=ET.fromstring(xml)
        texts=[n.get('text','') for n in root.iter('node') if n.get('text','').strip()]
        clickable=len([n for n in root.iter('node') if n.get('clickable')=='true'])
        subprocess.run(['ssh','xiaomi-jack',"su -c 'input keyevent 3'"],capture_output=True,timeout=5)
        return {'paket':paket,'texts':texts[:20],'clickable':clickable,'ts':int(time.time())}
    except Exception as e:
        return {'paket':paket,'error':str(e)[:100],'ts':int(time.time())}

def run_exploration(max_apps=5, send_fn=None):
    apps=scan_apps()
    if send_fn: send_fn('Xiaomi Apps gefunden: '+str(len(apps))+'. Erkunde '+str(max_apps)+'...')
    try:
        known=json.load(open(APPS_FILE))
    except: known={}
    results=[]
    explored=0
    for paket in apps:
        if explored>=max_apps: break
        if paket in known: continue
        if send_fn: send_fn('Erkunde: '+paket)
        info=explore_app(paket)
        if info:
            known[paket]=info
            results.append(info)
            if send_fn:
                t=', '.join([x for x in info.get('texts',[]) if x][:5])
                send_fn('Gelernt: '+paket+' - '+str(info.get('clickable',0))+' Buttons | '+t[:80])
            try:
                import jack_skill_lib as sk
                plan={'steps':[
                    {'type':'open_app','paket':paket,'desc':'Oeffne '+paket},
                    {'type':'wait','seconds':2,'desc':'Laden'},
                    {'type':'ui_text','desc':'UI lesen'},
                    {'type':'home','desc':'Home'}
                ]}
                sk.save('explore_'+paket.split('.')[-1], plan, 'Auto-exploriert: '+paket)
            except: pass
            explored+=1
            time.sleep(1)
    json.dump(known, open(APPS_FILE,'w'), ensure_ascii=False, indent=2)
    if send_fn: send_fn('Exploration abgeschlossen. '+str(explored)+' neue Apps gelernt. Gesamt bekannt: '+str(len(known)))
    return results
