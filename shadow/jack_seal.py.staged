#!/data/data/com.termux/files/usr/bin/python3
import os, json, subprocess, sys
J="/data/data/com.termux/files/home/jack"
P=J+"/missions/pending"
D=J+"/missions/done"
F=J+"/missions/fail"
R=J+"/jack_mission_runner.py"
os.makedirs(P, exist_ok=True)
# alte Seal-Ergebnisse entfernen damit wirklich neu gemessen wird
for folder in (D, F, P):
    if not os.path.isdir(folder):
        continue
    for n in list(os.listdir(folder)):
        if n.startswith("seal-") and n.endswith(".json"):
            try: os.remove(os.path.join(folder, n))
            except Exception: pass
pack=[
 {"id":"seal-chrome","act":"no_chrome_src","expect":"PASS"},
 {"id":"seal-fact","act":"fact","expect":"PASS"},
 {"id":"seal-c-fact","act":"classify_is","text":"Ist Zustand?","expect":"FACT"},
 {"id":"seal-c-diag","act":"classify_is","text":"analysiere deinen eigenen Code","expect":"DIAG"},
 {"id":"seal-c-talk","act":"classify_is","text":"Frag mich irgendwas was dich interessiert","expect":"TALK"},
 {"id":"seal-explain","act":"explain_ok","expect":"PASS"},
 {"id":"seal-sv-tg","act":"sv_ok","service":"jack_telegram","expect":"PASS"},
 {"id":"seal-sv-mi","act":"sv_ok","service":"jack_missions","expect":"PASS"},
 {"id":"seal-sv-wa","act":"sv_ok","service":"jack_waechter","expect":"PASS"},
 {"id":"seal-hb-mi","act":"hb_ok","service":"jack_missions","max_age_s":300,"expect":"PASS"},
 {"id":"seal-hb-tg","act":"hb_ok","service":"jack_telegram","max_age_s":300,"expect":"PASS"},

]
for m in pack:
    open(os.path.join(P, m["id"]+".json"),"w",encoding="utf-8").write(json.dumps(m,ensure_ascii=False)+"\n")
r=subprocess.run([sys.executable,R,"once"],cwd=J)
fail=sorted(x for x in os.listdir(F) if x.endswith(".json")) if os.path.isdir(F) else []
print("SEAL rc", r.returncode, "fail", fail)
sys.exit(0 if r.returncode==0 and not fail else 1)
