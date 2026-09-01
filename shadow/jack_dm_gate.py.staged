import os,time
P="/data/data/com.termux/files/home/jack/.deadman_last_tg"
MIN=10800
def allow(min_s=MIN):
    n=time.time()
    try:
        if os.path.isfile(P) and n-os.path.getmtime(P)<min_s:
            return False
    except Exception:
        pass
    try: open(P,"w").write(str(int(n)))
    except Exception: pass
    return True
