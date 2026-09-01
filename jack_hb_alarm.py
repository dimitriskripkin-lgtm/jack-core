MODULE_VERSION = 1
import json, os, time
J = "/data/data/com.termux/files/home/jack"
F = J + "/hb_fail_state.json"
N, COOL = 3, 600
def _load():
    try:
        d=json.load(open(F,encoding="utf-8"))
        return d if isinstance(d,dict) else {}
    except Exception:
        return {}
def _save(d):
    open(F,"w",encoding="utf-8").write(json.dumps(d))
def record(svc, ok):
    d=_load(); s=d.setdefault(str(svc), {"fail":0,"last_alarm":0})
    if ok:
        s["fail"]=0; _save(d); return False
    s["fail"]=int(s.get("fail") or 0)+1
    now=time.time(); fired=False
    if s["fail"]>=N and now-float(s.get("last_alarm") or 0)>=COOL:
        s["last_alarm"]=now; fired=True
        try:
            import jack_telegram as tg
            msg="Heartbeat 3x rot: "+str(svc)
            if hasattr(tg,"send"): tg.send(msg)
            elif hasattr(tg,"send_message"): tg.send_message(msg)
        except Exception:
            pass
    _save(d); 
    try:
        if str(svc)=="xiaomi":
            import jack_degraded as _dg
            _dg.set_on(int(s.get("fail") or 0)>=3)
        import jack_quota as _q; _q.maybe()
    except Exception:
        pass
    return fired
