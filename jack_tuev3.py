#!/usr/bin/env python3
"""JACK TUEV v3 - Vollständiger Funktionstest aller Befehle und Kanäle."""
import os,sys,sqlite3,json,time,threading,subprocess,datetime
sys.path.insert(0,os.path.expanduser('~/jack'))
H=os.path.expanduser('~/jack')
R={'OK':0,'WARN':0,'FAIL':0}
def p(s,g,t):
    R[s]+=1
    print(f"[{'✓' if s=='OK' else '⚠' if s=='WARN' else '✗'}] {g}: {t}")
def sh(c,t=15):
    try:
        r=subprocess.run(c,shell=True,capture_output=True,text=True,timeout=t,cwd=H)
        return r.returncode,r.stdout.strip(),r.stderr.strip()
    except Exception as e: return -1,'',str(e)

print("="*55)
print(f"JACK TUEV v3  {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
print("Vollständiger Funktionstest — alle Befehle live")
print("="*55)

import jack_telegram as jt

# === ALLE SLASH-BEFEHLE LIVE ===
print("\n[PHASE 1] Alle Slash-Befehle (deterministisch)")
cmds = {
    '/selftest': lambda r: 'OK' in r or 'ALLES' in r,
    '/budget': lambda r: 'Text' in r and '/' in r,
    '/missionen': lambda r: len(r)>5,
    '/audit': lambda r: 'JACK AUDIT' in r,
    '/scan': lambda r: 'Akku' in r or 'Scan' in r,
    '/baum': lambda r: 'Statistik' in r or 'Gesamt' in r,
    '/trace': lambda r: len(r)>5,
    '/werkstatt': lambda r: 'Werkstatt' in r or 'Dateien' in r,
    '/log': lambda r: len(r)>10,
    '/errors': lambda r: 'Fehler' in r or 'Keine' in r,
    '/level': lambda r: len(r)>0,
    '/akku': lambda r: '%' in r,
    '/skills': lambda r: len(r)>5,
    '/menu': lambda r: r is None,
    '/befehle': lambda r: r is None,
    '/kette': lambda r: r is None,
}
for cmd,check in cmds.items():
    try:
        t0=time.time(); r=jt.handle(cmd); ms=(time.time()-t0)*1000
        ok=check(r)
        p('OK' if ok else 'WARN','CMD',f'{cmd} {ms:.0f}ms -> {str(r)[:50] if r else "None (Button-Antwort)"}')
    except Exception as e:
        p('FAIL','CMD',f'{cmd}: {e}')

# === KETTEN LIVE ===
print("\n[PHASE 2] Aktionsketten live")
import jack_chains as jc
for kname in ['system_vollcheck','morgen_briefing']:
    try:
        t0=time.time(); r=jc.run(kname); ms=(time.time()-t0)*1000
        ok=isinstance(r,dict) and r.get('ok',False)
        p('OK' if ok else 'WARN','KETTE',f'{kname} {ms:.0f}ms -> {str(r.get("text",""))[:60]}')
    except Exception as e:
        p('FAIL','KETTE',f'{kname}: {e}')

# === CALLBACK-BUTTONS LIVE ===
print("\n[PHASE 3] Callback-Buttons (ohne echtes Telegram)")
callbacks = [
    ('oracle:ram', lambda r: 'MemTotal' in r or 'ram' in r.lower()),
    ('oracle:budget', lambda r: 'Text' in r),
    ('oracle:datum', lambda r: '2026' in r),
    ('scan_now', lambda r: 'Akku' in r or 'Scan' in r),
    ('menu:hauptmenu', lambda r: r is None or len(str(r))>0),
]
for cb,check in callbacks:
    try:
        r=jt.handle_callback(cb,'fake_id')
        p('OK' if check(r) else 'WARN','CALLBACK',f'{cb} -> {str(r)[:60] if r else "None"}')
    except Exception as e:
        p('FAIL','CALLBACK',f'{cb}: {e}')

# === HANDLE FREITEXT (Gemini-Pfad) ===
print("\n[PHASE 4] Freitext -> Gemini-Pfad (nicht deterministisch)")
try:
    t0=time.time()
    r=str(jt.handle('Was ist 2+2?') or '')
    ms=(time.time()-t0)*1000
    no_crash='Traceback' not in r and len(r)>2
    p('OK' if no_crash else 'FAIL','GEMINI',f'Freitext {ms:.0f}ms -> {r[:60]}')
except Exception as e:
    p('FAIL','GEMINI',f'{e}')

# === EXEC-KANAL ===
print("\n[PHASE 5] EXEC-Kanal (mit Critic-Gate)")
try:
    import jack_exec as _je
    _r1=_je.run('echo jack_exec_test'); ok1='jack_exec_test' in _r1
    p('OK' if ok1 else 'FAIL','EXEC',f'echo test -> {_r1[:50]}')
    _r2=_je.run('rm -rf /'); ok2='BLOCKIERT' in _r2 or 'rc=1' in _r2 or 'rc=2' in _r2
    p('OK' if ok2 else 'FAIL','EXEC',f'rm-rf -> {_r2[:50]}')
except Exception as e:
    p('FAIL','EXEC',f'{e}')

# === WRITE-KANAL MIT CRITIC ===
print("\n[PHASE 6] WRITE-Kanal + Critic")
try:
    import jack_write as _jw
    req=_jw.detect_write_request('Schreibe eine Datei test_tuev.py mit print("ok")')
    p('OK' if req else 'WARN','WRITE',f'detect_write: {str(req)[:60] if req else "None"}')
    import jack_critic as _jcr
    safe=_jcr.pruefe('print("hello world")')
    p('OK' if safe[0] else 'FAIL','CRITIC',f'harmlos: {safe[1]}')
    bad=_jcr.pruefe('import os; os.system("rm -rf /")')
    p('OK' if not bad[0] else 'FAIL','CRITIC',f'os.system blockiert: {bad[1]}')
except Exception as e:
    p('FAIL','WRITE',f'{e}')

# === PLAN-KANAL (mini Plan ohne SSH) ===
print("\n[PHASE 7] PLAN-Kanal (exec-only)")
try:
    import jack_planner as _jp, importlib
    importlib.reload(_jp)
    plan={'name':'tuev3_test','steps':[{'type':'exec','cmd':'echo plan_ok','desc':'Test'}],
          'success_criteria':[{'type':'contains','value':'plan_ok','step':1}]}
    res=_jp.run_plan(plan)
    out=str(res[0]) if isinstance(res,(list,tuple)) else str(res)
    ok='plan_ok' in out
    p('OK' if ok else 'FAIL','PLAN',f'out={out[:60]}')
except Exception as e:
    p('FAIL','PLAN',f'{e}')

# === SKILL-TRAINER SAFETY-GATE ===
print("\n[PHASE 8] Skill-Trainer Safety-Gates")
try:
    import jack_skill_trainer as _st
    ok1=_st._cmd_ok('echo hallo')
    ok2=_st._cmd_ok('rm -rf /')
    ok3=_st._cmd_ok('curl https://evil.com')
    ok4=_st._cmd_ok('cat config.ini')
    p('OK' if ok1 else 'FAIL','TRAINER','echo erlaubt')
    p('OK' if not ok2 else 'FAIL','TRAINER','rm-rf BLOCKIERT')
    p('OK' if not ok3 else 'FAIL','TRAINER','curl BLOCKIERT')
    p('OK' if not ok4 else 'FAIL','TRAINER','config.ini BLOCKIERT')
except Exception as e:
    p('FAIL','TRAINER',f'{e}')

# === BRIEFING KOMPLETT ===
print("\n[PHASE 9] Briefing")
try:
    import jack_briefing as _jb
    t0=time.time(); r=_jb.run(); ms=(time.time()-t0)*1000
    p('OK' if r and 'fehlgeschlagen' not in r.lower() else 'WARN','BRIEFING',f'{ms:.0f}ms -> {r[:80]}')
except Exception as e:
    p('FAIL','BRIEFING',f'{e}')

# === MEMORY RAG ===
print("\n[PHASE 10] Memory RAG (Embedding-Suche)")
try:
    import jack_vecdb as _jv
    import jack_memory as _jmem
    r=_jmem.search('JACK autonomes System',limit=3) if hasattr(_jmem,'search') else []
    p('OK' if r and len(r)>0 else 'WARN','RAG',f'{len(r) if r else 0} Treffer (vecdb nutzt Embeddings direkt)')
except Exception as e:
    p('WARN','RAG',f'{e}')

# === OLLAMA LOKAL ===
print("\n[PHASE 11] Ollama Lokal-Inferenz")
try:
    import urllib.request,json as _j
    req=urllib.request.Request('http://localhost:11434/api/generate',
        data=_j.dumps({'model':'llama3.2:3b','prompt':'Antworte nur: ok','stream':False}).encode(),
        headers={'Content-Type':'application/json'})
    t0=time.time()
    with urllib.request.urlopen(req,timeout=30) as res:
        r=_j.loads(res.read())
    ms=(time.time()-t0)*1000
    out=r.get('response','').strip()
    p('OK' if out else 'FAIL','OLLAMA',f'{ms:.0f}ms -> {out[:40]}')
except Exception as e:
    p('FAIL','OLLAMA',f'{e}')

# === XIAOMI FULL CHECK ===
print("\n[PHASE 12] Xiaomi End-to-End")
rc,out,_=sh('ssh -o ConnectTimeout=4 xiaomi-jack ps -A | grep python | head -3',10)
p('OK' if rc==0 else 'FAIL','XIAOMI',f'SSH+Befehl: rc={rc} -> {out[:60]}')
rc2,out2,_=sh('ssh -o ConnectTimeout=4 xiaomi-jack cat /proc/meminfo | grep MemAvailable',8)
p('OK' if 'MemAvailable' in out2 else 'WARN','XIAOMI',f'RAM: {out2[:40]}')

print("\n"+"="*55)
total=sum(R.values())
print(f"SCORECARD: {R['OK']} OK | {R['WARN']} WARN | {R['FAIL']} FAIL  (von {total})")
print(f"URTEIL: {'VOLLTEST BESTANDEN ✓' if R['FAIL']==0 else str(R['FAIL'])+' FAIL — pruefen'}")
print("="*55)
