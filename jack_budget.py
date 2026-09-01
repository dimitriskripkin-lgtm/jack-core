MODULE_VERSION = 1
#!/usr/bin/env python3
import json, datetime
J="/data/data/com.termux/files/home/jack"
F=J+"/.api_budget"
W=J+"/.api_budget_week"
LIMITS={"text":40,"vision":8}
EUR_WEEK=3.0
EUR_PER_MTOK=0.40
def _load():
    heute=str(datetime.date.today())
    try:
        d=json.load(open(F))
        if d.get("datum")!=heute:
            d={"datum":heute,"text":0,"vision":0,"tokens":0}
    except Exception:
        d={"datum":heute,"text":0,"vision":0,"tokens":0}
    d.setdefault("tokens",0)
    return d
def _week():
    iso=datetime.date.today().isocalendar()
    key="%s-W%02d"%(iso[0],iso[1])
    try:
        w=json.load(open(W))
        if w.get("week")!=key:
            raise ValueError("new")
    except Exception:
        d=_load()
        tok=int(d.get("tokens") or 0)
        w={"week":key,"tokens":tok,"eur":round(tok/1e6*EUR_PER_MTOK,4)}
        json.dump(w,open(W,"w"))
    return w
def week_ok():
    return _week().get("eur",0)<EUR_WEEK
def check_and_count(kind="text"):
    if not week_ok():
        return False, "Wochenlimit 3 EUR"
    d=_load()
    if d.get(kind,0)>=LIMITS.get(kind,40):
        return False, "Tageslimit "+kind
    d[kind]=d.get(kind,0)+1
    if kind=="text" and d[kind]==max(1,int(LIMITS.get(kind,40)*0.8)):
        try:
            import jack_telegram as tg
            msg="Gemini Budget 80 Prozent %s/%s"%(d[kind],LIMITS[kind])
            if hasattr(tg,"send"): tg.send(msg)
            elif hasattr(tg,"send_message"): tg.send_message(msg)
        except Exception:
            pass
    json.dump(d,open(F,"w"))
    return True, "%s %s/%s"%(kind,d[kind],LIMITS[kind])
def add_tokens(n):
    n=int(n or 0)
    d=_load(); d["tokens"]=d.get("tokens",0)+n
    json.dump(d,open(F,"w"))
    w=_week(); w["tokens"]=w.get("tokens",0)+n
    w["eur"]=round(w["tokens"]/1e6*EUR_PER_MTOK,4)
    json.dump(w,open(W,"w"))
def status():
    d=_load(); w=_week()
    return "Heute %s/%s vis %s/%s tok %s eur %.2f/3"%(d.get("text",0),LIMITS["text"],d.get("vision",0),LIMITS["vision"],d.get("tokens",0),w.get("eur",0))
