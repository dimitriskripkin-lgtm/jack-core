import threading, subprocess, datetime, os

def _agent_honor(res):
    try:
        import jack_sensors as _js
        mi=open('/proc/meminfo').read()
        ram=next(int(l.split()[1])//1024 for l in mi.splitlines() if 'MemAvailable' in l)
        tf='/sys/class/thermal/thermal_zone0/temp'
        temp=int(open(tf).read().strip())//1000 if os.path.exists(tf) else 0
        import json as _j2, subprocess as _sp2
        try:
            _b=_j2.loads(_sp2.run(['termux-battery-status'],capture_output=True,text=True,timeout=10).stdout)
            akku=str(_b.get('percentage','?'))+'% '+str(_b.get('status',''))
        except Exception:
            akku='?'
        res['honor']=f"RAM {ram}MB | Temp {temp}C | Akku {akku}"
    except Exception as e:
        res['honor']=f"Fehler: {e}"

def _agent_xiaomi(res):
    try:
        r=subprocess.run(['ssh','xiaomi-jack',
            "free -m|grep Mem|awk '{print $7}'; su -c 'cat /sys/class/power_supply/battery/capacity'; cat /sys/class/thermal/thermal_zone0/temp"],
            capture_output=True,text=True,timeout=12)
        lines=r.stdout.strip().split(chr(10))
        ram=lines[0] if len(lines)>0 else '?'
        akku=lines[1] if len(lines)>1 else '?'
        temp=str(int(lines[2])//1000)+'C' if len(lines)>2 else '?'
        res['xiaomi']=f"RAM {ram}MB | Akku {akku}% | Temp {temp}"
    except Exception as e:
        res['xiaomi']=f"Fehler: {e}"

def _agent_logs(res):
    try:
        lf=os.path.expanduser('~/jack/jack.log')
        lines=open(lf).readlines() if os.path.exists(lf) else []
        errors=[l.strip() for l in lines[-50:] if 'ERROR' in l or 'FEHLER' in l]
        res['logs']=errors[-2:] if errors else ['Keine Fehler']
    except Exception as e:
        res['logs']=[f"Fehler: {e}"]

def _agent_dienste(res):
    try:
        svcs=['jack_telegram','jack_cortex','jack_waechter','ollama']
        stati=[]
        for s in svcs:
            r=subprocess.run(['sv','status',s],capture_output=True,text=True,timeout=3)
            ok='run' in r.stdout
            stati.append(f"{'OK' if ok else 'DOWN'}: {s}")
        res['dienste']=stati
    except Exception as e:
        res['dienste']=[f"Fehler: {e}"]

def run_all():
    res={}
    threads=[
        threading.Thread(target=_agent_honor,args=(res,)),
        threading.Thread(target=_agent_xiaomi,args=(res,)),
        threading.Thread(target=_agent_logs,args=(res,)),
        threading.Thread(target=_agent_dienste,args=(res,)),
    ]
    for t in threads: t.start()
    for t in threads: t.join(timeout=15)
    lines=[
        f"HONOR: {res.get('honor','?')}",
        f"XIAOMI: {res.get('xiaomi','?')}",
        "DIENSTE: " + " | ".join(res.get('dienste',['?'])),
        "LOGS: " + " | ".join(res.get('logs',['?'])),
    ]
    return chr(10).join(lines)

if __name__=='__main__':
    print(run_all())
