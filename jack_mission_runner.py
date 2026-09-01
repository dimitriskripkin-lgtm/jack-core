#!/usr/bin/env python3
MODULE_VERSION = 1
import json, os, shutil, sys, time, traceback, subprocess
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
J="/data/data/com.termux/files/home/jack"
V="/data/data/com.termux/files/usr/var/service"
P=J+"/missions/pending"
D=J+"/missions/done"
F=J+"/missions/fail"
L=J+"/missions/logs"
STOP=J+"/missions/STOP"
ALLOWED=set(["shadow_report","talk_contract","fact","diag","no_chrome_src","ui_none","classify_is","compile_ok","explain_ok","sv_ok","mtime_fresh","json_valid","no_secret","grep_count","line_check","hb_ok","file_exists","line_count","sed_replace","py_replace"])
def sh(cmd,t=8):
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=t)
        return r.returncode,(r.stdout or "")+(r.stderr or "")
    except Exception as e:
        return 1,str(e)
def load(path):
    return json.load(open(path,encoding="utf-8"))

def _run_fix_shadow(m, fp, content, bak):
    """Fix in shadow/ anwenden, 3x verifizieren, dann wartet_freigabe."""
    import os, shutil, subprocess, json, time
    J = "/data/data/com.termux/files/home/jack"
    SHADOW = os.path.join(J, "shadow")
    APPROVALS = os.path.join(J, "pending_approvals.json")
    os.makedirs(SHADOW, exist_ok=True)

    fname = os.path.basename(fp)
    staged = os.path.join(SHADOW, fname + ".staged")
    shutil.copy2(fp, staged)

    old = m.get("old",""); new = m.get("new","")
    staged_content = open(staged, errors="ignore").read()
    if old not in staged_content:
        return False, "shadow: old nicht gefunden: " + old[:40]

    staged_content = staged_content.replace(old, new, 1)
    open(staged, "w").write(staged_content)

    # 3x verifizieren
    for attempt in range(3):
        if fp.endswith(".py"):
            rc, out = sh(["python3", "-m", "py_compile", staged], t=10)
            if rc != 0:
                os.remove(staged)
                return False, f"shadow py_compile FAIL attempt {attempt+1}: " + out[:60]
        verify_act = m.get("verify_act")
        if verify_act:
            vm = {"act": verify_act,
                  "file": "~/" + os.path.relpath(staged, os.path.expanduser("~")),
                  "pattern": m.get("verify_pattern",""),
                  "expect_max": m.get("verify_expect_max", 0)}
            vm["file"] = staged
            vok, vinfo, _ = run_act(vm)
            if not vok:
                os.remove(staged)
                return False, f"shadow verify FAIL attempt {attempt+1}: " + vinfo

    # Alle 3 grün — Freigabe ausstehend
    approval = {
        "id": m.get("id","?"),
        "file": fp,
        "staged": staged,
        "what": str(old[:50]) + " -> " + str(new[:30]),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "status": "wartet_freigabe"
    }
    approvals = []
    if os.path.exists(APPROVALS):
        try: approvals = json.load(open(APPROVALS))
        except Exception: approvals = []
    # Deduplizieren + veraltete staged-Dateien entfernen
    approvals = [a for a in approvals if a.get("id") != approval["id"] and os.path.exists(a.get("staged",""))]
    approvals.append(approval)
    json.dump(approvals, open(APPROVALS,"w"), indent=2, ensure_ascii=False)

    # Telegram-Notify mit Buttons
    try:
        import jack_keyboards as _jk, jack_telegram as _jt
        kb = _jk.build_approval_keyboard(m.get("id","?"), fname, old[:40]+" -> "+new[:30])
        msg = f"🔧 Fix bereit: {fname}\nWas: {old[:40]}\n→ {new[:30]}\n3x verifiziert ✓"
        _jt.send_with_keyboard(msg, kb)
    except Exception as _ne:
        try:
            import jack_notify as _jn
            _jn.notify(f"🔧 Fix bereit: {fname} | /approve_{m.get('id','?')} | /reject_{m.get('id','?')}")
        except Exception: pass

    return True, f"shadow: wartet_freigabe — {fname}.staged"

def run_act(m):
    act=m.get("act")
    if act not in ALLOWED:
        return False,"act nicht erlaubt: "+str(act),""

    if act in ("sed_replace","py_replace"):
        import os, shutil, subprocess
        HOME=os.environ.get("HOME","/data/data/com.termux/files/home")
        fp=m.get("file","").replace("~",HOME)
        if not fp.startswith(J):
            return False,"fix: Pfad-Tabu",""
        if not os.path.exists(fp):
            return False,"fix: Datei fehlt "+fp,""
        old=m.get("old",""); new=m.get("new","")
        if not old:
            return False,"fix: old fehlt",""
        content=open(fp,errors="ignore").read()

        # Shadow-Modus wenn staged=True
        if m.get("staged") or m.get("shadow"):
            ok2, info2 = _run_fix_shadow(m, fp, content, bak=None)
            return ok2, info2, ""

        if old not in content:
            return False,"fix: old nicht gefunden: "+old[:40],""


        bak=fp+".fix.bak"
        shutil.copy2(fp,bak)
        try:
            count=content.count(old)
            content=content.replace(old,new,1)
            open(fp,"w").write(content)
            if fp.endswith(".py"):
                rc,out=sh(["python3","-m","py_compile",fp],t=10)
                if rc!=0:
                    shutil.copy2(bak,fp); os.remove(bak)
                    return False,"fix: py_compile FAIL Rollback: "+out[:60],""
            verify_act=m.get("verify_act")
            if verify_act:
                vm={"act":verify_act,"file":m.get("file",""),"pattern":m.get("verify_pattern",""),"expect_max":m.get("verify_expect_max",0)}
                vok,vinfo,_=run_act(vm)
                if not vok:
                    shutil.copy2(bak,fp); os.remove(bak)
                    return False,"fix: verify FAIL Rollback: "+vinfo,""
            os.remove(bak)
            return True,"fix OK "+str(count)+"x: "+old[:30]+" -> "+new[:20],""
        except Exception as e:
            try: shutil.copy2(bak,fp); os.remove(bak)
            except Exception: pass
            return False,"fix Exception Rollback: "+str(e)[:80],""

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
        name=m.get("service") or m.get("svc") or m.get("name") or "jack_telegram"
        rc,o=sh(["sv","status", "/data/data/com.termux/files/usr/var/service/"+name],t=8)
        ok=("run:" in o) and ("down:" not in o[:20])
        return ok,"sv "+name,o[:200]

    if act=="hb_ok":
        import os, time
        name=m.get("service") or m.get("svc") or "jack_telegram"
        if not name.startswith("jack_"):
            name="jack_"+name
        cands=[
            "/data/data/com.termux/files/home/.heartbeat_"+name,
            "/data/data/com.termux/files/home/jack/.heartbeat_"+name,
        ]
        fp=None
        for c in cands:
            if os.path.isfile(c):
                fp=c; break
        maxage=int(m.get("max_age_s",600))
        if not fp:
            return False,"hb_ok: fehlt "+",".join(cands),""
        age=int(time.time()-os.path.getmtime(fp))
        ok=age<=maxage
        return ok,"hb_ok "+name+" "+str(age)+"s",str(age)

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
        expect_max=m.get("expect_max",None)
        expect_min=m.get("expect_min",None)
        if not os.path.exists(fp):
            return False,"grep_count: Datei fehlt "+fp,""
        with open(fp,errors="ignore") as gf:
            lines=[l for l in gf.readlines() if pattern in l]
        count=len(lines)
        if expect_min is not None:
            ok=count>=int(expect_min)
            return ok,f"grep_count: {count} Treffer (min {expect_min})",str(count)
        ok=count<=int(expect_max if expect_max is not None else 0)
        return ok,"grep_count: "+str(count)+" Treffer (max "+str(expect_max if expect_max is not None else 0)+")",str(count)
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
    if act=="talk_contract":
        import jack_talk_contract as tc
        rs=tc.rows(40)
        bad=[r for r in rs if tc.score(r.get("j",""))]
        mx=int(m.get("max_breaches",0))
        ok=len(bad)<=mx
        return ok,"talk_contract breaches "+str(len(bad))+"/"+str(len(rs))+" max "+str(mx),str(len(bad))
    if act=="shadow_report":
        import json as _j, os as _o, time as _t, subprocess as _sp
        dest=_o.path.join(J,"shadow", _o.path.basename(str(m.get("file") or "report.json")))
        if not dest.endswith((".json",".md")): return False,"shadow: bad name",""
        sv=_sp.run(["sv","status",V+"/jack_telegram"],capture_output=True,text=True,timeout=5)
        rec={"ts":_t.strftime("%Y-%m-%d %H:%M:%S"),"host":"HONOR","ssh_note":"not probed here","sv_telegram":(sv.stdout or "")[:80],"next":"propose only in shadow","rule":"no live rewrite"}
        _o.makedirs(_o.path.dirname(dest),exist_ok=True)
        open(dest,"w",encoding="utf-8").write(_j.dumps(rec,ensure_ascii=False,indent=2))
        md=dest.rsplit(".",1)[0]+".md"
        open(md,"w",encoding="utf-8").write("# shadow 220\nNur NebenDatei. Kein Live-Write.\n"+rec["ts"]+"\n")
        return True,"shadow_report "+dest,dest
    if act=="file_exists":
        import os
        fp=m.get("file","").replace(chr(126),os.environ.get("HOME","/data/data/com.termux/files/home"))
        ok=os.path.isfile(fp)
        return ok,"file_exists "+fp+" "+("yes" if ok else "no"),""
    if act=="line_count":
        import os
        fp=m.get("file","").replace(chr(126),os.environ.get("HOME","/data/data/com.termux/files/home"))
        if not os.path.exists(fp):
            return False,"line_count: Datei fehlt "+fp,""
        n=sum(1 for _ in open(fp,errors="ignore"))
        mn=m.get("expect_min"); mx=m.get("expect_max"); ex=m.get("expect_n")
        ok=True
        if mn is not None: ok=ok and n>=int(mn)
        if mx is not None: ok=ok and n<=int(mx)
        if ex is not None: ok=ok and n==int(ex)
        return ok,"line_count "+str(n)+" min="+str(mn)+" max="+str(mx)+" n="+str(ex),str(n)
    return False,"unbekannt",""

def one(path):
    _hb()
    m=load(path)
    mid=str(m.get("id") or os.path.basename(path))
    # dedup: schon erledigt -> pending entfernen, nicht nochmal
    for _d in (D,F):
        _p=os.path.join(_d, os.path.basename(path))
        _p2=os.path.join(_d, mid+".json")
        if os.path.isfile(_p) or os.path.isfile(_p2):
            try: os.remove(path)
            except Exception: pass
            return {"id":mid,"act":m.get("act"),"ok":True,"note":"SKIP-DEDUP already in "+_d,"out":"","expect":m.get("expect","PASS")}


    rec={"id":mid,"act":m.get("act"),"ts":time.strftime("%Y-%m-%d %H:%M:%S"),"ok":False,"note":"","out":"","expect":m.get("expect","PASS")}
    try:
        ok,note,out=run_act(m)
        rec.update({"ok":ok,"note":note,"out":out})
    except Exception as e:
        rec["note"]="EXC "+type(e).__name__+" "+str(e)[:160]
        rec["out"]=traceback.format_exc()[-400:]
    want=(m.get("expect") or "PASS").upper()
    rec["expect"]=want
    raw=bool(rec.get("ok"))
    rec["raw_ok"]=raw
    if str(rec.get("note","")).startswith("EXC"):
        rec["ok"]=False
    elif want=="FAIL":
        rec["ok"]=not raw
    else:
        rec["ok"]=raw
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
        if not rec["ok"]:
            rc=1; break
    return rc
def _hb():
    try:
        open("/data/data/com.termux/files/home/jack/.heartbeat_jack_missions","w").write(str(time.time()))
    except Exception:
        pass
def loop(poll=30, maxn=200):
    while True:
        _hb()
        if os.path.isfile(STOP):
            print("STOP-FILE"); return 0
        try:
            import importlib as _il, jack_mission_pull as _jp
            _il.reload(_jp)
            print(_jp.pull())
            print(_jp.push_status())
        except Exception as _e:
            print("PULL-SKIP",type(_e).__name__)
        # JACK_TUNE_BRIDGEHOOK
        if pending_files():
            rc=run_queue(maxn=maxn)
            if rc!=0: return rc
        time.sleep(poll)
if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "once"
    sys.exit(loop() if mode=="loop" else run_queue())
