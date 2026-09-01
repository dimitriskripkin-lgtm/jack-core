import subprocess,os,time,sys
sys.path.insert(0,os.path.expanduser('~/jack'))

def _ssh(cmd,t=10):
    return subprocess.run(['ssh','xiaomi-jack',cmd],capture_output=True,text=True,timeout=t)

def _tap(x,y):
    _ssh("su -c 'input tap "+str(x)+" "+str(y)+"'",5)
    time.sleep(1.2)

def _back():
    _ssh("su -c 'input keyevent 4'",5)
    time.sleep(0.8)

def _home():
    _ssh("su -c 'input keyevent 3'",5)
    time.sleep(1)

def _termux_cmd(cmd,t=15):
    import subprocess
    r=subprocess.run(['ssh','xiaomi-jack',cmd],capture_output=True,text=True,timeout=t)
    return ((r.stdout or '')+(r.stderr or '')).strip()[:400]

def _type(text):
    safe=text.replace(' ','%s')
    _ssh("su -c 'input text "+safe+"'",5)
    time.sleep(0.5)

def _enter():
    _ssh("su -c 'input keyevent 66'",5)
    time.sleep(0.8)

def _dump():
    import jack_ghost as jg
    return jg.hol_xiaomi_ui()

def _lese_ui(xml):
    import xml.etree.ElementTree as ET,jack_ghost as jg
    try:
        root=ET.fromstring(xml)
        buttons=[]
        texts=[]
        for n in root.iter('node'):
            t=n.get('text','').strip()
            d=n.get('content-desc','').strip()
            if t: texts.append(t[:50])
            if n.get('clickable')=='true':
                pos=jg._mitte(n.get('bounds',''))
                if pos and pos[1]<2100:
                    buttons.append({'label':(t or d)[:40],'x':pos[0],'y':pos[1]})
        return texts[:20],buttons[:12]
    except Exception:
        return [],[]

def _frage_gemini(ziel,verlauf,texte,buttons):
    import jack_gemini_bridge as gb
    btn_str=', '.join([b['label'] or 'unnamed' for b in buttons])
    txt_str=' | '.join(texte[:10])
    ssh_out=''
    prompt=("Du steuerst ein Android-Geraet via SSH und UI. Ziel: "+ziel+chr(10)+chr(10)+"WICHTIG: Fuer Terminal-Befehle (ls, python3, cd etc) schreibe TIPPEN: $befehl - das fuehrt den Befehl direkt via SSH aus."+chr(10)+"Fuer UI-Interaktion (Buttons antippen) schreibe AKTION: tap und ZIEL_BUTTON: Buttonname."+chr(10)+"ZIEL_ERREICHT: ja NUR wenn du den Output gelesen und dokumentiert hast."+chr(10)+chr(10)+("Letzter SSH-Output: "+verlauf[-1] if verlauf and 'OUTPUT:' in verlauf[-1] else "")+chr(10)+chr(10)+"KONTEXT: Wenn du Buttons wie ESC, HOME, TAB, Pfeile oder eine Tastatur siehst, bist du BEREITS in Termux. Termux ist ein Terminal - du kannst SOFORT Befehle tippen. Nicht zurueck, nicht suchen - einfach tippen!"+chr(10)+"REGEL: Fuehre ALLE Befehle als TIPPEN: $befehl aus. NIEMALS ohne Dollar-Zeichen tippen."+chr(10)+chr(10)+
        "Sichtbare Texte: "+txt_str+chr(10)+
        "Klickbare Buttons: "+btn_str+chr(10)+chr(10)+
        "Verlauf: "+chr(10).join(verlauf[-4:])+chr(10)+chr(10)+
        "WICHTIG: Ziel gilt erst als erreicht wenn du den Output GELESEN hast und ihn im Verlauf dokumentiert hast. Nicht vorher!"+chr(10)+chr(10)+"Antworte IMMER auf Deutsch in diesem Format:"+chr(10)+
        "AKTION: [tap/back/home/tippen/enter/warte/fertig]"+chr(10)+
        "ZIEL_BUTTON: [exakter Button-Text oder leer]"+chr(10)+
        "TIPPEN: [Text der eingegeben werden soll oder leer]"+chr(10)+
        "BEGRUENDUNG: [ein Satz auf Deutsch]"+chr(10)+
        "ZIEL_ERREICHT: [ja/nein]")
    try:
        return gb.ask_gemini(prompt,{})
    except Exception:
        return "AKTION: back\nZIEL_BUTTON: \nTIPPEN: \nBEGRUENDUNG: Fehler\nZIEL_ERREICHT: nein"

def _parse(antwort):
    r={'aktion':'back','button':'','tippen':'','grund':'','fertig':False}
    for line in antwort.splitlines():
        if line.startswith('AKTION:'): r['aktion']=line[7:].strip().lower()
        elif line.startswith('ZIEL_BUTTON:'): r['button']=line[12:].strip()
        elif line.startswith('TIPPEN:'): r['tippen']=line[7:].strip()
        elif line.startswith('BEGRUENDUNG:'): r['grund']=line[12:].strip()
        elif line.startswith('ZIEL_ERREICHT:') and 'ja' in line.lower(): r['fertig']=True
    return r

def run_ssh_agent(befehle,send_fn=None):
    import jack_gemini_bridge as gb
    ergebnisse=[]
    for cmd in befehle:
        out=_termux_cmd(cmd)
        if send_fn: send_fn('$ '+cmd+chr(10)+out)
        ergebnisse.append({'cmd':cmd,'out':out})
    zusammenfassung='\n'.join(['$ '+e['cmd']+chr(10)+e['out'][:200] for e in ergebnisse])
    prompt='Hier sind die Ergebnisse der SSH-Befehle auf dem Xiaomi Android Geraet:'+chr(10)+zusammenfassung+chr(10)+chr(10)+'Fasse zusammen was du gelernt hast. Antworte auf Deutsch.'
    try:
        fazit=gb.ask_gemini(prompt,{})
        if send_fn: send_fn(chr(10)+'FAZIT: '+fazit[:500])
    except Exception as e:
        if send_fn: send_fn('Fazit-Fehler: '+str(e)[:100])
    return ergebnisse

def run_agent(ziel,start_app=None,max_schritte=20,send_fn=None):
    if send_fn: send_fn('Agent gestartet: '+ziel)
    verlauf=[]
    if start_app:
        subprocess.run(['ssh','xiaomi-jack',"su -c 'monkey -p "+start_app+" 1'"],capture_output=True,timeout=10)
        time.sleep(3)
    for schritt in range(1,max_schritte+1):
        xml=_dump()
        if not xml.startswith('<'):
            time.sleep(3); continue
        texte,buttons=_lese_ui(xml)
        antwort=_frage_gemini(ziel,verlauf,texte,buttons)
        e=_parse(antwort)
        log='['+str(schritt)+'] '+e['aktion'].upper()+': '+e['grund'][:60]
        verlauf.append(log)
        if send_fn: send_fn(log)
        if schritt>=3 and (e['fertig'] or e['aktion']=='fertig'):
            if send_fn: send_fn('Ziel erreicht!')
            _home(); return True,verlauf
        if e['aktion']=='tap' and e['button']:
            btn=next((b for b in buttons if e['button'].lower() in (b['label'] or '').lower()),None)
            if btn: _tap(btn['x'],btn['y'])
            else: _back()
        elif e['aktion']=='tippen' and e['tippen']:
            txt=e['tippen'].strip()
            if txt.startswith('$'):
                cmd=txt[1:].strip()
                out=_termux_cmd(cmd)
                if send_fn: send_fn('$ '+cmd+chr(10)+out)
                verlauf.append('OUTPUT: '+out[:150])
            else:
                _type(txt)
        elif e['aktion']=='enter':
            _enter()
        elif e['aktion']=='back':
            _back()
        elif e['aktion']=='home':
            _home()
        elif e['aktion']=='warte':
            time.sleep(3)
        time.sleep(0.5)
    _home()
    if send_fn: send_fn('Max Schritte erreicht.')
    return False,verlauf
