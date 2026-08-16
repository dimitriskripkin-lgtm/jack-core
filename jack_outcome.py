import json, os, time, subprocess, sys
sys.path.insert(0, os.path.expanduser('~/jack'))

OUTCOMES = ['SUCCESS','PARTIAL','FAILED','ABORTED','UNKNOWN']

def evaluate(plan, results):
    criteria = plan.get('success_criteria', [])
    name = plan.get('name','?')
    total = len(results)
    failed = [r for r in results if 'FEHLER' in str(r.get('r','')) or 'NICHT_GEFUNDEN' in str(r.get('r',''))]
    if not results: return _rec(name,'UNKNOWN','Keine Steps ausgefuehrt',[])
    if not criteria:
        if not failed: return _rec(name,'SUCCESS','Alle Steps rc=0, keine Kriterien definiert',results)
        if len(failed)==total: return _rec(name,'FAILED','Alle Steps fehlgeschlagen',results)
        return _rec(name,'PARTIAL',str(len(failed))+' von '+str(total)+' Steps fehlgeschlagen',results)
    passed=[]
    for c in criteria:
        typ=c.get('type','contains')
        target=c.get('target','')
        value=c.get('value','')
        step_n=c.get('step',None)
        evidence=''
        if step_n is not None:
            r=next((x for x in results if x.get('n')==step_n),None)
            evidence=str(r.get('r','')) if r else ''
        else:
            evidence=' '.join(str(r.get('r','')) for r in results)
        ok=value.lower() in evidence.lower() if typ=='contains' else evidence.strip()==value.strip()
        passed.append({'criterion':c,'ok':ok,'evidence':evidence[:200]})
    all_ok=all(p['ok'] for p in passed)
    any_ok=any(p['ok'] for p in passed)
    outcome='SUCCESS' if all_ok else ('PARTIAL' if any_ok else 'FAILED')
    summary=str(sum(1 for p in passed if p['ok']))+'/'+str(len(passed))+' Kriterien erfuellt'
    return _rec(name,outcome,summary,passed)

def _rec(name,outcome,summary,evidence):
    rec={'mission':name,'outcome':outcome,'summary':summary,'ts':int(time.time()),'evidence':evidence}
    try:
        lf=os.path.expanduser('~/jack/jack_outcomes.jsonl')
        open(lf,'a').write(json.dumps(rec,ensure_ascii=False)+chr(10))
    except Exception: pass
    return rec

def fmt(rec):
    e={'SUCCESS':'OK','PARTIAL':'TEILWEISE','FAILED':'FEHLGESCHLAGEN','ABORTED':'ABGEBROCHEN','UNKNOWN':'UNBEKANNT'}
    return 'MISSION: '+rec.get('mission','?')+chr(10)+'ERGEBNIS: '+e.get(rec.get('outcome','UNKNOWN'),rec.get('outcome','?'))+chr(10)+'DETAILS: '+rec.get('summary','')
