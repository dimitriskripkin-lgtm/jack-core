MODULE_VERSION = 1
import os,time
J="/data/data/com.termux/files/home/jack"
FLAG=J+"/.xiaomi_degraded"
def set_on(v=True):
    if v: open(FLAG,"w").write(str(int(time.time())))
    elif os.path.isfile(FLAG): os.remove(FLAG)
def is_on():
    return os.path.isfile(FLAG)
