import urllib.request,json,os,time,threading
INBOX='https://raw.githubusercontent.com/dimitriskripkin-lgtm/jack-core/master/jack_inbox.json'
_last_ts=None

def poll_inbox(send_fn=None):
    global _last_ts
    try:
        with urllib.request.urlopen(INBOX+'?t='+str(int(time.time())),timeout=8) as r:
            d=json.loads(r.read())
        ts=d.get('ts',0)
        if ts and ts!=_last_ts:
            _last_ts=ts
            plan=d.get('plan')
            if plan and send_fn:
                import jack_planner,importlib
                importlib.reload(jack_planner)
                threading.Thread(target=jack_planner.run_plan,args=(plan,send_fn),daemon=True).start()
    except Exception as e:
        pass

def start_inbox_poller(send_fn):
    def loop():
        while True:
            try: poll_inbox(send_fn)
            except Exception: pass
            time.sleep(60)
    threading.Thread(target=loop,daemon=True).start()
