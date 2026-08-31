#!/data/data/com.termux/files/usr/bin/python3
"""UI tippen: EditText finden, leeren, Text setzen, Enter."""
import re, time, subprocess

def _ssh(cmd, t=25):
    r=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack", cmd],
        capture_output=True, text=True, timeout=t)
    return r.returncode, (r.stdout or "")+(r.stderr or "")

def _dump_xml():
    import jack_ui_session as ui
    d=ui.ui_dump(max_chars=120000)
    return d.get("xml") or ""

def _bounds(node):
    m=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
    if not m: return None
    x1,y1,x2,y2=map(int,m.groups())
    return (x1+x2)//2, (y1+y2)//2, x1,y1,x2,y2

def find_edittext(package=None):
    xml=_dump_xml()
    nodes=re.findall(r'<node[^>]*class="[^"]*EditText[^"]*"[^>]*>', xml)
    out=[]
    for n in nodes:
        if package and ('package="%s"'%package) not in n: continue
        b=_bounds(n)
        if not b: continue
        tm=re.search(r'text="([^"]*)"', n)
        text=tm.group(1) if tm else ""
        out.append({"node":n,"cx":b[0],"cy":b[1],"text":text,"bounds":b[2:]})
    # topmost first (smallest y)
    out.sort(key=lambda x: x["cy"])
    return out

def clear_and_type(text, package="com.android.chrome"):
    try:
        import jack_xiaomi_unlock as xu
        xu.ensure_unlocked()
    except Exception:
        pass
    edits=find_edittext(package=package)
    if not edits:
        return False, "kein EditText in %s" % package
    e=edits[0]
    cx,cy=e["cx"],e["cy"]
    # focus
    _ssh("su -c 'input tap %d %d'" % (cx,cy))
    time.sleep(0.35)
    # select all + delete
    _ssh("su -c 'input keyevent 113'")  # CTRL maybe noop on android
    _ssh("su -c 'input keyevent --longpress 67'")  # long DEL often clears selection poorly
    # spam backspace
    for _ in range(min(80, max(12, len(e.get("text") or "")+8))):
        _ssh("su -c 'input keyevent 67'")
    time.sleep(0.2)
    # type (escape single quotes)
    safe=text.replace("'","")
    rc,_=_ssh("su -c \"input text '%s'\"" % safe)
    time.sleep(0.3)
    # ENTER
    _ssh("su -c 'input keyevent 66'")
    return True, "typed %r into EditText@%d,%d was=%r" % (safe, cx, cy, e.get("text"))

def chrome_search(query):
    try:
        import jack_verify_gate as vg
        ok,msg=vg.app_open_verified("com.android.chrome", times=2)
        if not ok:
            return False, "chrome open fail: "+msg
    except Exception as e:
        return False, "chrome open exc: "+str(e)
    time.sleep(0.8)
    return clear_and_type(query, package="com.android.chrome")



def _spotify_score_tap(query):
    """JACK_TUNE_SPOTIFY_SCORE: UI-Dump, beste Titelzeile tippen."""
    import re, time
    q=(query or "").lower()
    keys=[w for w in re.split(r"\W+", q) if len(w)>2]
    rc, xml = _ssh_x("su -c 'uiautomator dump /sdcard/jack_ui.xml >/dev/null && cat /sdcard/jack_ui.xml'") if '_ssh_x' in dir() else (1,"")
    try:
        import jack_yt_hybrid as _yh
        rc, xml = _yh.ssh("su -c 'uiautomator dump /sdcard/jack_ui.xml >/dev/null && cat /sdcard/jack_ui.xml'")
    except Exception:
        return False, "no_ssh"
    nodes=re.findall(r'<node[^>]+>', xml or "")
    ban=("home","suche","bibliothek","premium","einstell")
    cands=[]
    for n in nodes:
        if 'clickable="true"' not in n: continue
        tx=re.search(r'text="([^"]*)"', n)
        cd=re.search(r'content-desc="([^"]*)"', n)
        lab=((tx.group(1) if tx else "")+" "+(cd.group(1) if cd else "")).strip()
        if len(lab)<3: continue
        low=lab.lower()
        if any(b in low for b in ban): continue
        m=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
        if not m: continue
        x1,y1,x2,y2=map(int,m.groups())
        cx,cy=(x1+x2)//2,(y1+y2)//2
        h=y2-y1
        if cy<200 or cy>2000 or h<40: continue
        sc=sum(1 for w in keys if w in low)
        if sc: cands.append((sc,h,cy,cx,lab[:80]))
    cands.sort(reverse=True)
    if not cands:
        return False, "no_candidates"
    sc,h,cy,cx,lab=cands[0]
    try:
        import jack_yt_hybrid as _yh
        _yh.ssh("su -c 'input tap %d %d'"%(cx,cy))
        import time; time.sleep(1.1)
        rc2, xml2 = _yh.ssh("su -c 'uiautomator dump /sdcard/jack_ui.xml >/dev/null && cat /sdcard/jack_ui.xml'")
        play=None
        for n2 in re.findall(r'<node[^>]+>', xml2 or ""):
            cd2=re.search(r'content-desc="([^"]*)"', n2)
            tx2=re.search(r'text="([^"]*)"', n2)
            lab2=((cd2.group(1) if cd2 else "")+" "+(tx2.group(1) if tx2 else "")).lower()
            if 'clickable="true"' not in n2: continue
            if any(k in lab2 for k in ('play','wiedergabe','abspielen')) and 'pause' not in lab2:
                m2=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n2)
                if not m2: continue
                a,b,c,d=map(int,m2.groups())
                play=((a+c)//2,(b+d)//2,lab2[:40])
                if (c-a)>80 and (d-b)>80: break
        if play:
            _yh.ssh("su -c 'input tap %d %d'"% (play[0],play[1]))
            lab = lab+" +play"
    except Exception as e:
        return False, "tap "+type(e).__name__
    return True, lab

def spotify_play(query):
    """JACK_TUNE_SPOTIFY: Deep-Link search + best title match."""
    import re, time, subprocess
    q=(query or "").strip()
    if not q:
        return False, "empty"
    def ssh(cmd, t=25):
        r=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack",cmd],
            capture_output=True,text=True,timeout=t)
        return r.returncode, (r.stdout or "")+(r.stderr or "")
    try:
        import jack_verify_gate as v
        ok,msg=v.app_open_verified("com.spotify.music",2)
        if not ok:
            return False, "app "+str(msg)
    except Exception as e:
        return False, "gate "+type(e).__name__
    time.sleep(0.5)
    ssh("su -c 'input keyevent 4'")
    time.sleep(0.3)
    dq=q.replace("'","")
    ssh("su -c \"am start -a android.intent.action.VIEW -d 'spotify:search:%s'\"" % dq)
    time.sleep(2.2)
    import jack_ui_session as ui
    xml=(ui.ui_dump(max_chars=120000).get("xml") or "")
    cands=[]
    ql=[w for w in re.split(r"\s+", q.lower()) if len(w)>1]
    for n in re.findall(r"<node[^>]+>", xml):
        if 'resource-id="com.spotify.music:id/title"' not in n and not n.rstrip().endswith('id/title"'):
            if 'id/title"' not in n:
                continue
        m=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
        txm=re.search(r'text="([^"]*)"', n)
        if not m or not txm:
            continue
        tx=txm.group(1).strip()
        if not tx:
            continue
        x1,y1,x2,y2=map(int,m.groups())
        cy=(y1+y2)//2
        cx=(x1+x2)//2
        if cy < 280 or cy > 1750:
            continue
        score=sum(1 for w in ql if w in tx.lower())
        cands.append((-score, cy, cx, tx))
    cands.sort()
    if not cands:
        return _spotify_score_tap(query)
    score, cy, cx, tx = cands[0][0], cands[0][1], cands[0][2], cands[0][3]
    ssh("su -c 'input tap %d %d'" % (cx, cy))
    time.sleep(1.6)
    xml2=(ui.ui_dump(max_chars=60000).get("xml") or "")
    for n in re.findall(r"<node[^>]+>", xml2):
        if "play_pause_button" in n and 'content-desc="Play"' in n:
            m=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
            if m:
                a,b,c,d=map(int,m.groups())
                ssh("su -c 'input tap %d %d'" % ((a+c)//2, (b+d)//2))
                time.sleep(0.7)
            break
    return True, "play %s (score %s)" % (tx, -score)

def spotify_surprise():
    """JACK_TUNE_SPOTIFY_SURPRISE: rotating seed list."""
    import time, hashlib
    seeds=["sido","apache 207","capital bra","bonez mc","raf camora",
           "kollegah","farid bang","187 strassenbande","luciano","nimo"]
    day=time.strftime("%Y%m%d")
    h=int(hashlib.md5((day+str(int(time.time())//300)).encode()).hexdigest(),16)
    q=seeds[h % len(seeds)]
    return spotify_play(q)

def maps_nav(query):
    """JACK_TUNE_MAPS_YT: Google Maps navigation search."""
    import subprocess, urllib.parse, time
    q=(query or "").strip()
    if not q: return False, "empty"
    def ssh(cmd,t=20):
        r=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack",cmd],
            capture_output=True,text=True,timeout=t)
        return r.returncode, ((r.stdout or "")+(r.stderr or ""))[:120]
    try:
        import jack_verify_gate as v
        ok,msg=v.app_open_verified("com.google.android.apps.maps",2)
        if not ok: return False, "app "+str(msg)
    except Exception as e:
        return False, "gate "+type(e).__name__
    time.sleep(0.4)
    enc=urllib.parse.quote(q)
    # geo query opens search; google.navigation starts nav when possible
    rc,out=ssh("su -c \"am start -a android.intent.action.VIEW -d 'geo:0,0?q=%s'\""%enc)
    time.sleep(1.5)
    return True, "maps "+q

def youtube_search(query):
    """JACK_TUNE_MAPS_YT: YouTube search results."""
    import subprocess, urllib.parse, time
    q=(query or "").strip()
    if not q: return False, "empty"
    def ssh(cmd,t=20):
        r=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack",cmd],
            capture_output=True,text=True,timeout=t)
        return r.returncode, ((r.stdout or "")+(r.stderr or ""))[:120]
    try:
        import jack_verify_gate as v
        ok,msg=v.app_open_verified("com.google.android.youtube",2)
        if not ok: return False, "app "+str(msg)
    except Exception as e:
        return False, "gate "+type(e).__name__
    time.sleep(0.4)
    enc=urllib.parse.quote(q)
    rc,out=ssh("su -c \"am start -a android.intent.action.VIEW -d 'https://www.youtube.com/results?search_query=%s' -n com.google.android.youtube/com.google.android.apps.youtube.app.WatchWhileActivity\""%enc)
    # fallback plain VIEW
    if rc!=0:
        ssh("su -c \"am start -a android.intent.action.VIEW -d 'https://www.youtube.com/results?search_query=%s'\""%enc)
    time.sleep(1.5)
    return True, "youtube "+q


def _ssh_x(cmd, t=25):
    import subprocess
    r=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack",cmd],
        capture_output=True,text=True,timeout=t)
    return r.returncode, ((r.stdout or "")+(r.stderr or ""))[:200]

def maps_open(query):
    """JACK_TUNE_MAPSYT: geo-search on Xiaomi."""
    import time
    q=(query or "").strip()
    if not q: return False, "empty"
    try:
        import jack_verify_gate as v
        ok,msg=v.app_open_verified("com.google.android.apps.maps",2)
        if not ok: return False, "app "+str(msg)
    except Exception as e:
        return False, "gate "+type(e).__name__
    time.sleep(0.4)
    dq=q.replace("'"," ").replace('"',"")
    rc,_=_ssh_x("su -c \"am start -a android.intent.action.VIEW -d 'geo:0,0?q=%s'\"" % dq)
    time.sleep(1.8)
    return True, "maps "+q+" rc="+str(rc)


def youtube_play(query):
    """JACK_TUNE_YTHYBRID: RVX + OCR-Check + UI-Dump-Tap via jack_yt_hybrid."""
    q=(query or "").strip()
    if not q:
        return False, "empty"
    try:
        import jack_yt_hybrid as _yh
        rec=_yh.play(q, save_recipe=True)
        if rec.get("ok"):
            return True, "YT %s → %s" % (q, rec.get("label","ok")[:80])
        return False, "YT fail: %s" % (rec.get("reason") or rec)
    except Exception as e:
        return False, "YT EXC %s" % type(e).__name__
