import urllib.request,json,os,time,threading

def _cfg():
    import configparser
    c=configparser.ConfigParser()
    c.read(os.path.expanduser('~/jack/config.ini'))
    return c

def _token():
    return _cfg().get('GITHUB','token',fallback='').strip()

def _repo():
    return _cfg().get('GITHUB','repo',fallback='dimitriskripkin-lgtm/jack-core').strip()

INBOX_FILE='jack_inbox.json'
RAW='https://raw.githubusercontent.com/'+_repo()+'/master/'+INBOX_FILE
_last_ts=None

def push_plan(plan,name='Claude-Plan'):
    import base64
    plan['name']=name
    payload={'ts':int(time.time()),'plan':plan}
    content=json.dumps(payload,ensure_ascii=False,indent=2).encode()
    b64=base64.b64encode(content).decode()
    api='https://api.github.com/repos/'+_repo()+'/contents/'+INBOX_FILE
    tok=_token()
    hdrs={'Authorization':'token '+tok,'User-Agent':'jack','Content-Type':'application/json'}
    try:
        req=urllib.request.Request(api,headers=hdrs)
        with urllib.request.urlopen(req,timeout=8) as r:
            sha=json.loads(r.read()).get('sha','')
    except: sha=''
    body=json.dumps({'message':'inbox: '+name,'content':b64,'sha':sha,'branch':'master'}).encode()
    req2=urllib.request.Request(api,data=body,headers=hdrs,method='PUT')
    try:
        with urllib.request.urlopen(req2,timeout=10) as r:
            return 'PUSH OK: '+name
    except Exception as e:
        return 'PUSH FEHLER: '+str(e)[:150]

def poll_inbox(send_fn=None):
    global _last_ts
    try:
        import base64
        api='https://api.github.com/repos/'+_repo()+'/contents/jack_inbox.json'
        hdrs={'Authorization':'token '+_token(),'User-Agent':'jack'}
        req=urllib.request.Request(api,headers=hdrs)
        with urllib.request.urlopen(req,timeout=8) as r:
            raw=json.loads(r.read())
            d=json.loads(base64.b64decode(raw['content']).decode())
        ts=d.get('ts',0)
        if ts and ts!=_last_ts:
            _last_ts=ts
            plan=d.get('plan')
            if plan and send_fn:
                import jack_planner,importlib
                importlib.reload(jack_planner)
                threading.Thread(target=jack_planner.run_plan,args=(plan,send_fn),daemon=True).start()
    except Exception: pass

def start_inbox_poller(send_fn):
    def loop():
        while True:
            try: poll_inbox(send_fn)
            except Exception: pass
            time.sleep(60)
    threading.Thread(target=loop,daemon=True).start()
