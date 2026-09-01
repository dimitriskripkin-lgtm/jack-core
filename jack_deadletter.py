MODULE_VERSION = 1
import json,os,shutil
J="/data/data/com.termux/files/home/jack"
C=J+"/missions/dead_counts.json"
D=J+"/missions/deadletter"
N=3
def _load():
    try:
        d=json.load(open(C,encoding="utf-8")); return d if isinstance(d,dict) else {}
    except Exception:
        return {}
def bump(mid, fail_path=None):
    d=_load(); k=str(mid); d[k]=int(d.get(k) or 0)+1
    os.makedirs(J+"/missions",exist_ok=True)
    open(C,"w",encoding="utf-8").write(json.dumps(d))
    if d[k]>=N and fail_path and os.path.isfile(fail_path):
        os.makedirs(D,exist_ok=True)
        shutil.move(fail_path, os.path.join(D, os.path.basename(fail_path)))
        return True
    return False
