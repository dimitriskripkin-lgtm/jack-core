#!/usr/bin/env python3
"""Eine Leitung: FACT / EXPLAIN / DIAG / TALK. Text und Stimme."""
import re, os, sys
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
J="/data/data/com.termux/files/home/jack"
def norm(text):
    t=(text or "").lower()
    for a,b in (("ä","ae"),("ö","oe"),("ü","ue"),("ß","ss")):
        t=t.replace(a,b)
    t=re.sub(r"[^a-z0-9 /]+"," ", t)
    return " ".join(t.split())
def classify(text):
    t=norm(text)
    if not t:
        return "TALK"
    fact=("ist zustand" in t) or t in ("status","/status") or ("kiste" in t and "steht" in t) or t.startswith("wie steht")
    diag=any(k in t for k in ("analysier","essenz","schau dich","schau mal","selbst sehen","eigenen code","eigener code","kompletten code","anomalie","nicht erreichbar","graceful","xiaomi offline","verbesser","murks","fehler","guck dir"))
    expl=("overmind" in t or "deadman" in t) and not fact and not diag
    if fact: return "FACT"
    if expl: return "EXPLAIN"
    if diag: return "DIAG"
    return "TALK"
def dispatch(text, send_keyboard=None):
    lane=classify(text)
    if lane=="FACT":
        return fact_report()
    if lane=="EXPLAIN":
        import jack_selfsee as ss
        return ss.explain(text) or "Overmind-Result ist jack_overmind_result.json. Deadman nach 3h. Nicht Cortex-Uptime."
    if lane=="DIAG":
        import jack_selfsee as ss
        fol=ss.follow(text)
        if fol: return fol
        body=ss.handle(text)
        act=""
        try:
            import json as _j
            act=_j.loads(open("/data/data/com.termux/files/home/jack/.selfsee_pending").read()).get("act") or ""
        except Exception:
            act=""
        if send_keyboard and act and act!="recheck":
            send_keyboard(body, [[("🟢 Ausführen","selfsee_go"),("🔴 Abbrechen","selfsee_no")]])
            return False
        return body
    return None
def lane_from(text):
    t=(text or "").lstrip()
    for k in ("FACT","DIAG","EXPLAIN","TALK"):
        if t.startswith("[[LANE:"+k+"]]"):
            return k
    return None
def strip_lane(text):
    t=(text or "")
    for k in ("FACT","DIAG","EXPLAIN","TALK"):
        tag="[[LANE:"+k+"]]"
        if t.lstrip().startswith(tag):
            return t.lstrip()[len(tag):].lstrip(" \n")
    return t
def fact_report():
    import json, subprocess
    subprocess.run(["python3",J+"/jack_health.py"],capture_output=True,timeout=20)
    h=json.load(open(J+"/jack_health_now.json",encoding="utf-8"))
    t=h.get("tune") or {}
    m=h.get("marks") or {}
    hb=h.get("heartbeats") or {}
    a=["Ist-Zustand:","SSH Xiaomi: "+str(h.get("ssh_xiaomi")),"Focus "+str(t.get("focus_sleep_s"))+"s, Genesis "+str(t.get("genesis_skip"))+", Idle "+str(t.get("autolearn_idle_s"))+"s","Marks: "+", ".join((k+":ja" if v else k+":nein") for k,v in m.items()),"Beats: "+", ".join(k+" "+str(v)+"s" for k,v in hb.items()),"Git-Push: tot."]
    return chr(10).join(a)
def dispatch_lane(lane, text):
    if lane=="FACT":
        return fact_report()
    if lane=="EXPLAIN":
        return explain_overmind()
    if lane=="DIAG":
        import jack_selfsee as ss
        return ss.handle(text or "")
    return None
def explain_overmind():
    import jack_selfsee as ss
    return ss.explain("overmind") or "Overmind-Result ist jack_overmind_result.json. Deadman nach 3h."
def apply_lane(llm_text, user_text):
    lane=lane_from(llm_text)
    if not lane:
        t=norm(user_text)
        lastp=J+"/.chat_lane"
        if os.path.isfile(lastp) and any(w in t for w in ("ergebnis","gefunden","weiter so","und dann")):
            try: lane=open(lastp).read().strip()
            except Exception: lane=None
    if lane in ("FACT","DIAG","EXPLAIN"):
        try: open(J+"/.chat_lane","w").write(lane)
        except Exception: pass
        d=dispatch_lane(lane, user_text)
        if d: return d
    else:
        try: os.remove(J+"/.chat_lane")
        except Exception: pass
    return strip_lane(llm_text or "")
