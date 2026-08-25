#!/usr/bin/env python3
import json, os, shutil, sys, time, traceback, subprocess
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
J="/data/data/com.termux/files/home/jack"
P=J+"/missions/pending"
D=J+"/missions/done"
F=J+"/missions/fail"
L=J+"/missions/logs"
STOP=J+"/missions/STOP"
ALLOWED=set(["fact","diag","no_chrome_src","ui_none","classify_is","compile_ok","explain_ok","sv_ok","mtime_fresh","json_valid","no_secret","grep_count","line_check"])
def sh(cmd,t=8):
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=t)
        return r.returncode,(r.stdout or "")+(r.stderr or "")
    except Exception as e:
        return 1,str(e)
def load(path):
    return json.load(open(path,encoding="utf-8"))
def run_act(m):
    act=m.get("act")
    if act not in ALLOWED:
        return False,"act nicht erlaubt: "+str(act),""
    if act=="fact":
        import jack_chat_router as c
        out=c.fact_report() if hasattr(c,"fact_report") else __import__("jack_talk").ist_zustand()
        ok=("SSH" in out) and ("Akku" not in out) and ("CHARGING" not in out)
        return ok,"fact",out[:800]
    if act=="diag":
        import jack_selfsee as s
        out=s.handle(m.get("text") or "analysiere")
        ok=("ESSENZ" in out) and ("google.com" not in out.lower())
        return ok,"diag",out[:800]
    if act=="no_chrome_src":
        t=open(J+"/jack_exec.py",encoding="utf-8",errors="ignore").read()
        bad=[' "such nach"',' "suche nach"',' "such dir"',' "interessiert"']
        hits=[b.strip() for b in bad if b in t]
        return (len(hits)==0),"chrome-src "+(",".join(hits) if hits else "clean"),""
    if act=="ui_none":
        import jack_exec
        out=jack_exec.handle_ui_intent(m.get("text") or "")
        s="" if out is None else str(out)
        ok=(not s.strip()) and ("Forschung" not in s)
        return ok,"ui_none",s[:400] or "None"
    if act=="classify_is":
        import jack_chat_router as c
        got=c.classify(m.get("text") or "")
        want=(m.get("expect") or "").upper()
        return got==want,"got="+str(got)+" want="+want,got
    if act=="compile_ok":
        files=m.get("files") or ["jack_talk.py","jack_telegram.py","jack_chat_router.py","jack_selfsee.py","jack_exec.py"]
        bad=[]
        for n in files:
            rc,o=sh(["python3","-m","py_compile",J+"/"+n],t=12)
            if rc!=0: bad.append(n)
        return (not bad),"compile "+("OK" if not bad else ",".join(bad)),""
    if act=="explain_ok":
        import jack_selfsee as s
        out=s.explain("overmind") or ""
        ok=("overmind" in out.lower()) and ("3" in out)
        return ok,"explain",out[:300]
    if act=="sv_ok":
        name=m.get("svc") or "jack_telegram"
        rc,o=sh(["sv","status", "/data/data/com.termux/files/usr/var/service/"+name],t=8)
        ok=("run:" in o) and ("down:" not in o[:20])
        return ok,"sv "+name,o[:200]
    if act=="mtime_fresh":
        import os,time
        fp=m.get("file","").replace("~",os.environ.get("HOME","/data/data/com.termux/files/home"))
        maxage=int(m.get("max_age_s",3600))
        if not os.path.exists(fp):
            return False,"mtime_fresh: Datei fehlt "+fp,""
        age=int(time.time()-os.path.getmtime(fp))
        return age<=maxage,"mtime_fresh: "+str(age)+"s alt limit "+str(maxage)+"s",""
    if act=="json_valid":
        import json,os
        fp=m.get("file","").replace("~",os.environ.get("HOME","/data/data/com.termux/files/home"))
        fields=m.get("required_fields",[])
        if not os.path.exists(fp):
            return False,"json_valid: Datei fehlt "+fp,""
        try:
            with open(fp) as jf:
                data=json.load(jf)
        except Exception as e:
            return False,"json_valid: parse-Fehler "+str(e),""
        missing=[k for k in fields if k not in data]
        if missing:
            return False,"json_valid: Felder fehlen "+str(missing),""
        return True,"json_valid: ok",""
    if act=="no_secret":
        import os
        fp=m.get("file","").replace("~",os.environ.get("HOME","/data/data/com.termux/files/home"))
        patterns=m.get("patterns",["AIza","sk-","Bearer ","api_key =","token ="])
        if not os.path.exists(fp):
            return False,"no_secret: Datei fehlt "+fp,""
        with open(fp,errors="ignore") as sf:
            text=sf.read()
        hits=[p for p in patterns if p.lower() in text.lower()]
        if hits:
            return False,"no_secret: Treffer "+str(hits),""
        return True,"no_secret: sauber",""
    if act=="grep_count":
        import os
        fp=m.get("file","").replace("~",os.environ.get("HOME","/data/data/com.termux/files/home"))
        pattern=m.get("pattern","")
        expect_max=int(m.get("expect_max",0))
        if not os.path.exists(fp):
            return False,"grep_count: Datei fehlt "+fp,""
        with open(fp,errors="ignore") as gf:
            lines=[l for l in gf.readlines() if pattern in l]
        count=len(lines)
        ok=count<=expect_max
        return ok,"grep_count: "+str(count)+" Treffer (max "+str(expect_max)+")",str(count)
    if act=="line_check":
        import os
        fp=m.get("file","").replace("~",os.environ.get("HOME","/data/data/com.termux/files/home"))
        must_contain=m.get("must_contain","")
        must_not_contain=m.get("must_not_contain","")
        if not os.path.exists(fp):
            return False,"line_check: Datei fehlt "+fp,""
        with open(fp,errors="ignore") as lf:
            text=lf.read()
        if must_contain and must_contain not in text:
            return False,"line_check: fehlt: "+must_contain[:60],""
        if must_not_contain and must_not_contain in text:
            return False,"line_check: verboten da: "+must_not_contain[:60],""
        return True,"line_check: ok",""
    return False,"unbekannt",""
def one(path):
    m=load(path)
    mid=str(m.get("id") or os.path.basename(path))


    rec={"id":mid,"act":m.get("act"),"ts":time.strftime("%Y-%m-%d %H:%M:%S"),"ok":False,"note":"","out":"","expect":m.get("expect","PASS")}
    try:
        ok,note,out=run_act(m)
        rec.update({"ok":ok,"note":note,"out":out})
    except Exception as e:
        rec["note"]="EXC "+type(e).__name__+" "+str(e)[:160]
        rec["out"]=traceback.format_exc()[-400:]
    os.makedirs(L,exist_ok=True)
    json.dump(rec,open(L+"/"+mid+".json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
    dest=D if rec["ok"] else F
    os.makedirs(dest,exist_ok=True)
    shutil.move(path,os.path.join(dest,os.path.basename(path)))
    return rec
def pending_files():
    return sorted(n for n in os.listdir(P) if n.endswith(".json"))
def run_queue(maxn=20):
    n=0; rc=0
    while n<maxn:
        if os.path.isfile(STOP):
            print("STOP-FILE"); break
        files=pending_files()
        if not files:
            print("QUEUE-EMPTY"); break
        rec=one(os.path.join(P,files[0]))
        print(("PASS" if rec["ok"] else "FAIL"), rec["id"], rec["act"], rec["note"])
        print((rec["out"] or "")[:300]); print("---")
        n+=1
        if not rec["ok"] and rec.get("expect","PASS").upper() == "PASS":
            rc=1; break
    return rc
def loop(poll=30, maxn=200):
    while True:
        if os.path.isfile(STOP):
            print("STOP-FILE"); return 0
        if pending_files():
            rc=run_queue(maxn=maxn)
            if rc!=0: return rc
        time.sleep(poll)
if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "once"
    sys.exit(loop() if mode=="loop" else run_queue())
