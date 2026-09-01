MODULE_VERSION = 1
import os
J="/data/data/com.termux/files/home/jack"
SH=J+"/shadow"
def preview():
    out=[]
    if not os.path.isdir(SH): return "(kein shadow)"
    for n in sorted(os.listdir(SH)):
        if not n.endswith(".staged"): continue
        live=os.path.join(J, n[:-7])
        st=os.path.join(SH,n)
        out.append(n+" -> "+("LIVE" if os.path.isfile(live) else "NEU"))
        try:
            a=open(st,encoding="utf-8",errors="ignore").read().splitlines()
            b=open(live,encoding="utf-8",errors="ignore").read().splitlines() if os.path.isfile(live) else []
            if a==b: out.append("  identisch")
            else:
                out.append("  staged %s zeilen, live %s"%(len(a),len(b)))
        except Exception as e:
            out.append("  "+str(e)[:60])
    return "\n".join(out) or "(nichts staged)"
