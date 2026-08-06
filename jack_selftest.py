#!/usr/bin/env python3
import os,subprocess,sys,time,urllib.request
sys.path.append(os.path.expanduser('~/jack'))
P=os.environ.get('PREFIX','/data/data/com.termux/files/usr')
G,R='\033[92m[OK]\033[0m','\033[91m[ER]\033[0m'
def t(b,n,m):print(G if b else R,n,m);return b
def dienste():
    ok=True
    for n in['jack_cortex','jack_telegram','jack_waechter','ollama']:
        s=subprocess.run(['sv','status',f'{P}/var/service/{n}'],
            capture_output=True,text=True)
        u='run:'in s.stdout;ok=ok and t(u,n,'up'if u else s.stdout.strip()[:30])
    return ok
def ram():
    a=int([l for l in open('/proc/meminfo')if'MemAvailable'in l][0].split()[1])//1024
    return t(a>=800,'RAM',f'{a}MB verfuegbar')
def temp():
    mx=0;h=''
    for z in os.listdir('/sys/class/thermal'):
        try:
            tp=open(f'/sys/class/thermal/{z}/type').read().strip()
            if any(x in tp for x in['trip','lvl','vbat']):continue
            r=int(open(f'/sys/class/thermal/{z}/temp').read())
            if r<0:continue
            g=r/1000 if r>1000 else float(r)
            if g>mx:mx=g;h=tp
        except:pass
    return t(mx<43,'Temp',f'{mx:.1f}C max ({h})')
def pub():
    r=subprocess.run(['git','-C',os.path.expanduser('~/jack-context'),
        'log','--format=%ct','-1'],capture_output=True,text=True)
    try:age=int((time.time()-int(r.stdout.strip()))//60);return t(age<10,'Publisher',f'{age}min her')
    except:return t(False,'Publisher','kein log')
def oll():
    try:urllib.request.urlopen('http://localhost:11434/api/tags',timeout=3);return t(True,'Ollama','up')
    except:return t(False,'Ollama','down')
print('\nJACK SELFTEST ---------------')
rs=[dienste(),ram(),temp(),pub(),oll()]
n=sum(1 for x in rs if x);print(f'-----------------------------\n{n}/{len(rs)}','ALLES OK'if n==len(rs)else'FEHLER - OBEN PRUEFEN')

def run():
    import subprocess as _sp, re as _re
    r = _sp.run(["python3","/data/data/com.termux/files/home/jack/jack_selftest.py"],capture_output=True,text=True,timeout=20)
    return _re.sub(r"\x1b\[[0-9;]*m","",r.stdout).strip()
