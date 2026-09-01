MODULE_VERSION = 1
import os
J="/data/data/com.termux/files/home/jack"
def text(n=40):
    p=J+"/waechter.log"
    if not os.path.isfile(p): p=J+"/jack_main.log"
    try:
        lines=open(p,encoding="utf-8",errors="ignore").read().splitlines()
        return "\n".join(lines[-n:])
    except Exception as e:
        return str(e)
