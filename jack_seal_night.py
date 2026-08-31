#!/data/data/com.termux/files/usr/bin/python3
import os, json, subprocess, sys
J="/data/data/com.termux/files/home/jack"
P=J+"/missions/pending"
D=J+"/missions/done"
F=J+"/missions/fail"
R=J+"/jack_mission_runner.py"
os.makedirs(P, exist_ok=True)
for folder in (D, F, P):
    if not os.path.isdir(folder): continue
    for n in list(os.listdir(folder)):
        if n.startswith("night-") and n.endswith(".json"):
            try: os.remove(os.path.join(folder, n))
            except Exception: pass
svs=["jack_telegram","jack_missions","jack_waechter","jack_cortex","jack_autolearn","jack_publisher","jack_focus_monitor"]
hbs=["jack_telegram","jack_missions","jack_waechter","jack_cortex","jack_publisher","jack_autolearn"]
pack=[]
for s in svs:
    pack.append({"id":"night-sv-"+s,"act":"sv_ok","service":s,"expect":"PASS"})
for s in hbs:
    pack.append({"id":"night-hb-"+s,"act":"hb_ok","service":s,"max_age_s":900,"expect":"PASS"})
pack += [
 {"id":"night-chrome","act":"no_chrome_src","expect":"PASS"},
 {"id":"night-fact","act":"fact","expect":"PASS"},
]
for m in pack:
    open(os.path.join(P,m["id"]+".json"),"w",encoding="utf-8").write(json.dumps(m,ensure_ascii=False)+"\n")
r=subprocess.run([sys.executable,R,"once"],cwd=J)
fail=sorted(x for x in os.listdir(F) if x.endswith(".json")) if os.path.isdir(F) else []
print("NIGHT rc", r.returncode, "fail", fail)
sys.exit(0 if r.returncode==0 and not fail else 1)
