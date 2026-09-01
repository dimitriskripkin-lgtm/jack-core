#!/usr/bin/env python3
import json,os,re,sys
J="/data/data/com.termux/files/home/jack"
S=J+"/missions/talk_samples.jsonl"
FAM={
 "opener": re.compile(r"^\s*(na\s+klar|na,?\s+dima|was geht bei|was liegt)", re.I),
 "tour": re.compile(r"nachtschicht|auf achse|\bsprinter\b|\btour\b", re.I),
 "klarspam": re.compile(r"\b[Kk]lar[,!\s]", re.I),
 "predigen": re.compile(r"keine frage, die mich weiterbringt|ueblichen (stress|kram)", re.I),
 "musik": re.compile(r"was (hoerst|hoerst du gerade)|welche musik (laeuft|hoerst)", re.I),
 "kopf": re.compile(r"im kopf|beschaeftigt dich|schwebt dir|festnageln", re.I),
 "dritte": re.compile(r"\ban JACK\b|fuer JACK|wir an JACK", re.I),
 "emoji_spam": re.compile(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF]{3,}", re.U),
 "meta_jack": re.compile(r"als (ki|ki-system|assistent)|meine (ki|funktion)|ich bin (eine? )?(ki|sprachmodell|assistent)", re.I),
 "frage_reflex": re.compile(r"was kann ich (noch |fuer dich |)?tun\?$|wie kann ich (dir |)?helfen\??$|womit kann ich", re.I),
 "lkw_reflex": re.compile(r"\b(lkw|lastwagenfahrer|trucker|fernfahrer)\b", re.I),
 "haessliche_gross": re.compile(r"^(Als KI|Als Sprachmodell|Als Assistent)", re.M),
 "zu_lang": None,
}  # JACK_TUNE_ICHBIN

def rows(n=30):
    if not os.path.isfile(S): return []
    ls=open(S,encoding="utf-8",errors="ignore").read().splitlines()
    out=[]
    for line in ls[-n:]:
        try: out.append(json.loads(line))
        except Exception: pass
    return out
def score(text, user_text=""):
    t=str(text or "")
    u=str(user_text or "")
    hits=[]
    for k,rx in FAM.items():
        if rx is None: continue
        if not rx.search(t): continue
        # tour: nur breach wenn User es NICHT selbst erwähnt hat
        if k == "tour" and rx.search(u): continue
        # haessliche_gross: kein breach bei technischen Outputs (slash commands)
        if k == "haessliche_gross" and u.strip().startswith("/"): continue
        hits.append(k)
    if len(t) > 400: hits.append("zu_lang")
    return hits
def main():
    rs=rows(40)
    bad=[]
    for r in rs:
        h=score(r.get("j",""), r.get("u",""))
        if h: bad.append((r.get("u","")[:40], h, r.get("j","")[:80]))
    print("samples", len(rs), "breaches", len(bad))
    for u,h,j in bad[-12:]:
        print("HIT", h, "|", u, "|", j)
    return 1 if bad else 0
if __name__=="__main__":
    sys.exit(main())
