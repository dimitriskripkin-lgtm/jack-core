#!/usr/bin/env python3
import json,os,re,sys
J="/data/data/com.termux/files/home/jack"
S=J+"/missions/talk_samples.jsonl"
FAM={
 "opener": re.compile(r"^\s*(na\s+klar|na,?\s+dima|was geht bei|was liegt)", re.I),
 "tour": re.compile(r"nachtschicht|auf achse|\bsprinter\b|\btour\b", re.I),
 "klarspam": re.compile(r"\b[Kk]lar[,!\s]", re.I),
 "predigen": re.compile(r"keine frage, die mich weiterbringt|ueblichen (stress|kram)", re.I),
 "musik": re.compile(r"was hoerst|was liegst du|auf dem herzen|was hoerst du gerade|welche musik", re.I),
 "kopf": re.compile(r"im kopf|beschaeftigt dich|schwebt dir|festnageln", re.I),
 "dritte": re.compile(r"\ban JACK\b|fuer JACK|wir an JACK", re.I),
}  # JACK_TUNE_ICHBIN

def rows(n=30):
    if not os.path.isfile(S): return []
    ls=open(S,encoding="utf-8",errors="ignore").read().splitlines()
    out=[]
    for line in ls[-n:]:
        try: out.append(json.loads(line))
        except Exception: pass
    return out
def score(text):
    t=str(text or "")
    hits=[k for k,rx in FAM.items() if rx.search(t)]
    return hits
def main():
    rs=rows(40)
    bad=[]
    for r in rs:
        h=score(r.get("j",""))
        if h: bad.append((r.get("u","")[:40], h, r.get("j","")[:80]))
    print("samples", len(rs), "breaches", len(bad))
    for u,h,j in bad[-12:]:
        print("HIT", h, "|", u, "|", j)
    return 1 if bad else 0
if __name__=="__main__":
    sys.exit(main())
