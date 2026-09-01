DIALOG_KEYWORDS=[
    'akzeptieren','ablehnen','zustimmen','verstanden','ok','weiter',
    'accept','decline','agree','continue','allow','permit',
    'anmelden','einloggen','login','sign in','registrieren',
    'bestaetigen','confirm','cookie','datenschutz','privacy',
    'jetzt nicht','spaeter','skip','ueberspringen',
    'alle akzeptieren','alle ablehnen','notwendige',
    'schliessen','close','fertig','done'
]

SKIP_KEYWORDS=[
    'kaufen','bezahlen','buy','purchase','checkout','bestellen',
    'kreditkarte','paypal','zahlung','payment',
    'passwort eingeben','password','pin eingeben'
]

def finde_dialog_button(xml):
    import xml.etree.ElementTree as ET, jack_ghost as jg
    try:
        root=ET.fromstring(xml)
        for n in root.iter('node'):
            if n.get('clickable')!='true': continue
            t=(n.get('text','').strip()+' '+n.get('content-desc','').strip()).lower()
            if any(k in t for k in SKIP_KEYWORDS): continue
            if any(k in t for k in DIALOG_KEYWORDS):
                pos=jg._mitte(n.get('bounds',''))
                if pos: return {'text':t[:40],'x':pos[0],'y':pos[1]}
    except Exception: pass
    return None
import subprocess,os,time,json,sys
sys.path.insert(0,os.path.expanduser('~/jack'))

MAP_FILE=os.path.expanduser('~/jack/xiaomi_deep_map.json')

def _ssh(cmd,t=10):
    return subprocess.run(['ssh','xiaomi-jack',cmd],capture_output=True,text=True,timeout=t)

def _dump_ui():
    import jack_ghost as jg
    return jg.hol_xiaomi_ui()

def _get_clickable(xml):
    import xml.etree.ElementTree as ET,jack_ghost as jg
    try:
        root=ET.fromstring(xml)
        els=[]
        for n in root.iter('node'):
            if n.get('clickable')!='true': continue
            t=n.get('text','').strip() or n.get('content-desc','').strip()
            pos=jg._mitte(n.get('bounds',''))
            if pos and pos[1]<2100:
                els.append({'text':t[:40],'x':pos[0],'y':pos[1]})
        return els
    except Exception: return []

def _kill(paket):
    _ssh('am force-stop '+paket,5)

def handle_dialogs(send_fn=None, max_rounds=10):
    import jack_ghost as jg, time
    for _ in range(max_rounds):
        xml=jg.hol_xiaomi_ui()
        if not xml.startswith('<'): break
        btn=finde_dialog_button(xml)
        if not btn: break
        if send_fn: send_fn('  Dialog: '+btn['text'][:30])
        _ssh("su -c 'input tap "+str(btn['x'])+" "+str(btn['y'])+"'",5)
        time.sleep(1.5)

def explore_deep(paket,max_els=8,depth=2,send_fn=None):
    if send_fn: send_fn('Deep-Explore: '+paket)
    try:
        _ssh("su -c 'monkey -p "+paket+" 1'",10)
        time.sleep(3)
    except Exception as e:
        if send_fn: send_fn('Start fehlgeschlagen: '+str(e)[:80])
        return None
    nav_map={'paket':paket,'ebene1':{}}
    xml1=_dump_ui()
    if not xml1.startswith('<'):
        _kill(paket); return None
    handle_dialogs(send_fn)
    xml1=_dump_ui()
    if not xml1.startswith('<'):
        _kill(paket); return None
    els1=_get_clickable(xml1)[:max_els]
    if send_fn: send_fn('Ebene 1: '+str(len(els1))+' Buttons nach Dialog-Handling')
    for el in els1:
        txt=el['text'] or 'btn_'+str(el['x'])+'_'+str(el['y'])
        _ssh("su -c 'input tap "+str(el['x'])+" "+str(el['y'])+"'",5)
        time.sleep(1.5)
        xml2=_dump_ui()
        import xml.etree.ElementTree as ET2
        try:
            root2=ET2.fromstring(xml2)
            texts2=[n.get('text','') for n in root2.iter('node') if n.get('text','').strip()][:8]
            els2=_get_clickable(xml2)[:5]
        except Exception: texts2=[]; els2=[]
        nav_map['ebene1'][txt]={'buttons':len(els2),'texte':texts2[:5]}
        if send_fn: send_fn('  '+txt[:25]+' -> '+str(len(els2))+' Btns | '+', '.join(texts2[:3])[:50])
        try:
            import jack_skill_lib as sk
            sname='nav_'+paket.split('.')[-1]+'_'+txt[:15].replace(' ','_').replace('/','')
            sk.save(sname,{'steps':[
                {'type':'open_app','paket':paket,'desc':'Oeffne '+paket},
                {'type':'wait','seconds':3,'desc':'Laden'},
                {'type':'tap','x':el['x'],'y':el['y'],'desc':'Tippe '+txt[:20]},
                {'type':'wait','seconds':2,'desc':'Warten'},
                {'type':'ui_text','desc':'Lesen'},
                {'type':'home','desc':'Home'}
            ]},'Deep-Explore: '+paket+' -> '+txt[:20])
        except Exception: pass
        handle_dialogs(send_fn)
        _ssh("su -c 'input keyevent 4'",5)
        time.sleep(0.8)
    _kill(paket)
    _ssh("su -c 'input keyevent 3'",5)
    try:
        known=json.load(open(MAP_FILE)) if os.path.exists(MAP_FILE) else {}
        known[paket]=nav_map
        json.dump(known,open(MAP_FILE,'w'),ensure_ascii=False,indent=2)
    except Exception: pass
    if send_fn: send_fn('Fertig: '+paket+' - '+str(len(nav_map['ebene1']))+' Pfade')
    return nav_map

def run_deep_loop(apps=None,max_per_app=6,send_fn=None):
    import jack_explorer as je
    if not apps: apps=je.scan_apps()
    try: known=set(json.load(open(MAP_FILE)).keys()) if os.path.exists(MAP_FILE) else set()
    except Exception: known=set()
    done=0
    for paket in apps:
        if paket in known: continue
        if done>=3: break
        explore_deep(paket,max_per_app,2,send_fn)
        done+=1; time.sleep(2)
    if send_fn: send_fn('Loop fertig. '+str(done)+' Apps tief erkundet.')
