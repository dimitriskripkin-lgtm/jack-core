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
import jack_acts as _acts  # JACK_TUNE_ACTS
ALLOWED=set(_acts.names())
def sh(cmd,t=8):
    try:
        r=subprocess.run(cmd,capture_output=True,text=True,timeout=min(60,int(t) if t else 60))
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
        import hashlib as _hl  # JACK_TUNE_HASHCHECK
        for _k,_v in (("sha256_old",old),("sha256_new",new)):
            if m.get(_k) and _hl.sha256(_v.encode("utf-8")).hexdigest()!=str(m.get(_k)).lower():
                return False,"fix: "+_k+" passt nicht - Transport beschaedigt, nichts geschrieben",""
        content=open(fp,errors="ignore").read()

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

    if act=="batch":
        steps=m.get("steps",[])
        if not isinstance(steps,list) or not steps:
            return False,"batch: steps fehlt oder leer",""
        results=[]
        all_ok=True
        for i,step in enumerate(steps):
            if not isinstance(step,dict) or "act" not in step:
                results.append(str(i)+": ungueltiger step"); all_ok=False; break
            sok,snote,sout=run_act(step)
            results.append(str(i)+" "+step.get("act","?")+": "+("OK" if sok else "FAIL")+" "+snote[:80])
            if not sok and not step.get("continue_on_fail"):
                all_ok=False
                break
            if not sok:
                all_ok=False
        return all_ok,"batch("+str(len(results))+"/"+str(len(steps))+"): "+" | ".join(results)[:400],""

    if act=="file_create":
        import os
        HOME=os.environ.get("HOME","/data/data/com.termux/files/home")
        fp=m.get("file","").replace("~",HOME)
        if not fp.startswith(J):
            return False,"file_create: Pfad-Tabu",""
        if os.path.exists(fp):
            return False,"file_create: Datei existiert schon, nutze sed_replace/py_replace",""
        content=m.get("content","")
        import hashlib as _hl  # JACK_TUNE_HASHCHECK
        _want=str(m.get("sha256","")).lower()
        if _want and _hl.sha256(content.encode("utf-8")).hexdigest()!=_want:
            return False,"file_create: sha256 passt nicht - Transport beschaedigt, nichts geschrieben",""
        os.makedirs(os.path.dirname(fp),exist_ok=True)
        open(fp,"w",encoding="utf-8").write(content)
        if _want and _hl.sha256(open(fp,"rb").read()).hexdigest()!=_want:
            os.remove(fp)
            return False,"file_create: sha256 nach Schreiben falsch - Datei entfernt",""
        if fp.endswith(".py"):
            rc,out=sh(["python3","-m","py_compile",fp],t=10)
            if rc!=0:
                os.remove(fp)
                return False,"file_create: py_compile FAIL, geloescht: "+out[:60],""
        return True,"file_create: "+fp+" angelegt ("+str(len(content))+" Zeichen)",""

    if act=="file_delete":
        import os, shutil, time as _t
        HOME=os.environ.get("HOME","/data/data/com.termux/files/home")
        fp=m.get("file","").replace("~",HOME)
        if not fp.startswith(J):
            return False,"file_delete: Pfad-Tabu",""
        if not os.path.exists(fp):
            return False,"file_delete: Datei existiert nicht",""
        attic=J+"/Attic"
        os.makedirs(attic,exist_ok=True)
        stamp=_t.strftime("%Y%m%d_%H%M%S")
        dest=os.path.join(attic,os.path.basename(fp)+"_"+stamp)
        shutil.move(fp,dest)
        return True,"file_delete: "+fp+" ins Attic verschoben nach "+dest,""

    if act=="open_url_xiaomi":
        import re, subprocess
        url=m.get("url","")
        if not re.match(r"^https?://[a-zA-Z0-9._\-/?=&%#]+$", url):
            return False,"open_url_xiaomi: ungueltige URL",""
        try:
            r=subprocess.run(["ssh","xiaomi-jack","su","-c","am start -a android.intent.action.VIEW -d \'"+url+"\'"],capture_output=True,text=True,timeout=15)
            if r.returncode!=0:
                return False,"open_url_xiaomi: SSH/am-Fehler: "+r.stderr[:100],""
            return True,"open_url_xiaomi: geoeffnet: "+url,""
        except Exception as e:
            return False,"open_url_xiaomi: "+str(e)[:100],""

    if act=="xiaomi_battery":
        import subprocess
        try:
            r=subprocess.run(["ssh","xiaomi-jack","termux-battery-status"],capture_output=True,text=True,timeout=15)
            if r.returncode!=0:
                return False,"xiaomi_battery: SSH-Fehler: "+r.stderr[:100],""
            return True,"xiaomi_battery: ok",r.stdout[:300]
        except Exception as e:
            return False,"xiaomi_battery: "+str(e)[:100],""

    if act=="xiaomi_ollama_restart":
        import subprocess, time as _tro, os as _oso
        _svd="/data/data/com.termux/files/usr/var/service/ollama"
        try:
            r=subprocess.run(["ssh","xiaomi-jack","rm -f "+_svd+"/down; sv up "+_svd+" 2>&1; sv status "+_svd+" 2>&1"],capture_output=True,text=True,timeout=25)
            _erreichbar=False
            for _i in range(10):
                _tro.sleep(2)
                _pc=subprocess.run(["ssh","xiaomi-jack","curl","-s","-m","3","http://127.0.0.1:11434/api/tags"],capture_output=True,text=True,timeout=10)
                if _pc.returncode==0 and _pc.stdout.strip().startswith("{"):
                    _erreichbar=True
                    break
            _note="xiaomi_ollama_restart: "+("erreichbar (sv up)" if _erreichbar else "NICHT erreichbar nach sv up")
            if _erreichbar:
                _lk=J+"/.ollama_lock"
                if _oso.path.isfile(_lk):
                    try:
                        _oso.rename(_lk,_lk+".session"); _note+=" (Lock fuer Sitzung aufgehoben)"
                    except Exception:
                        pass
                try:
                    _mins=int(m.get("auto_off_min",20) or 0)
                except Exception:
                    _mins=20
                if _mins>0:
                    _q=chr(34); _s=chr(39)
                    _sid=str(int(_tro.time()))
                    open(J+"/.ollama_session","w").write(_sid)
                    _cmd=("sleep "+str(_mins*60)+"; [ "+_q+"$(cat "+J+"/.ollama_session 2>/dev/null)"+_q+" = "+_q+_sid+_q+" ] || exit 0; "
                          "ssh xiaomi-jack "+_s+"touch "+_svd+"/down; sv down "+_svd+_s+"; "
                          "if [ -f "+_lk+".session ] && [ ! -f "+_lk+" ]; then mv "+_lk+".session "+_lk+"; fi; rm -f "+J+"/.ollama_session")
                    subprocess.Popen(["sh","-c",_cmd],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    _note+=" (Auto-Aus in "+str(_mins)+" Min)"
            else:
                _note+=" | "+(r.stdout+r.stderr)[:200].replace(chr(10)," / ")
            return _erreichbar,_note,""
        except Exception as e:
            return False,"xiaomi_ollama_restart: "+str(e)[:100],""

    if act=="xiaomi_ollama_stop":
        import subprocess, time as _tos, os as _oso
        _svd="/data/data/com.termux/files/usr/var/service/ollama"
        try:
            r=subprocess.run(["ssh","xiaomi-jack","touch "+_svd+"/down; sv down "+_svd+" 2>&1; pkill -x llama-server; true"],capture_output=True,text=True,timeout=25)
            _still=False
            for _i in range(5):
                _tos.sleep(2)
                _c=subprocess.run(["ssh","xiaomi-jack","curl","-s","-m","3","http://127.0.0.1:11434/api/tags"],capture_output=True,text=True,timeout=10)
                _still = _c.returncode==0 and _c.stdout.strip().startswith("{")
                if not _still:
                    break
            if _still:
                return False,"xiaomi_ollama_stop: Ollama antwortet noch nach sv down | "+(r.stdout+r.stderr)[:150].replace(chr(10)," / "),""
            _lk=J+"/.ollama_lock"
            try:
                if _oso.path.isfile(_lk+".session") and not _oso.path.isfile(_lk):
                    _oso.rename(_lk+".session",_lk)
                elif not _oso.path.isfile(_lk):
                    open(_lk,"w").write("Ollama default AUS (Standard, nach Sitzungsende wiederhergestellt)")
                if _oso.path.isfile(J+"/.ollama_session"):
                    _oso.remove(J+"/.ollama_session")
            except Exception:
                pass
            return True,"xiaomi_ollama_stop: Ollama aus (sv down + down-Datei), Standard-Lock aktiv",""
        except Exception as e:
            return False,"xiaomi_ollama_stop: "+str(e)[:100],""

    if act=="xiaomi_ollama_restart_v1":
        import subprocess, time as _tro
        try:
            r=subprocess.run(["ssh","xiaomi-jack","pkill -x ollama; sleep 1; setsid nohup ollama serve > $HOME/ollama_start.log 2>&1 < /dev/null &"],capture_output=True,text=True,timeout=20)
            for _i in range(10):
                _tro.sleep(2)
                _pc=subprocess.run(["ssh","xiaomi-jack","curl","-s","-m","3","http://127.0.0.1:11434/api/tags"],capture_output=True,text=True,timeout=10)
                if _pc.returncode==0 and _pc.stdout.strip().startswith("{"):
                    break
            _chk=subprocess.run(["ssh","xiaomi-jack","curl","-s","-m","5","http://127.0.0.1:11434/api/tags"],capture_output=True,text=True,timeout=12)
            _erreichbar = _chk.returncode==0 and ("models" in (_chk.stdout or "") or _chk.stdout.strip().startswith("{"))
            _note = "xiaomi_ollama_restart: "+("erreichbar nach Neustart" if _erreichbar else "NICHT erreichbar nach Neustart-Versuch")
            if _erreichbar:
                import os as _oso
                _lk=J+"/.ollama_lock"
                if _oso.path.isfile(_lk):
                    try:
                        _oso.rename(_lk,_lk+".session"); _note+=" (Lock fuer Sitzung aufgehoben)"
                    except Exception:
                        pass
                try:
                    _mins=int(m.get("auto_off_min",20) or 0)
                except Exception:
                    _mins=20
                if _mins>0:
                    _q=chr(34); _s=chr(39)
                    _sid=str(int(_tro.time()))
                    open(J+"/.ollama_session","w").write(_sid)
                    _cmd=("sleep "+str(_mins*60)+"; [ "+_q+"$(cat "+J+"/.ollama_session 2>/dev/null)"+_q+" = "+_q+_sid+_q+" ] || exit 0; "
                          "ssh xiaomi-jack "+_s+"pkill -x ollama; pkill -x llama-server; true"+_s+"; "
                          "if [ -f "+_lk+".session ] && [ ! -f "+_lk+" ]; then mv "+_lk+".session "+_lk+"; fi; rm -f "+J+"/.ollama_session")
                    subprocess.Popen(["sh","-c",_cmd],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    _note+=" (Auto-Aus in "+str(_mins)+" Min)"
            _tail=""
            if not _erreichbar:
                try:
                    _tl=subprocess.run(["ssh","xiaomi-jack","tail -6 $HOME/ollama_start.log 2>&1"],capture_output=True,text=True,timeout=10)
                    _tail=" | LOG: "+(_tl.stdout or _tl.stderr)[:300].replace(chr(10)," / ")
                except Exception:
                    pass
            return _erreichbar, _note+_tail, (r.stdout[:150]+r.stderr[:100])
        except Exception as e:
            return False,"xiaomi_ollama_restart: "+str(e)[:100],""

    if act=="xiaomi_ssh_check":
        import subprocess, time as _tm2
        t0=_tm2.time()
        try:
            r=subprocess.run(["ssh","-o","ConnectTimeout=5","xiaomi-jack","echo","ok"],capture_output=True,text=True,timeout=10)
            dt=round(_tm2.time()-t0,2)
            if r.returncode==0 and "ok" in r.stdout:
                return True,"xiaomi_ssh_check: erreichbar in "+str(dt)+"s",""
            return False,"xiaomi_ssh_check: nicht erreichbar: "+r.stderr[:80],""
        except Exception as e:
            return False,"xiaomi_ssh_check: "+str(e)[:100],""

    if act=="create_demo_file":
        import os, re
        DOWNLOADS="/storage/emulated/0/Download"
        name=m.get("name","")
        if not re.match(r"^jack_demo_[a-zA-Z0-9_\-]+\.txt$", name):
            return False,"create_demo_file: Name muss jack_demo_*.txt sein",""
        fp=os.path.join(DOWNLOADS, name)
        if os.path.exists(fp):
            return False,"create_demo_file: Datei existiert schon: "+name,""
        content=m.get("content","")[:2000]
        try:
            os.makedirs(DOWNLOADS, exist_ok=True)
            with open(fp,"w") as f:
                f.write(content)
            return True,"create_demo_file: "+fp+" angelegt ("+str(len(content))+" Zeichen)",""
        except Exception as e:
            return False,"create_demo_file: "+str(e)[:100],""

    if act=="spotify_play_xiaomi":
        try:
            import jack_ui_type as _ut
            try:
                import jack_xiaomi_unlock as _xu
                _xu.ensure_unlocked()  # JACK_TUNE_UNLOCK_FIRST
            except Exception: pass
            q=m.get("query","")
            if not q:
                return False,"spotify_play_xiaomi: query fehlt",""
            ok,msg=_ut.spotify_play(q)
            return ok,"spotify_play_xiaomi: "+str(msg)[:180],""
        except Exception as e:
            return False,"spotify_play_xiaomi: "+str(e)[:100],""

    if act=="chrome_search_xiaomi":
        try:
            import jack_ui_type as _ut
            try:
                import jack_xiaomi_unlock as _xu
                _xu.ensure_unlocked()
            except Exception: pass
            q=m.get("query","")
            if not q:
                return False,"chrome_search_xiaomi: query fehlt",""
            ok,msg=_ut.chrome_search(q)
            return ok,"chrome_search_xiaomi: "+str(msg)[:180],""
        except Exception as e:
            return False,"chrome_search_xiaomi: "+str(e)[:100],""

    if act=="maps_nav_xiaomi":
        try:
            import jack_ui_type as _ut
            try:
                import jack_xiaomi_unlock as _xu
                _xu.ensure_unlocked()
            except Exception: pass
            q=m.get("query","")
            if not q:
                return False,"maps_nav_xiaomi: query fehlt",""
            ok,msg=_ut.maps_nav(q)
            return ok,"maps_nav_xiaomi: "+str(msg)[:180],""
        except Exception as e:
            return False,"maps_nav_xiaomi: "+str(e)[:100],""

    if act=="maps_open_xiaomi":
        try:
            import jack_ui_type as _ut
            try:
                import jack_xiaomi_unlock as _xu
                _xu.ensure_unlocked()
            except Exception: pass
            q=m.get("query","")
            if not q:
                return False,"maps_open_xiaomi: query fehlt",""
            ok,msg=_ut.maps_open(q)
            return ok,"maps_open_xiaomi: "+str(msg)[:180],""
        except Exception as e:
            return False,"maps_open_xiaomi: "+str(e)[:100],""

    if act=="youtube_search_xiaomi":
        try:
            import jack_ui_type as _ut
            try:
                import jack_xiaomi_unlock as _xu
                _xu.ensure_unlocked()
            except Exception: pass
            q=m.get("query","")
            if not q:
                return False,"youtube_search_xiaomi: query fehlt",""
            ok,msg=_ut.youtube_search(q)
            return ok,"youtube_search_xiaomi: "+str(msg)[:180],""
        except Exception as e:
            return False,"youtube_search_xiaomi: "+str(e)[:100],""

    if act=="youtube_play_xiaomi":
        try:
            import jack_ui_type as _ut
            try:
                import jack_xiaomi_unlock as _xu
                _xu.ensure_unlocked()
            except Exception: pass
            q=m.get("query","")
            if not q:
                return False,"youtube_play_xiaomi: query fehlt",""
            ok,msg=_ut.youtube_play(q)
            return ok,"youtube_play_xiaomi: "+str(msg)[:180],""
        except Exception as e:
            return False,"youtube_play_xiaomi: "+str(e)[:100],""

    if act=="sv_restart":
        import subprocess
        SV_ALLOWED={"jack_telegram","jack_cortex","jack_waechter","jack_autolearn","jack_publisher","jack_focus_monitor","jack_missions","jack_mcp"}
        svc=m.get("service","")
        if svc not in SV_ALLOWED:
            return False,"sv_restart: Dienst nicht erlaubt: "+svc+" (erlaubt: "+",".join(sorted(SV_ALLOWED))+")",""
        if svc=="jack_missions":
            # JACK_TUNE_SELFRESTART_SAFE: Selbst-Neustart tötet diesen Prozess sofort und
            # verhindert, dass diese Mission je fertig geschrieben/verschoben wird -> Queue haengt.
            # Stattdessen: Neustart um 3s verzoegert und losgekoppelt im Hintergrund anstossen,
            # damit dieser Mission-Durchlauf erst sauber zu Ende laufen kann.
            try:
                subprocess.Popen(["sh","-c","sleep 3 && sv restart "+V+"/"+svc],
                                  start_new_session=True,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True,"sv_restart: "+svc+" verzoegerter Selbst-Neustart in 3s geplant",""
            except Exception as e:
                return False,"sv_restart: "+str(e)[:100],""
        try:
            r=subprocess.run(["sv","restart",V+"/"+svc],capture_output=True,text=True,timeout=15)
            out=(r.stdout or "")+(r.stderr or "")
            if r.returncode!=0:
                return False,"sv_restart: rc="+str(r.returncode)+" "+out[:150],""
            return True,"sv_restart: "+svc+" neu gestartet: "+out.strip()[:100],""
        except Exception as e:
            return False,"sv_restart: "+str(e)[:100],""

    if act=="dashboard_render":
        import subprocess, json as _dj, os as _do, glob as _dg, time as _dt
        base = J + "/missions"
        def _count(d):
            p = _do.path.join(base, d)
            return len([f for f in _do.listdir(p) if f.endswith(".json")]) if _do.path.isdir(p) else 0
        counts = {"pending": _count("pending"), "done": _count("done"), "fail": _count("fail")}
        # letzte Aktion als Warum-Feld
        why = "keine Daten"
        try:
            logs_dir = _do.path.join(base, "logs")
            files = sorted(_do.listdir(logs_dir), key=lambda f: _do.path.getmtime(_do.path.join(logs_dir,f)), reverse=True)[:1]
            if files:
                with open(_do.path.join(logs_dir, files[0]), encoding="utf-8") as _wf:
                    _rec = _dj.load(_wf)
                why = (_rec.get("act","?") + ": " + str(_rec.get("note",""))[:160])
        except Exception:
            pass
        # Honor-Akku lokal
        honor_batt = "unbekannt"
        try:
            r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=8)
            _b = _dj.loads(r.stdout)
            honor_batt = str(_b.get("percentage","?")) + "% " + str(_b.get("status",""))
        except Exception as _eH:
            honor_batt = "FEHLER: "+type(_eH).__name__+" "+str(_eH)[:80]
        # Xiaomi-Akku per SSH
        xiaomi_batt = "unbekannt"
        try:
            r = subprocess.run(["ssh","xiaomi-jack","termux-battery-status"], capture_output=True, text=True, timeout=15)
            _b = _dj.loads(r.stdout)
            xiaomi_batt = str(_b.get("percentage","?")) + "% " + str(_b.get("status",""))
        except Exception as _eX:
            xiaomi_batt = "FEHLER: "+type(_eX).__name__+" "+str(_eX)[:80]
        # Xiaomi-SSH-Status
        xiaomi_ssh = "offline"
        try:
            r = subprocess.run(["ssh","-o","ConnectTimeout=5","xiaomi-jack","echo","ok"], capture_output=True, text=True, timeout=10)
            if r.returncode==0 and "ok" in r.stdout:
                xiaomi_ssh = "online"
        except Exception:
            pass
        stand = _dt.strftime("%d.%m.%Y %H:%M:%S")
        total = counts["done"]+counts["fail"]
        rate = round(100*counts["done"]/total,1) if total else 0.0
        html = """<!DOCTYPE html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JACK Dashboard</title>
<style>
body{margin:0;background:#111;color:#eee;font-family:-apple-system,Helvetica,Arial,sans-serif;padding:20px;}
h1{font-size:20px;margin:0 0 4px;} .stand{font-size:12px;color:#999;margin:0 0 20px;}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;}
.card{background:#1c1c1e;border-radius:14px;padding:14px;}
.card p.label{font-size:12px;color:#999;margin:0 0 4px;}
.card p.val{font-size:22px;font-weight:600;margin:0;}
.list{background:#1c1c1e;border-radius:14px;padding:14px 16px;margin-bottom:12px;}
.row{display:flex;justify-content:space-between;padding:6px 0;border-top:1px solid #2c2c2e;font-size:14px;}
.row:first-child{border-top:none;}
.ok{color:#34d058;} .bad{color:#ff453a;}
.why{background:#1c1c1e;border-radius:14px;padding:14px 16px;}
.why p.label{font-size:12px;color:#999;margin:0 0 6px;}
.why p.val{font-size:13px;line-height:1.6;margin:0;color:#ddd;}
</style></head><body>
<h1>JACK Dashboard</h1>
<p class="stand">Stand: STANDX</p>
<div class="grid">
<div class="card"><p class="label">Akku Honor</p><p class="val">HONORBATTX</p></div>
<div class="card"><p class="label">Akku Xiaomi</p><p class="val">XIAOMIBATTX</p></div>
<div class="card"><p class="label">Missionen (Pending/Done/Fail)</p><p class="val">PENDX / DONEX / FAILX</p></div>
<div class="card"><p class="label">Erfolgsrate</p><p class="val">RATEX%</p></div>
</div>
<div class="list">
<div class="row"><span>MCP-Schnittstelle</span><span class="ok">Online</span></div>
<div class="row"><span>Xiaomi SSH</span><span class="XSSHCLASSX">XSSHVALX</span></div>
</div>
<div class="why"><p class="label">Warum JACK das gerade tut</p><p class="val">WHYX</p></div>
</body></html>"""
        html = html.replace("STANDX", stand)
        html = html.replace("HONORBATTX", honor_batt)
        html = html.replace("XIAOMIBATTX", xiaomi_batt)
        html = html.replace("PENDX", str(counts["pending"]))
        html = html.replace("DONEX", str(counts["done"]))
        html = html.replace("FAILX", str(counts["fail"]))
        html = html.replace("RATEX", str(rate))
        html = html.replace("XSSHCLASSX", "ok" if xiaomi_ssh=="online" else "bad")
        html = html.replace("XSSHVALX", xiaomi_ssh.capitalize())
        html = html.replace("WHYX", why)
        out_path = J + "/jack_dashboard.html"
        dl_path = "/storage/emulated/0/Download/jack_dashboard.html"
        try:
            with open(out_path, "w", encoding="utf-8") as _of:
                _of.write(html)
            _dl_note = ""
            try:
                with open(dl_path, "w", encoding="utf-8") as _odl:
                    _odl.write(html)
                _dl_note = " + Downloads-Kopie (Chrome-zugreifbar)"
            except Exception as _eD:
                _dl_note = " (Downloads-Kopie fehlgeschlagen: "+str(_eD)[:60]+")"
            return True, "dashboard_render: geschrieben nach "+out_path+_dl_note, ""
        except Exception as e:
            return False, "dashboard_render: "+str(e)[:120], ""

    if act=="reload_module":
        import importlib, sys
        RELOAD_ALLOWED = {"jack_ui_type","jack_verify_gate","jack_xiaomi_unlock","jack_yt_hybrid","jack_chat_router","jack_ui_session"}
        name = m.get("module","")
        if name not in RELOAD_ALLOWED:
            return False,"reload_module: nicht erlaubt: "+name+" (erlaubt: "+",".join(sorted(RELOAD_ALLOWED))+")",""
        try:
            if name in sys.modules:
                importlib.reload(sys.modules[name])
                return True,"reload_module: "+name+" neu geladen (war bereits im Speicher)",""
            else:
                importlib.import_module(name)
                return True,"reload_module: "+name+" frisch importiert (war noch nicht geladen)",""
        except Exception as e:
            return False,"reload_module: "+type(e).__name__+" "+str(e)[:150],""

    if act=="propose_fix":
        import json as _pj, os as _po, time as _pt, uuid as _pu
        problem = m.get("problem","")
        proposed_act = m.get("proposed_act","")
        proposed_extra = m.get("proposed_extra","{}")
        if not problem or not proposed_act:
            return False,"propose_fix: problem und proposed_act erforderlich",""
        pdir = J+"/missions/proposals/pending"
        _po.makedirs(pdir, exist_ok=True)
        pid = "prop_"+_pt.strftime("%Y%m%d_%H%M%S")+"_"+_pu.uuid4().hex[:6]
        data = {"id":pid, "ts":_pt.strftime("%Y-%m-%d %H:%M:%S"), "problem":problem,
                "proposed_act":proposed_act, "proposed_extra":proposed_extra, "status":"pending"}
        with open(_po.path.join(pdir, pid+".json"), "w", encoding="utf-8") as f:
            _pj.dump(data, f, ensure_ascii=False, indent=2)
        return True, "propose_fix: "+pid+" angelegt: "+problem[:100], ""

    if act=="list_proposals":
        import json as _pj, os as _po
        pdir = J+"/missions/proposals/pending"
        items = []
        if _po.path.isdir(pdir):
            for fn in sorted(_po.listdir(pdir)):
                if fn.endswith(".json"):
                    try:
                        with open(_po.path.join(pdir, fn), encoding="utf-8") as f:
                            items.append(_pj.load(f))
                    except Exception:
                        pass
        return True, "list_proposals: "+str(len(items))+" offen", _pj.dumps(items, ensure_ascii=False)

    if act=="approve_proposal":
        import json as _pj, os as _po, shutil as _psh
        pid = m.get("proposal_id","")
        pdir = J+"/missions/proposals/pending"
        fp = _po.path.join(pdir, pid+".json")
        if not _po.path.isfile(fp):
            return False,"approve_proposal: nicht gefunden: "+pid,""
        with open(fp, encoding="utf-8") as f:
            prop = _pj.load(f)
        inner_act = prop.get("proposed_act","")
        if inner_act not in ALLOWED:
            return False,"approve_proposal: proposed_act nicht (mehr) erlaubt: "+inner_act,""
        try:
            inner_extra = _pj.loads(prop.get("proposed_extra","{}") or "{}")
        except Exception as e:
            return False,"approve_proposal: proposed_extra ungueltig: "+str(e)[:80],""
        inner_m = dict(inner_extra)
        inner_m["act"] = inner_act
        ok, note, out = run_act(inner_m)
        done_dir = J+"/missions/proposals/"+("done" if ok else "failed")
        _po.makedirs(done_dir, exist_ok=True)
        prop["status"] = "applied" if ok else "failed"
        prop["result_note"] = note
        with open(_po.path.join(done_dir, pid+".json"), "w", encoding="utf-8") as f:
            _pj.dump(prop, f, ensure_ascii=False, indent=2)
        try:
            _po.remove(fp)
        except Exception:
            pass
        return ok, "approve_proposal: "+pid+" angewendet -> "+note, out

    if act=="preview_proposal":
        import json as _pvj, os as _pvo
        pid = m.get("proposal_id","")
        pdir = J+"/missions/proposals/pending"
        fp = _pvo.path.join(pdir, pid+".json")
        if not _pvo.path.isfile(fp):
            return False,"preview_proposal: nicht gefunden: "+pid,""
        with open(fp, encoding="utf-8") as f:
            prop = _pvj.load(f)
        inner_act = prop.get("proposed_act","")
        try:
            inner_extra = _pvj.loads(prop.get("proposed_extra","{}") or "{}")
        except Exception:
            inner_extra = {}
        if inner_act in ("sed_replace","py_replace"):
            _file = inner_extra.get("file","?")
            _old = inner_extra.get("old","")
            _new = inner_extra.get("new","")
            preview = ("DATEI: "+_file+chr(10)+
                       "ALT :"+chr(10)+_old[:300]+chr(10)+
                       "NEU :"+chr(10)+_new[:300])
        else:
            preview = "Act: "+inner_act+" mit Parametern: "+_pvj.dumps(inner_extra)[:300]
        return True, "preview_proposal: "+pid+" -> "+prop.get("problem","")[:100], preview

    if act=="close_app_xiaomi":
        import subprocess
        pkg = m.get("package","")
        _known = {"chrome":"com.android.chrome","spotify":"com.spotify.music",
                  "maps":"com.google.android.apps.maps","youtube":"com.google.android.youtube"}
        pkg = _known.get(pkg.lower(), pkg) if pkg else ""
        if not pkg or "." not in pkg:
            return False,"close_app_xiaomi: ungueltiges package/App-Name: "+str(pkg),""
        try:
            r=subprocess.run(["ssh","xiaomi-jack","su","-c","am force-stop "+pkg],
                              capture_output=True,text=True,timeout=15)
            if r.returncode!=0:
                return False,"close_app_xiaomi: rc="+str(r.returncode)+" "+(r.stderr or r.stdout)[:120],""
            return True,"close_app_xiaomi: "+pkg+" geschlossen (force-stop)",""
        except Exception as e:
            return False,"close_app_xiaomi: "+str(e)[:100],""

    if act=="write_proposed":
        import jack_write as _jw
        _fn = m.get("filename","")
        _ct = m.get("content","")
        if not _fn:
            return False,"write_proposed: kein filename",""
        _ok,_msg = _jw.commit_write(_fn,_ct)
        return _ok, "write_proposed: "+str(_msg)[:150], str(_msg)

    if act=="exec_proposed":
        import jack_exec as _je
        _cmd = m.get("cmd","")
        if not _cmd:
            return False,"exec_proposed: kein cmd",""
        _out = _je.run(_cmd)
        _ok = _out.startswith("rc=0")
        return _ok, "exec_proposed: "+_out[:150], _out

    if act=="honor_heat_report":
        import subprocess, glob as _hg, json as _hj
        rep = []
        try:
            r=subprocess.run(["termux-battery-status"],capture_output=True,text=True,timeout=8)
            b=_hj.loads(r.stdout)
            rep.append("AKKU: "+str(b.get("temperature","?"))+"C "+str(b.get("percentage","?"))+"% "+str(b.get("status","")))
        except Exception as e:
            rep.append("AKKU: Fehler "+type(e).__name__)
        zones=[]
        for zp in _hg.glob("/sys/class/thermal/thermal_zone*"):
            try:
                t=open(zp+"/type").read().strip()
                v=float(open(zp+"/temp").read().strip())
                if abs(v)>200: v=v/1000.0
                if v<=120 and ("trip" not in t) and ("ibat" not in t) and ("lvl" not in t):
                    zones.append((v,t))
            except Exception:
                pass
        zones.sort(reverse=True)
        if zones:
            rep.append("THERMAL Top6: "+", ".join(t+"="+str(round(v,1)) for v,t in zones[:6]))
        else:
            rep.append("THERMAL: keine Zone lesbar")
        procs=""
        for cmd in (["ps","-eo","pid,pcpu,pmem,etime,args","--sort=-pcpu"],["top","-b","-n","1"],["ps","-A"]):
            try:
                r=subprocess.run(cmd,capture_output=True,text=True,timeout=10)
                if r.returncode==0 and r.stdout.strip():
                    procs=chr(10).join([ln[:110] for ln in r.stdout.splitlines()[:12]])
                    break
            except Exception:
                continue
        rep.append("PROZESSE (nur eigene UID sichtbar, CPU-sortiert):"+chr(10)+(procs or "nicht lesbar"))
        try:
            _pg=subprocess.run(["pgrep","-a","ollama"],capture_output=True,text=True,timeout=5)
            rep.append("OLLAMA-PROZESSE auf Honor: "+((_pg.stdout or "").strip()[:200] or "keine"))
        except Exception:
            rep.append("OLLAMA-PROZESSE auf Honor: pgrep nicht verfuegbar")
        return True,"honor_heat_report: ok",chr(10).join(rep)[:1800]

    if act=="xiaomi_ollama_stop_v1":
        import subprocess, time as _tos, os as _oso
        try:
            subprocess.run(["ssh","xiaomi-jack","pkill -x ollama; pkill -x llama-server; true"],capture_output=True,text=True,timeout=20)
            _tos.sleep(2)
            _c=subprocess.run(["ssh","xiaomi-jack","curl","-s","-m","4","http://127.0.0.1:11434/api/tags"],capture_output=True,text=True,timeout=12)
            if _c.returncode==0 and _c.stdout.strip().startswith("{"):
                return False,"xiaomi_ollama_stop: Ollama antwortet noch nach Stopp-Versuch",""
            _lk=J+"/.ollama_lock"
            try:
                if _oso.path.isfile(_lk+".session") and not _oso.path.isfile(_lk):
                    _oso.rename(_lk+".session",_lk)
                elif not _oso.path.isfile(_lk):
                    open(_lk,"w").write("Ollama default AUS (Standard, nach Sitzungsende wiederhergestellt)")
                if _oso.path.isfile(J+"/.ollama_session"):
                    _oso.remove(J+"/.ollama_session")
            except Exception:
                pass
            return True,"xiaomi_ollama_stop: Ollama aus, Standard-Lock wieder aktiv",""
        except Exception as e:
            return False,"xiaomi_ollama_stop: "+str(e)[:100],""

    if act=="xiaomi_ollama_status":
        import subprocess
        try:
            _sv="/data/data/com.termux/files/usr/var/service"
            cmd=("ps -eo pid,ppid,user,etime,args 2>/dev/null | grep -i '[o]llama' | cut -c1-150; "
                 "echo ---SERVICES---; ls -1 "+_sv+" 2>&1 | head -20; "
                 "echo ---DOWN---; ls "+_sv+"/*/down 2>&1 | head -5; "
                 "echo ---BIN---; for b in ollama pkill sv setsid curl; do printf '%s=' $b; command -v $b || echo MISSING; done; "
                 "echo ---API---; curl -s -m 3 http://127.0.0.1:11434/api/tags | cut -c1-80; echo")
            r=subprocess.run(["ssh","xiaomi-jack",cmd],capture_output=True,text=True,timeout=25)
            return True,"xiaomi_ollama_status: ok",(r.stdout+r.stderr)[:1500]
        except Exception as e:
            return False,"xiaomi_ollama_status: "+str(e)[:100],""

    if act=="honor_ollama_disable":
        import subprocess, time as _thd, os as _ohd
        _svd="/data/data/com.termux/files/usr/var/service/ollama_local"
        try:
            if not _ohd.path.isdir(_svd):
                return False,"honor_ollama_disable: Service-Ordner fehlt: "+_svd,""
            open(_svd+"/down","a").close()
            _r1=subprocess.run(["sv","down",_svd],capture_output=True,text=True,timeout=15)
            _thd.sleep(2)
            subprocess.run(["pkill","-x","ollama"],capture_output=True,text=True,timeout=10)
            _thd.sleep(2)
            _p1=subprocess.run(["pgrep","-a","ollama"],capture_output=True,text=True,timeout=5)
            _p2=subprocess.run(["pgrep","-f","jack_ollama_guard"],capture_output=True,text=True,timeout=5)
            _left=((_p1.stdout or "").strip()+" "+(_p2.stdout or "").strip()).strip()
            _lk=J+"/.ollama_lock"
            if not _ohd.path.isfile(_lk):
                open(_lk,"w").write("Ollama default AUS (Standard)")
            if _left:
                return False,"honor_ollama_disable: noch aktiv: "+_left[:150],(_r1.stdout+_r1.stderr)[:150]
            return True,"honor_ollama_disable: Honor-Ollama-Hybrid aus (sv down + down-Datei), keine ollama/guard-Prozesse mehr",(_r1.stdout+_r1.stderr)[:150]
        except Exception as e:
            return False,"honor_ollama_disable: "+str(e)[:100],""

    if act=="graph_add_fact":
        import re as _gre, sqlite3 as _gsq, os as _gos, time as _gtm, glob as _ggl
        try:
            import jack_graph as _g
        except Exception as e:
            return False,"graph_add_fact: jack_graph nicht ladbar: "+str(e)[:80],""
        typ=(m.get("typ") or "fakt").strip()
        name=(m.get("name") or "").strip()
        wert=(m.get("wert") or "").strip()
        von=(m.get("von") or "person:dima").strip()
        rel=(m.get("rel") or "hat").strip()
        confirm=bool(m.get("confirm"))
        overwrite=bool(m.get("overwrite"))
        gueltig_tage=m.get("gueltig_tage")
        _gbis=None
        if gueltig_tage not in (None,""):
            try: _gbis=_gtm.time()+float(gueltig_tage)*86400
            except Exception: return False,"graph_add_fact: gueltig_tage muss eine Zahl sein",""
        if typ not in _g.TYPS:
            return False,"graph_add_fact: typ ungueltig (erlaubt: "+",".join(_g.TYPS)+")",""
        if rel not in _g.RELS:
            return False,"graph_add_fact: rel ungueltig (erlaubt: "+",".join(_g.RELS)+")",""
        if not name or not wert:
            return False,"graph_add_fact: name und wert erforderlich",""
        if len(name)>60 or len(wert)>200:
            return False,"graph_add_fact: name max 60, wert max 200 Zeichen",""
        _low=(name+" "+wert).lower()
        if any(k in _low for k in ("token","passwort","password","secret","bearer","api_key","apikey")) or _gre.search(r"[A-Za-z0-9+/=_-]{30,}",name+" "+wert):
            return False,"graph_add_fact: abgelehnt (sieht nach Geheimnis aus)",""
        if _g._is_suspicious(name) or _g._is_suspicious(wert):
            return False,"graph_add_fact: abgelehnt (Halluzinations-Filter)",""
        _nid=_g.nid(typ,name)
        c=_g.con()
        try:
            ex=c.execute("SELECT wert,src FROM nodes WHERE id=?",(_nid,)).fetchone()
            vn=c.execute("SELECT 1 FROM nodes WHERE id=?",(von,)).fetchone()
        finally:
            c.close()
        if not vn:
            return False,"graph_add_fact: Ausgangsknoten existiert nicht: "+von,""
        if ex and ex[1]!="claude_mcp" and not overwrite:
            return False,"graph_add_fact: "+_nid+" existiert (src="+str(ex[1])+") - nicht ueberschrieben, overwrite nur mit Dimas Wort",""
        plan=_nid+" (wert="+wert+") + Kante "+von+" -"+rel+"-> "+_nid+(" (gueltig "+str(gueltig_tage)+" Tage)" if _gbis else "")
        if not confirm:
            return True,"graph_add_fact VORSCHAU (nichts geschrieben): "+plan+" | schreiben mit confirm=true",""
        bdir=J+"/graph_backups"
        try:
            _gos.makedirs(bdir,exist_ok=True)
            _bp=bdir+"/jack_graph_"+_gtm.strftime("%Y%m%d_%H%M%S")+".db"
            _s=_gsq.connect(_g.DB,timeout=5); _d=_gsq.connect(_bp); _s.backup(_d); _d.close(); _s.close()
            for _f in sorted(_ggl.glob(bdir+"/jack_graph_*.db"))[:-5]:
                try:
                    _gos.remove(_f)
                except Exception:
                    pass
        except Exception as e:
            return False,"graph_add_fact: Backup fehlgeschlagen, nichts geschrieben: "+str(e)[:80],""
        r1=_g.put_node(typ,name,wert,"claude_mcp")
        if not r1:
            return False,"graph_add_fact: put_node lehnte ab (Filter)",""
        _g.put_edge(von,rel,r1,"claude_mcp",_gbis)
        c=_g.con()
        try:
            ck=c.execute("SELECT 1 FROM edges WHERE a=? AND rel=? AND b=?",(von,rel,r1)).fetchone()
        finally:
            c.close()
        return bool(ck),"graph_add_fact: geschrieben: "+plan+(" | Kante ok" if ck else " | KANTE FEHLT"),""

    if act=="graph_remove_fact":
        try:
            import jack_graph as _g
        except Exception as e:
            return False,"graph_remove_fact: jack_graph nicht ladbar: "+str(e)[:80],""
        _rid=(m.get("node_id") or "").strip()
        if not _rid:
            return False,"graph_remove_fact: node_id erforderlich",""
        c=_g.con()
        try:
            ex=c.execute("SELECT src,wert FROM nodes WHERE id=?",(_rid,)).fetchone()
            if not ex:
                return False,"graph_remove_fact: Knoten nicht gefunden: "+_rid,""
            if ex[0]!="claude_mcp":
                return False,"graph_remove_fact: nur eigene Eintraege (src=claude_mcp) loeschbar, hier src="+str(ex[0]),""
            if not m.get("confirm"):
                return True,"graph_remove_fact VORSCHAU: wuerde "+_rid+" (wert="+str(ex[1])[:60]+") samt Kanten loeschen | mit confirm=true",""
            c.execute("DELETE FROM edges WHERE a=? OR b=?",(_rid,_rid))
            c.execute("DELETE FROM nodes WHERE id=?",(_rid,))
            c.commit()
        finally:
            c.close()
        return True,"graph_remove_fact: "+_rid+" samt Kanten entfernt",""

    if act=="was_ist_neu":
        import time as _wtm, os as _wos, glob as _wgl, sqlite3 as _wsq, datetime as _wdt, json as _wjs
        try:
            _std=float(m.get("stunden",10) or 10)
        except Exception:
            _std=10.0
        _cutoff_epoch=_wtm.time()-_std*3600
        _cutoff_dt=_wdt.datetime.now()-_wdt.timedelta(hours=_std)
        rep=["ZEITRAUM: letzte "+str(_std)+" Std"]
        # 1) Missions-Protokolle
        try:
            _logs=_wgl.glob(J+"/missions/logs/*.json")
            _recent=[(p,_wos.path.getmtime(p)) for p in _logs if _wos.path.getmtime(p)>=_cutoff_epoch]
            _recent.sort(key=lambda x:-x[1])
            _ok=0; _fail=0; _samples=[]
            for p,_ in _recent:
                try:
                    with open(p,encoding="utf-8") as f: _d=_wjs.load(f)
                    if _d.get("ok"): _ok+=1
                    else: _fail+=1
                    if len(_samples)<6:
                        _samples.append(_d.get("act","?")+": "+str(_d.get("note",""))[:70])
                except Exception:
                    pass
            rep.append("MISSIONEN: "+str(len(_recent))+" gesamt ("+str(_ok)+" ok, "+str(_fail)+" fehlgeschlagen)")
            if _samples:
                rep.append("Beispiele: "+" | ".join(_samples))
        except Exception as e:
            rep.append("MISSIONEN: Fehler "+str(e)[:60])
        # 2) Frische Graph-Fakten
        try:
            import jack_graph as _g
            c=_g.con()
            try:
                rows=c.execute("SELECT id,wert,src FROM nodes WHERE ts>=? ORDER BY ts DESC LIMIT 10",(_cutoff_epoch,)).fetchall()
            finally:
                c.close()
            rep.append("NEUE FAKTEN: "+str(len(rows)))
            for rid,wert,src in rows[:8]:
                rep.append("- "+rid+" = "+str(wert)[:80]+" (src="+src+")")
        except Exception as e:
            rep.append("FAKTEN: Fehler "+str(e)[:60])
        # 3) Speicher-Episoden
        try:
            _mdb=J+"/jack_memory.db"
            if _wos.path.isfile(_mdb):
                c=_wsq.connect(_mdb,timeout=5)
                try:
                    rows=c.execute("SELECT cmd,intent,source,timestamp FROM memory WHERE timestamp>=? ORDER BY timestamp DESC LIMIT 8",
                                   (_cutoff_dt.strftime("%Y-%m-%d %H:%M:%S"),)).fetchall()
                finally:
                    c.close()
                rep.append("EPISODEN: "+str(len(rows)))
                for cmd,intent,src,ts in rows[:6]:
                    rep.append("- ["+str(intent)+"/"+str(src)+"] "+str(cmd)[:80])
            else:
                rep.append("EPISODEN: DB fehlt")
        except Exception as e:
            rep.append("EPISODEN: Fehler "+str(e)[:60])
        return True,"was_ist_neu: ok","\n".join(rep)[:1800]

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
        # "file" (singular) hat Vorrang vor "files" (plural)
        if "file" in m:
            import os as _os
            single = m["file"].replace("~/jack", J)
            if not _os.path.exists(single):
                return False, f"compile FAIL: Datei fehlt: {_os.path.basename(single)}", ""
            rc,o=sh(["python3","-m","py_compile",single],t=12)
            return (rc==0), "compile "+("OK" if rc==0 else "FAIL: "+o[:60]), ""
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
    if str(dest).rstrip("/").endswith("fail"):
        try:
            import jack_deadletter as _dl
            _dl.bump(os.path.splitext(os.path.basename(path))[0], os.path.join(dest,os.path.basename(path)))
        except Exception:
            pass

    # JACK_TUNE_MCPKANAL: Ergebnis in jack_memory.db damit Claude es via memory_recent lesen kann
    try:
        import sqlite3 as _sq, uuid as _uuid
        from datetime import datetime as _dtm
        _mdb = J+"/jack_memory.db"
        _conn = _sq.connect(_mdb)
        _mid = str(_uuid.uuid4())
        _ts = _dtm.now().isoformat()[:19]
        _summ = ("ok" if rec.get("ok") else "fail")+": "+str(rec.get("raw_ok",""))[:200]
        _conn.execute(
            "INSERT INTO memory (id, cmd, result, intent, time, timestamp, source, kontext_typ) VALUES (?,?,?,?,?,?,?,?)",
            (_mid, rec.get("id",""), _summ, "mission_result", _ts, _ts, "jack_mission_runner", "mission"))
        _conn.commit(); _conn.close()
    except Exception:
        pass  # nie blockieren

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
            rc=1  # JACK_TUNE_QUEUENOFAIL: merken, aber weitermachen statt Schleife abzubrechen
    return rc
def _hb():
    try:
        open("/data/data/com.termux/files/home/jack/.heartbeat_jack_missions","w").write(str(time.time()))
    except Exception:
        pass
BOOST_FILE=J+"/.mission_boost"  # JACK_TUNE_BOOST
def _poll_now(default_poll):
    return 1 if os.path.exists(BOOST_FILE) else default_poll

def loop(poll=30, maxn=200):
    while True:
        _hb()
        if os.path.isfile(STOP):
            print("STOP-FILE"); open(V+"/jack_missions/down","a").close(); os._exit(0)  # JACK_TUNE_STOPKILL
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
            if rc!=0: print("QUEUE-FAIL rc", rc)  # JACK_TUNE_QSTAY
        time.sleep(1)  # JACK_TUNE_FASTLOOP
if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "once"
    sys.exit(loop() if mode=="loop" else run_queue())
