# JACK_TUNE_UI_LEARN — Dump speichern, Heuristik-Kandidaten, kein Auto-Write ohne Gate
import os, re, json, time
J="/data/data/com.termux/files/home/jack"
OUT=os.path.join(J,"ui_learn")
os.makedirs(OUT, exist_ok=True)

def dump_and_candidates(tag="anon"):
    import jack_ui_session as ui
    xml=(ui.ui_dump(max_chars=120000).get("xml") or "")
    ts=time.strftime("%Y%m%d_%H%M%S")
    path=os.path.join(OUT, f"{ts}_{tag}.xml")
    open(path,"w",encoding="utf-8").write(xml)
    cands=[]
    for n in re.findall(r"<node[^>]+>", xml):
        m=re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
        if not m: continue
        x1,y1,x2,y2=map(int,m.groups())
        cy=(y1+y2)//2; cx=(x1+x2)//2
        cd=(re.search(r'content-desc="([^"]*)"', n) or type("",(),{"group":lambda s,i:""})()).group(1)
        tx=(re.search(r'text="([^"]*)"', n) or type("",(),{"group":lambda s,i:""})()).group(1)
        rid=(re.search(r'resource-id="([^"]*)"', n) or type("",(),{"group":lambda s,i:""})()).group(1)
        cls=(re.search(r'class="([^"]*)"', n) or type("",(),{"group":lambda s,i:""})()).group(1)
        clk='clickable="true"' in n
        score=0
        low=(cd+" "+tx+" "+rid).lower()
        if "search" in low or "such" in low: score+=3
        if "EditText" in cls: score+=5
        if clk: score+=1
        if tx and cy<400: score+=2
        if score and 40<cy<2200:
            cands.append({"score":score,"cx":cx,"cy":cy,"cd":cd[:60],"tx":tx[:40],"rid":rid[:50],"cls":cls.split(".")[-1]})
    cands.sort(key=lambda x:-x["score"])
    meta={"tag":tag,"ts":ts,"xml":path,"cands":cands[:12]}
    mp=os.path.join(OUT, f"{ts}_{tag}.json")
    json.dump(meta, open(mp,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
    return meta

if __name__=="__main__":
    import sys
    tag=sys.argv[1] if len(sys.argv)>1 else "manual"
    m=dump_and_candidates(tag)
    print("xml", m["xml"])
    print("top")
    for c in m["cands"][:6]:
        print(c["score"], c["cy"], c["cls"], c["cd"] or c["tx"] or c["rid"])
