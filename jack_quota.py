MODULE_VERSION = 1
import os,subprocess,time
J="/data/data/com.termux/files/home/jack"
ST=J+"/.quota_last"
LIM=1024*1024  # JACK_TUNE_QUOTA1G (24.10.2026): 500 MB war dauerhaft ueberschritten (703 MB) und meldete bei jedem Xiaomi-Aussetzer ohne Aussage
def maybe():
    now=time.time()
    try:
        if now-os.path.getmtime(ST)<3600: return
    except Exception:
        pass
    kb=0
    try:
        r=subprocess.run(["du","-sk",J],capture_output=True,text=True,timeout=20)
        kb=int((r.stdout or "0").split()[0])
    except Exception:
        return
    open(ST,"w").write(str(int(now)))
    if kb>LIM:
        try:
            import jack_telegram as tg
            msg="JACK-Ordner %s MB, Warnschwelle %s MB"%(kb//1024, LIM//1024)  # JACK_TUNE_QUOTA1G
            if hasattr(tg,"send"): tg.send(msg)
            elif hasattr(tg,"send_message"): tg.send_message(msg)
        except Exception:
            pass
    return kb
