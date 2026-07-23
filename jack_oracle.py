#!/usr/bin/env python3
"""JACK Oracle - bidirektionaler Kanal zwischen Claude und JACK via GitHub."""
import os, json, subprocess, time, urllib.request

REPO = "https://raw.githubusercontent.com/dimitriskripkin-lgtm/jack-commands/master/jack_cmd.json"
LOCAL = os.path.expanduser("~/jack-commands")
SEEN = os.path.expanduser("~/jack/.oracle_last_uuid")

def fetch_cmd():
    try:
        req = urllib.request.Request(REPO, headers={"Cache-Control":"no-cache","Pragma":"no-cache"})
        return json.loads(urllib.request.urlopen(req, timeout=10).read())
    except Exception: return None

def last_uuid():
    try: return open(SEEN).read().strip()
    except: return ""

def save_uuid(uid): open(SEEN,"w").write(uid)

ALIASES = {
    "dienste": "sv status jack_cortex jack_telegram jack_autolearn jack_publisher jack_waechter jack_oracle ollama",
    "ram": "free -h",
    "speicher": "df -h /data/data/com.termux/files",
    "fehler": "python3 -c \"import sqlite3,os; con=sqlite3.connect(os.path.expanduser('~/jack/jack_errors.db')); [print(r) for r in con.execute('SELECT timestamp,module,error_msg FROM errors WHERE resolved=0 ORDER BY id DESC LIMIT 5').fetchall()]\"",
    "datum": "date",
    "uptime": "uptime",
    "modelle": "ollama list",
    "budget": "python3 -c \"import sys,os; sys.path.insert(0,os.path.expanduser('~/jack')); import jack_budget; print(jack_budget.status())\"",
    "ram_check": "free -h",
    "log": "tail -10 /data/data/com.termux/files/home/jack/jack_decisions.log",
}

def resolve_alias(cmd):
    low = cmd.strip().lower()
    if low in ALIASES:
        return ALIASES[low], low
    return cmd, cmd

def is_safe(cmd):
    KILL=["rm -rf","rmtree","os.remove","os.unlink","drop table","delete from",
          "mkfs","dd if=","eval(","exec(","os.environ","jack_secrets","api_key",
          ".ssh/","urllib","requests.","socket","curl","wget","nc ","netcat",
          "|","&&","||",";","$(","\`",">",">>"]
    # Shell-Injection-Schutz: Pipes und Chaining verbieten
    ALLOW=["echo","sv","free","df","ls","cat","git","ollama","sqlite3",
           "python3","termux-battery-status","termux-wifi-connectioninfo",
           "pwd","date","uptime","grep","wc","head","tail"]
    low=cmd.lower()
    for k in KILL:
        if k in low: return False,"KILL: "+k
    first=cmd.strip().split()[0] if cmd.strip() else ""
    if first not in ALLOW: return False,"Nicht auf Whitelist: "+first
    return True,"OK"

def run_cmd(cmd):
    try:
        r=subprocess.run(cmd,shell=True,capture_output=True,text=True,timeout=30)
        return (r.stdout+r.stderr).strip()[:2000]
    except Exception as e: return "FEHLER: "+str(e)

def _telegram_send(msg):
    try:
        import urllib.request as _u, json as _j
        secrets = open(os.path.expanduser('~/.jack_secrets')).read()
        token = [l.split('=',1)[1].strip().strip('"') for l in secrets.split(chr(10)) if 'TELEGRAM_BOT_TOKEN' in l][0]
        chat = [l.split('=',1)[1].strip().strip('"') for l in secrets.split(chr(10)) if 'TELEGRAM_CHAT_ID' in l][0]
        d = _j.dumps({'chat_id': chat, 'text': msg[:3000]}).encode()
        req = _u.Request(f'https://api.telegram.org/bot{token}/sendMessage', data=d, headers={'Content-Type':'application/json'})
        _u.urlopen(req, timeout=10)
    except Exception as e:
        print('Telegram-Fehler:', e)

def push_result(uuid,cmd,result,status):
    data={"uuid":uuid,"cmd":cmd,"status":status,"result":result,
          "ts":time.strftime("%Y-%m-%d %H:%M:%S")}
    stack_path=os.path.join(LOCAL,"jack_results_stack.json")
    try: stack=json.load(open(stack_path))
    except: stack=[]
    stack.insert(0,data)
    stack=stack[:5]
    json.dump(stack,open(stack_path,"w"),ensure_ascii=False,indent=2)
    open(os.path.join(LOCAL,"jack_result.json"),"w").write(
        json.dumps(data,ensure_ascii=False,indent=2))
    subprocess.run(
        "cd ~/jack-commands && git add jack_result.json && "
        "git commit -m 'oracle: result "+uuid[:8]+"' && git push origin master",
        shell=True,capture_output=True,timeout=30)

def cycle():
    orig_cmd = ""
    d=fetch_cmd()
    if not d: return
    uuid=d.get("uuid",""); cmd=d.get("cmd","").strip()
    if not uuid or not cmd or uuid==last_uuid(): return
    cmd, alias = resolve_alias(cmd)
    save_uuid(uuid)
    try:
        import jack_log; jack_log.log_decision("ORACLE-EINGANG",f"{uuid[:8]}: {cmd[:80]}")
    except: pass
    safe,reason=is_safe(cmd)
    if not safe:
        push_result(uuid,cmd,"BLOCKIERT: "+reason,"blocked"); return
    result=run_cmd(cmd)
    push_result(uuid,cmd,result,"ok")
    _telegram_send("Oracle [" + orig_cmd + "]:" + chr(10) + result[:2000])

if __name__=="__main__":
    print("JACK Oracle laeuft. Polling alle 60s...")
    while True:
        try: cycle()
        except Exception as e:
            try:
                import jack_log; jack_log.log_decision("ORACLE-FEHLER",str(e)[:100])
            except: pass
        time.sleep(60)
