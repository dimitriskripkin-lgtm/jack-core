MODULE_VERSION=1
import os
J='/data/data/com.termux/files/home/jack'
M=os.path.join(J,'missions')
def allow():
    if os.path.isfile(os.path.join(M,'STOP')): return False
    def n(s):
        d=os.path.join(M,s)
        return len([x for x in os.listdir(d) if x.endswith('.json')]) if os.path.isdir(d) else 0
    if n('pending')>=25: return False
    if n('fail')>=15: return False
    return True
