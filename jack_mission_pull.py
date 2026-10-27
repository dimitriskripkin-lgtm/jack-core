#!/usr/bin/env python3
# JACK_TUNE_BRIDGE
import os,json,shutil,subprocess,time
H="/data/data/com.termux/files/home"
J=H+"/jack/missions"
R=H+"/jack-missions"
MAX=10
OK=set("talk_contract fact diag no_chrome_src classify_is compile_ok explain_ok sv_ok mtime_fresh json_valid no_secret grep_count line_check hb_ok".split())  # JACK_TUNE_PULLSAFE
def pull_allowed(d):
    """Nur strikt lesende Git-Missionen; Runner prueft erneut."""
    try:
        import jack_acts
        if not isinstance(d,dict): return False
        act=d.get("act")
        return (d.get("src")=="git_pull" and d.get("staged") is True
                and d.get("expect","PASS")=="PASS"
                and act in OK and act in jack_acts.ACTS
                and jack_acts.ACTS[act].get("freigabe") is False)
    except Exception:
        return False

def _reject(name, reason):
    """Abgelehnte Git-Dateien als nachvollziehbaren, sicheren Fehlerfall protokollieren."""
    import secrets
    failed=J+"/fail"
    os.makedirs(failed,exist_ok=True)
    mid="git_reject_"+str(int(time.time()))+"_"+secrets.token_hex(5)
    p=os.path.join(failed,mid+".json")
    with open(p+".tmp","w",encoding="utf-8") as f:
        json.dump({"id":mid,"src":"git_pull","act":"pull_rejected",
                   "source_filename":name,"ok":False,
                   "note":"PULL_GESPERRT: "+str(reason)[:120]},f,ensure_ascii=False)
    os.replace(p+".tmp",p)
def git(a,t=30):
    return subprocess.run(["git","-C",R]+a,capture_output=True,text=True,timeout=t)
def cnt(k):
    p=J+"/"+k
    return 0 if not os.path.isdir(p) else sum(x.endswith(".json") for x in os.listdir(p))
def halt():
    if os.path.isfile(J+"/STOP"): return "STOP"
    if cnt("fail"): return "FAIL"
    return ""
def pull():
    # JACK_TUNE_PULLGATE (19.10.2026, Fund ChatGPT Auftrag 4d): Git-Missionen umgingen MCP-Rollen, EXTRAGUARD und Handbuch-Gate
    # (OK-Liste enthielt ui_none/shadow_report mit Wirkung). War nur zufaellig ruhig, weil missions/fail nie leer ist.
    # Gesperrt, bis der Pfad dieselben Pruefungen bekommt. Freischalten nur bewusst: ~/jack/.mission_pull_on
    if not os.path.isfile(H+"/jack/.mission_pull_on"):
        return "PULL_GESPERRT (JACK_TUNE_PULLGATE)"
    w=halt()
    if w: return "HALT "+w
    git(["pull","--ff-only","origin","main"])
    src=R+"/pending"
    if not os.path.isdir(src): return "NO_SRC"
    n=0
    for name in sorted(os.listdir(src)):
        if n>=MAX: break
        if not name.endswith(".json"): continue
        if any(os.path.exists(x) for x in (J+"/pending/"+name,J+"/logs/"+name,J+"/done/"+name,J+"/fail/"+name,J+"/archive/"+name+".fail")): continue
        if os.path.islink(os.path.join(src,name)):
            _reject(name,"Symlink gesperrt")
            continue
        try:
            with open(os.path.join(src,name),encoding="utf-8") as _f:
                d=json.load(_f)
        except Exception:
            _reject(name,"JSON ungueltig")
            continue
        if not pull_allowed(d):
            _reject(name,"Act/Quelle/Stufe/Freigabe nicht erlaubt")
            continue
        target=os.path.join(J,"pending",name)
        tmp=target+".gitpull.tmp"
        with open(tmp,"w",encoding="utf-8") as f:
            json.dump(d,f,ensure_ascii=False,indent=2)
        os.replace(tmp,target)
        n+=1
    return "PULLED "+str(n)
def push_status():
    st={"ts":time.strftime("%Y-%m-%dT%H:%M:%S"),"pending":cnt("pending"),"done":cnt("done"),"fail":cnt("fail")}
    os.makedirs(R+"/status",exist_ok=True)
    open(R+"/status/honor.json","w").write(json.dumps(st))
    git(["add","status/honor.json"])
    if git(["diff","--cached","--quiet"]).returncode==0: return "SKIP"
    git(["commit","-m","status: "+st["ts"]])
    return "PUSH "+str(git(["push","origin","main"],t=40).returncode)
