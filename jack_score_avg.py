MODULE_VERSION = 1
import json,os,time
J="/data/data/com.termux/files/home/jack"
H=J+"/jack_score_hist.jsonl"
def tick(score=None):
    if score is None:
        try:
            d=json.load(open(J+"/jack_diag_snapshot.json",encoding="utf-8"))
            score=d.get("score") or d.get("selftest") or d.get("pct")
        except Exception:
            return None
    open(H,"a",encoding="utf-8").write(json.dumps({"t":int(time.time()),"s":score})+"\n")
    rows=[]
    try:
        for line in open(H,encoding="utf-8"):
            try: rows.append(json.loads(line))
            except Exception: pass
    except Exception:
        return score
    cut=time.time()-7*86400
    vals=[r.get("s") for r in rows if r.get("t",0)>=cut and isinstance(r.get("s"),(int,float))]
    return sum(vals)/len(vals) if vals else None
