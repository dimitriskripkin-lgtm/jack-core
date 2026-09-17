#!/usr/bin/env python3
MODULE_VERSION = 1
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
    diag=any(k in t for k in ("essenz","schau dich","selbst sehen","eigenen code","eigener code","kompletten code","anomalie","nicht erreichbar","graceful","xiaomi offline","murks","guck dir")) or (any(k in t for k in ("analysier","fehler","verbesser","schau mal")) and any(k in t for k in ("code","modul","datei","log","dienst",".py")))  # JACK_TUNE_GATE1
    expl=("overmind" in t or "deadman" in t) and not fact and not diag
    if fact: return "FACT"
    if expl: return "EXPLAIN"
    if diag: return "DIAG"
    return "TALK"


def _bat_parse(out):
    if out and out.strip().startswith("{"):
        import json as _j
        try:
            d=_j.loads(out)
            temp=d.get("temperature")
            lev=d.get("percentage")
            pl=str(d.get("plugged") or "")
            st=str(d.get("status") or "")
            pw=[]
            if "AC" in pl: pw.append("AC")
            if "USB" in pl: pw.append("USB")
            if "WIRELESS" in pl: pw.append("Wireless")
            sm={"CHARGING":"laedt","DISCHARGING":"entlaedt","FULL":"voll","NOT_CHARGING":"nicht laden"}.get(st,st.lower())
            return temp, lev, pw, sm
        except Exception:
            pass

    temp=lev=None
    powered=[]
    status=None
    for ln in (out or "").splitlines():
        s=ln.strip().lower()
        if "temperature" in s and ":" in s:
            try: temp=int("".join(ch for ch in s.split(":")[-1] if ch.isdigit() or ch=="-"))/10.0
            except Exception: pass
        if "level:" in s and "voltage" not in s:
            try: lev=int("".join(ch for ch in s.split(":")[-1] if ch.isdigit()))
            except Exception: pass
        if s.startswith("ac powered:") and "true" in s: powered.append("AC")
        if s.startswith("usb powered:") and "true" in s: powered.append("USB")
        if s.startswith("wireless powered:") and "true" in s: powered.append("Wireless")
        if s.startswith("status:"):
            try: status=int("".join(ch for ch in s.split(":")[-1] if ch.isdigit()))
            except Exception: pass
    st={1:"unbekannt",2:"laedt",3:"entlaedt",4:"voll",5:"nicht laden"}.get(status,"status "+str(status))
    return temp, lev, powered, st

def _tool_name(text):
    """JACK_TUNE_TOOLNAME — welches Werkzeug wuerde greifen. Nur fuer den Logger."""
    t = norm(text)
    low = (text or "").lower()
    if any(w in t for w in ("zeig mir alles","zeig mir alle","alles davon","alle davon","alle werte","umgebung","wie sieht")):
        return "sammel_alles"
    if any(w in t for w in ("wie alt sind diese","diese daten","wie frisch")):
        return "daten_alter"
    if any(w in t for w in ("temperatur","akku","batterie","warm","hitze","grad","laden","ladeger")):
        if "xiaomi" in low or "muskel" in low: return "bat_xiaomi"
        if "honor" in low or "gehirn" in low: return "bat_honor"
        return "bat_beide"
    # P3-Fix (16.09.): nur explizite Knoten-Anfragen, keine Gespraechsfragen
    if any(w in t for w in ("letzte knoten","knoten zeigen","zeig die knoten","zeig mir die knoten","graph knoten","liste der knoten")):
        return "graph_knoten"
    if any(w in t for w in ("erreichbar","ssh","verbindung","verbunden","online","xiaomi da","xiaomi laeuft","xiaomi läuft")):
        return "ssh_xiaomi"
    if any(w in t for w in ("welche dienste","was laeuft","dienste")):
        return "sv_status"
    if any(w in t for w in ("speicher","wie voll","platz","speicherplatz")):
        return "df_xiaomi" if "xiaomi" in low else "df_honor"
    if any(w in t for w in ("welche werkzeuge","was kannst du messen","was kannst du","was kannst du tun","kiste","zehn punkte","umsetzen kannst","was kannst du umsetzen")):
        return "kiste_liste"
    return None

def _tools(text):
    # JACK_TUNE_TOOLBOX
    t=norm(text)
    if any(w in t for w in ("zeig mir alles","zeig mir alle","alles davon","alle davon","alle werte","alles messen","komplette kiste","systemzustand jetzt")):  # JACK_TUNE_NOAMB
        bits=[]
        for q in ("wie warm xiaomi und honor","ist xiaomi erreichbar","welche dienste laufen","wie voll speicher xiaomi","wie voll speicher honor","letzte erinnerungen"):
            r=_tools(q)
            if r: bits.append(r)
        return "\n".join(bits) if bits else "Kiste leer."  # JACK_TUNE_TOOLALL
    raw=(text or "")
    low=raw.lower()
    import subprocess
    def sh(cmd, tmo=10):
        r=subprocess.run(cmd, capture_output=True, text=True, timeout=tmo)
        return ((r.stdout or "")+(r.stderr or ""))
    want_bat=any(w in t for w in ("temperatur","akku","batterie","warm","hitze","grad","laden","ladeger"))
    # P3-Fix (16.09.): nur explizite Knoten-Anfragen
    want_mem=any(w in t for w in ("letzte knoten","knoten zeigen","zeig die knoten","zeig mir die knoten","graph knoten","liste der knoten"))
    want_age=any(w in t for w in ("wie alt sind diese","diese daten","wie frisch")) and any(w in t for w in ("daten","messung","sensor","akku","temp"))  # JACK_TUNE_AGEENG
    if want_age and not want_bat:
        return "Sensorwerte gelten nur fuer die letzte Messung, nicht aus Logs."
    if want_bat:
        parts=[]
        do_x=("xiaomi" in low) or ("honor" not in low)
        do_h=("honor" in low) or ("xiaomi" not in low)
        if do_x:
            try:
                out=sh(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=6","xiaomi-jack","su","-c","dumpsys battery"])
                temp,lev,pw,st=_bat_parse(out)
                parts.append("Xiaomi Temp %s C Akku %s %% %s Strom %s jetzt" % (
                    temp if temp is not None else "?",
                    lev if lev is not None else "?",
                    st,
                    ",".join(pw) if pw else "kein"))
            except Exception as e:
                parts.append("Xiaomi Sensor: "+str(e)[:60])
        if do_h:
            try:
                _used=False
                try:
                    import jack_health as _jhbf
                    _bat=_jhbf.bat_fresh() or {}
                    if _bat.get("pct") is not None:
                        parts.append("Honor Temp %s C Akku %s %% %s Strom %s jetzt" % (
                            _bat.get("c") if _bat.get("c") is not None else "?",
                            _bat.get("pct"),
                            str(_bat.get("status") or "?").lower(),
                            str(_bat.get("plugged") or "kein")))
                        _used=True  # JACK_TUNE_TBHEALTH
                except Exception:
                    _used=False
            except Exception as e:
                parts.append("Honor Sensor: "+str(e)[:60])
        if parts:
            return "; ".join(parts)
    if want_mem:
        try:
            import jack_graph as _g
            rows=_g.con().execute("SELECT typ,name,wert FROM nodes ORDER BY rowid DESC LIMIT 10").fetchall()
            if not rows:
                return "Graph leer."
            return "Letzte Knoten:\n"+"\n".join("%s %s=%s"%(a,b,c) for a,b,c in rows)
        except Exception as e:
            return "Graph-Lesen fehl: "+str(e)[:80]
    want_ssh=any(w in t for w in ("erreichbar","ssh ok","xiaomi da","ping xiaomi","ssh xiaomi","verbunden","verbindung","online"))  # JACK_TUNE_F2SSH
    if want_ssh or ("ssh" in t and "xiaomi" in t):
        try:
            out=sh(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=6","xiaomi-jack","echo OK"], 8)
            return "Xiaomi SSH " + ("OK" if "OK" in out else "DOWN "+out[:80])
        except Exception as e:
            return "Xiaomi SSH DOWN "+str(e)[:80]
    want_sv=any(w in t for w in ("welche dienste","was laeuft","was lauft","sv status"))
    if want_sv:
        try:
            out=sh(["sv","status","jack_telegram"])+" | "+sh(["sv","status","jack_waechter"])+" | "+sh(["sv","status","jack_cortex"])+" | "+sh(["sv","status","jack_missions"])  # JACK_TUNE_K4TB
            return "Dienste jetzt: "+out.replace("\n"," ")[:400]
        except Exception as e:
            return "sv fehl: "+str(e)[:80]
    want_disk=any(w in t for w in ("speicher","wie voll","freier platz"))
    if want_disk or (("xiaomi" in t) and ("voll" in t or "speicher" in t)):
        parts=[]
        do_x=("xiaomi" in t)
        do_h=("honor" in t) or not do_x
        if do_h:
            try:
                h=sh(["df","-h","/data"], 8)
                line=[ln for ln in h.splitlines() if ln.strip()][-1]
                parts.append("Honor Speicher: "+line[:160])
            except Exception as e:
                parts.append("Honor df: "+str(e)[:60])
        if do_x:
            try:
                x=sh(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=6","xiaomi-jack","df -h /data"], 10)
                line=[ln for ln in x.splitlines() if ln.strip()][-1]
                parts.append("Xiaomi Speicher: "+line[:160])
            except Exception as e:
                parts.append("Xiaomi df: "+str(e)[:60])
        if parts:
            return "; ".join(parts)
    if any(w in t for w in ("wer bist du","was bist du","was ist deine persona","deine persona","wer bin ich")):
        return "JACK. Dimas System auf Honor, Xiaomi als Arm. Kein Assistent."  # JACK_TUNE_WERBIN1
    want_list=any(w in t for w in ("welche werkzeuge","was kannst du messen","was misst du","werkzeugkiste","toolkiste","zehn punkte","umsetzen kannst","was kannst du umsetzen"))  # JACK_TUNE_NOAMB2
    if want_list:
        return None  # JACK_TUNE_KISTELIVE
    if any(w in t for w in ("gespraechsverlauf","chatverlauf","telegram verlauf","letzte frage","letzte was","zuletzt gefragt","was habe ich gefragt","was fragte ich","gefragt habe")):
        try:
            import json
            rows=[]
            for ln in open("/data/data/com.termux/files/home/jack/reports/decisions.jsonl",encoding="utf-8"):
                try:
                    o=json.loads(ln)
                    m=(o.get("msg") or "").strip()
                    if m: rows.append((o.get("ts",""), m))
                except Exception:
                    pass
            rows=rows[-3:]
            if not rows: return "Keine Fragen im Log."
            return "Zuletzt:\n" + "\n".join("%s %s"%(a,b[:80]) for a,b in rows)
        except Exception as e:
            return "Log fehlt: "+str(e)[:60]
    if any(w in t for w in ("ueber mich","über mich","letzten 10","letzte 10 sachen","was weisst du alles ueber")):
        try:
            import jack_graph as _g
            c=_g.con()
            rows=c.execute("SELECT typ,name,wert FROM nodes ORDER BY rowid DESC LIMIT 10").fetchall()
            if not rows: return "Keine Knoten."
            lines=[]
            for typ,name,wert in rows:
                if typ=="fakt":
                    lines.append("%s: %s"%(name, wert))
                elif typ=="geraet":
                    continue
                else:
                    lines.append("%s: %s"%(name, wert))
            return "Was ich ueber dich habe:\n" + "\n".join(lines)  # JACK_TUNE_LESBAR
        except Exception as e:
            return "Graph: "+str(e)[:60]
    return None  # JACK_TUNE_TOOLIST

def kiste_fuer_prompt(text):
    t=norm(text)
    keys=("was kannst","wie kannst","fuer mich tun","mir dienen","zehn punkte","umsetzen kannst","ausfuehren kannst","welche werkzeuge","werkzeugkiste","toolkiste")
    if not any(w in t for w in keys):
        return None
    return ("Nur das: Temp/Akku Honor+Xiaomi messen, Graph-Knoten lesen, SSH Xiaomi pruefen, sv-Status der vier Dienste sagen, Speicher beider Geraete. Talk=Groq. Ollama aus. missions pausiert. autolearn/publisher aus. Keine Dienste starten oder stoppen. Keine lokalen Modelle. Keine erfundenen Scheduler. Formuliere frei. Keine Tune-Marke.")

def talk_local(text):

    t=norm(text)
    # JACK_TUNE_LERN1 (16.09., Phase 8.3+8.4): Korrektur-Erkennung
    try:
        import json as _jl, time as _jt2, os as _jo
        _stp = J + "/reports/last_msg.json"
        _tnow = _jt2.time()
        _toks = set(w for w in t.split() if len(w) > 3)
        _prev = None
        if _jo.path.isfile(_stp):
            try: _prev = _jl.loads(open(_stp, encoding="utf-8").read())
            except Exception: _prev = None
        if _prev and _prev.get("msg","") != (text or "")[:300] and (_tnow - _prev.get("t", 0)) <= 120:  # JACK_TUNE_LERN2
            _gemeinsam = _toks & set(_prev.get("toks", []))
            _expl = any(w in t for w in ("hoer auf", "nicht fragen", "sagte doch", "falsch", "nicht so"))
            if _gemeinsam or _expl:
                _pair = {"ts": _jt2.strftime("%Y-%m-%d %H:%M:%S"), "original": _prev.get("msg", ""), "korrektur": (text or "")[:300], "explizit": bool(_expl), "quelle": "live"}
                with open(J + "/reports/korrekturen.jsonl", "a", encoding="utf-8") as _kf:
                    _kf.write(_jl.dumps(_pair, ensure_ascii=False) + chr(10))
        open(_stp, "w", encoding="utf-8").write(_jl.dumps({"t": _tnow, "msg": (text or "")[:300], "toks": list(_toks)[:20]}, ensure_ascii=False))
    except Exception:
        pass
    if ("zehn punkte" in t or "10 punkte" in t or "punkte auf" in t) and ("erzaehl" not in t):  # JACK_TUNE_GATE1
        pts=[
            "Temp und Akku Honor messen",
            "Temp und Akku Xiaomi messen",
            "SSH zu Xiaomi pruefen",
            "sv-Status telegram, waechter, cortex, missions sagen",
            "Speicher Honor sagen",
            "Speicher Xiaomi sagen",
            "letzte Graph-Knoten lesen",
            "mit dir ueber Groq sprechen",
        ]
        lines=["Echt sind %d. Mehr waere erfunden."%len(pts)]
        for k,x in enumerate(pts,1):
            lines.append("%d. %s"%(k,x))
        return "\n".join(lines)
    _tb=_tools(text)
    try:
        import jack_log as _jl
        if hasattr(_jl,"log_decision_event"):
            _tn = _tool_name(text) if _tb else None
            _jl.log_decision_event(text,"keyword","tool" if _tb else "talk",
                ["sammel_alles","daten_alter","bat_xiaomi","bat_honor","bat_beide",
                 "graph_knoten","ssh_xiaomi","sv_status","df_xiaomi","df_honor",
                 "kiste_liste","talk"], tool=_tn)
    except Exception:
        pass  # JACK_TUNE_LOGEV
    if _tb: return _tb
    raw=(text or "").strip()
    low=raw.lower()
    if low.startswith("merk dir") or low.startswith("merke dir"):
        body=raw.split(":",1)[-1] if ":" in raw else raw.split("dir",1)[-1]
        body=body.strip(" .")
        name,wert= (body.split("=",1)+["ja"])[:2] if "=" in body else (body,"ja")
        name=name.strip()[:48]; wert=wert.strip()[:80]
        if name:
            try:
                import jack_graph as _g
                _g.put_node("fakt", name, wert, "chat")
                return "Steht: "+name+"="+wert
            except Exception as e:
                return "Graph-Schreibfehler: "+str(e)[:80]
    # JACK_TUNE_MERK
    low2=low
    if "ich fahre" in low2 or "mein auto" in low2 or "meinen passat" in low2 or "einen passat" in low2:
        try:
            import jack_graph as _g
            wert=raw
            for p in ("ich fahre ","ich fahre einen ","mein auto ist ","meinen "):
                if p in low2:
                    i=low2.find(p); wert=raw[i+len(p):].strip(" .")[:80]; break
            if wert:
                _g.put_node("fakt","Auto",wert,"chat")
        except Exception:
            pass
    # JACK_TUNE_EDGE
    if (not low.startswith(("was ","wie ","wer ","wo ","warum ","wieso "))) and low.startswith("mein ") and " ist " in low:
        rest=raw[4:].strip()
        i=rest.lower().find(" ist ")
        if i>0:
            name=rest[:i].strip()[:48]; wert=rest[i+5:].strip(" .")[:80]
            if name and wert:
                try:
                    import jack_graph as _g
                    nid=_g.put_node("fakt", name, wert, "chat")
                    did=_g.put_node("person", "Dima", "owner", "chat")
                    _g.put_edge(did, "hat", nid, "chat")
                    return "Steht: "+name+"="+wert
                except Exception as e:
                    return "Graph-Schreibfehler: "+str(e)[:80]
    if t.startswith("was_ist") or t.startswith("was ist") or "was ist mein" in (text or "").lower():
        try:
            import jack_graph as _g
            r=(_g.recall(text) or "")
            facts=[ln[5:] for ln in r.splitlines() if ln.startswith("fakt ")]
            toks=[w for w in (text or "").lower().replace("ä","ae").split() if len(w)>3 and w not in ("was","ist","mein","eine","einen","bitte")]
            pick=None
            for f in facts:
                fl=f.lower()
                if any(w in fl for w in toks):
                    pick=f; break
            if pick is None and len(facts)==1:
                pick=facts[0]
            if pick:
                return pick.replace("="," = ",1)
        except Exception:
            pass
    # JACK_TUNE_WASIST
    if any(x in t for x in ("du bist jack","wer bist du","wer bist du eigentlich")):
        return "JACK. Dimas System auf Honor, Xiaomi als Arm. Kein Assistent."
    _bezug=any(w in t for w in ("mein hund","dein hund","sein hund","hast du","habe ich","hast du einen","kein hund","keinen hund"))
    if (("hund" in t) or ("rex" in t)) and _bezug:  # JACK_TUNE_HUNDREF
        try:
            import jack_graph as _g
            r=(_g.recall(text) or "")
            if "Hund=ja" in r: return "Ja."
            if "Hund=nein" in r or "hund=nein" in r.lower(): return "Nein. Kein Hund."
        except Exception:
            pass
        return "Nein. Kein Hund."  # JACK_TUNE_HUNDGRAPH
    # JACK_TUNE_EDGE_FREE: freie Aussage ohne Prefix
    import re as _re
    _free = _re.match(
        r'^(ich habe|ich hab|ich bin|ich mag|ich liebe|meine? .+ ist|meine? .+ heisst|meine? .+ heißt)\b',
        low)
    if _free and len(raw.split()) >= 3:
        try:
            import jack_graph as _g
            _ents = raw.strip(" .").split(None, 4)
            _name = " ".join(_ents[2:4]).strip()[:48] if len(_ents) >= 3 else raw[len(_free.group()):].strip()[:48]
            _wert = " ".join(_ents[4:]).strip()[:80] if len(_ents) >= 5 else "ja"
            if _name:
                nid = _g.put_node("fakt", _name, _wert, "chat")
                did = _g.put_node("person", "Dima", "owner", "chat")
                _g.put_edge(did, "hat", nid, "chat")
        except Exception:
            pass
    # JACK_TUNE_TLNARROW: kein Pflicht-Gegenfrage-Satz
    return None
_LAST=""
def talk_scrub(s):
    raw=str(s or "").strip()
    t=norm(raw)
    if any(x in t for x in ("muss nachsehen","im log nachsehen","im log nachschauen","fehlt im log","aus den logs","aus den vorhandenen logs")):
        return "Kein Werkzeug fuer den Satz."  # JACK_TUNE_F5LOG
    if t.startswith(("na dima","na klar","na ","ach dima","alles klar bei","hey dima")):
        rest=raw.replace("!",".").split(".",1)
        if len(rest)>1 and len(rest[1].strip())>12:
            return rest[1].strip()
    return raw
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
    loc=talk_local(text)
    if loc: return loc
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
    _pub=open(J+"/jack_publish.py",encoding="utf-8",errors="ignore").read()
    _g="live" if "git push origin main" in _pub else "tot"
    a=["Ist-Zustand:","SSH Xiaomi: "+str(h.get("ssh_xiaomi")),"Focus "+str(t.get("focus_sleep_s"))+"s, Genesis "+str(t.get("genesis_skip"))+", Idle "+str(t.get("autolearn_idle_s"))+"s","Marks: "+", ".join((k+":ja" if v else k+":nein") for k,v in m.items()),"Beats: "+", ".join(k+" "+str(v)+"s" for k,v in hb.items()),"Git-Push: "+_g+"."]  # JACK_TUNE_GITDYN
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

def strip_lane_tags(s):
    """JACK_TUNE_LANESTRIP: [[LANE:...]] nie an User."""
    if not s: return s
    import re
    s=re.sub(r"^\[\[?LANE:[A-Z]+\]\]?\s*", "", str(s))
    s=re.sub(r"\[\[?LANE:[A-Z]+\]\]?\s*", "", s)
    return s.strip()

def apply_lane(llm_text, user_text):
    # JACK_TUNE_LANEUSER
    lane=classify(user_text)
    if lane=="TALK":
        lane=None
    if False:
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
    return talk_scrub(strip_lane(llm_text or ""))

# JACK_TUNE_PACK517
