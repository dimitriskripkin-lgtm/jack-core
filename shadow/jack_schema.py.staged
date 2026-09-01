import json

REQUIRED=['steps']
VALID_TYPES=['exec','tap','find_and_tap','open_app','keyevent','wait','ui_check','home','input_text','ui_text','chrome_search']

def validate(raw):
    try:
        if isinstance(raw,str):
            raw=raw.strip()
            i=raw.find('{')
            j=raw.rfind('}')
            if i>=0 and j>i: raw=raw[i:j+1]
            plan=json.loads(raw)
        else:
            plan=raw
    except Exception as e:
        return None,'JSON-Fehler: '+str(e)[:100]
    if not isinstance(plan,dict):
        return None,'Plan muss ein Dict sein'
    if 'steps' not in plan:
        return None,'steps fehlt'
    if not isinstance(plan['steps'],list) or len(plan['steps'])==0:
        return None,'steps muss eine nicht-leere Liste sein'
    for i,s in enumerate(plan['steps']):
        if 'type' not in s:
            return None,'Step '+str(i+1)+' hat kein type-Feld'
        if s['type'] not in VALID_TYPES:
            return None,'Unbekannter Step-Typ: '+s['type']
    return plan,'OK'
