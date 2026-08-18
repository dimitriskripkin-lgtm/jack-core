#!/usr/bin/env python3
"""JACK Oracle - bidirektionaler Kanal zwischen Claude und JACK via GitHub."""
import os, json, subprocess, time, urllib.request, hmac, hashlib, datetime
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

REPO = "https://raw.githubusercontent.com/dimitriskripkin-lgtm/jack-commands/master/jack_cmd.json"
LOCAL = os.path.expanduser("~/jack-commands")
SEEN = os.path.expanduser("~/jack/.oracle_last_uuid")
RATE_LOG = []
RATE_LIMIT = 10  # Max Befehle pro Stunde

def get_oracle_secret():
    try:
        s = open(os.path.expanduser("~/.jack_secrets")).read()
        for l in s.split(chr(10)):
            if "ORACLE_SECRET=" in l:
                return l.split("=",1)[1].strip().strip('"')
    except Exception as _le: _jlog and _jlog.fehler("oracle","unbenannt",_le)
    return None

def verify_sig(cmd, uuid, ts, sig):
    secret = get_oracle_secret()
    if not secret: return False, "Kein Secret konfiguriert"
    if not sig: return False, "Keine Signatur"
    msg = f"{uuid}:{cmd}:{ts}".encode()
    expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return False, "Signatur ungueltig"
    return True, "OK"

def check_rate_limit():
    global RATE_LOG
    now = datetime.datetime.now()
    RATE_LOG = [t for t in RATE_LOG if (now-t).seconds < 3600]
    if len(RATE_LOG) >= RATE_LIMIT:
        return False, f"Rate-Limit: {RATE_LIMIT}/h erreicht"
    RATE_LOG.append(now)
    return True, "OK"

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
    "dienste": "sv status jack_cortex jack_telegram jack_waechter ollama",
    "ram": "free -h",
    "speicher": "df -h /data/data/com.termux/files",
    "fehler": "python3 ~/jack/jack_errors_status.py",
    "datum": "date",
    "uptime": "uptime",
    "modelle": "ollama list",
    "budget": "python3 ~/jack/jack_budget_status.py",
    "ram_check": "free -h",
    "log": "tail -10 /data/data/com.termux/files/home/jack/jack_decisions.log",
}

def resolve_alias(cmd):
    low = cmd.strip().lower()
    if low in ALIASES:
        return ALIASES[low], low
    return cmd, cmd

SUBCMD_ALLOW = {
    "git": ["status", "log", "diff", "show", "branch", "ls-files", "rev-parse", "describe"],
    "sv": ["status"],
    "python3": ["--version", "-V"],
    "ollama": ["list", "ps"],
    "sqlite3": None,
}
PFAD_TABU = [".ssh", ".jack_secrets", "id_jack", "known_hosts", "authorized_keys",
             ".jack_private_filter", "/data/data/com.termux/files/usr/etc",
             "..", "~/.", "/proc/self/environ"]

def is_safe(cmd):
    """CRIT-005: Allowlist auf Tool UND Subcommand-Ebene, plus Pfad-Tabus.
    Default deny. Unbekanntes Tool oder unbekannter Subcommand -> BLOCKIERT."""
    KILL = ["rm -rf", "rmtree", "os.remove", "os.unlink", "drop table", "delete from",
            "mkfs", "dd if=", "eval(", "exec(", "os.environ", "jack_secrets", "api_key",
            ".ssh/", "urllib", "requests.", "socket", "curl", "wget", "nc ", "netcat",
            "|", "&&", "||", ";", "$(", "`", ">", ">>", "chmod", "chown", "mv ", "cp "]
    ALLOW = ["echo", "sv", "free", "df", "ls", "cat", "git", "ollama", "sqlite3",
             "python3", "termux-battery-status", "termux-wifi-connectioninfo",
             "pwd", "date", "uptime", "grep", "wc", "head", "tail"]
    low = cmd.lower()
    for k in KILL:
        if k in low: return False, "KILL: " + k
    for t in PFAD_TABU:
        if t in low: return False, "TABU-Pfad: " + t
    teile = cmd.strip().split()
    if not teile: return False, "Leerer Befehl"
    first = teile[0]
    if first not in ALLOW: return False, "Nicht auf Whitelist: " + first
    if first == "python3":
        ok, grund = _py_skript_ok(teile)
        if not ok: return False, grund
        return True, "OK"
    if first in SUBCMD_ALLOW:
        erlaubt = SUBCMD_ALLOW[first]
        if erlaubt is None:
            return False, "Tool " + first + " nur mit expliziter Freigabe"
        sub = teile[1] if len(teile) > 1 else ""
        if sub not in erlaubt:
            return False, "Subcommand nicht erlaubt: " + first + " " + (sub or "(leer)")
    return True, "OK"

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
    # Rate-Limit pruefen
    ok, reason = check_rate_limit()
    if not ok:
        push_result(uuid, cmd, "BLOCKIERT: "+reason, "blocked")
        return
    # HMAC-Signatur pruefen
    sig = d.get("sig", "")
    if sig:  # Wenn sig vorhanden, muss sie stimmen
        ok, reason = verify_sig(cmd, uuid, d.get("ts",""), sig)
        if not ok:
            push_result(uuid, cmd, "BLOCKIERT: "+reason, "blocked")
            _telegram_send("Oracle BLOCKIERT: " + reason)
            return
    cmd, alias = resolve_alias(cmd)
    orig_cmd = alias  # Alias-Name fuer Telegram
    save_uuid(uuid)
    try:
        import jack_log; jack_log.log_decision("ORACLE-EINGANG",f"{uuid[:8]}: {cmd[:80]}")
    except Exception as _le: _jlog and _jlog.fehler("oracle","unbenannt",_le)
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
            except Exception as _le: _jlog and _jlog.fehler("oracle","unbenannt",_le)
        time.sleep(60)


JACK_DIR = os.path.expanduser("~/jack")

def _py_skript_ok(teile):
    """python3 darf NUR .py-Skripte aus ~/jack starten. Kein -c, kein -m,
    keine Traversierung, keine Symlinks. Argumente danach nur [A-Za-z0-9_.-]."""
    if len(teile) < 2:
        return False, "python3 ohne Skript nicht erlaubt"
    ziel = teile[1]
    if ziel.startswith("-"):
        return False, "python3-Flags nicht erlaubt: " + ziel
    pfad = os.path.realpath(os.path.expanduser(ziel))
    if not pfad.endswith(".py"):
        return False, "Nur .py-Skripte: " + os.path.basename(pfad)
    if os.path.dirname(pfad) != os.path.realpath(JACK_DIR):
        return False, "Skript ausserhalb ~/jack: " + pfad[:60]
    if os.path.basename(pfad) not in SKRIPT_ALLOW:
        return False, "Skript nicht freigegeben: " + os.path.basename(pfad)
    if not os.path.isfile(pfad):
        return False, "Skript existiert nicht"
    if os.path.islink(os.path.expanduser(ziel)):
        return False, "Symlink als Skript blockiert"
    for a in teile[2:]:
        if not all(ch.isalnum() or ch in "_.-" for ch in a):
            return False, "Unerlaubtes Argument: " + a[:30]
    return True, "OK"

SKRIPT_ALLOW = {
    "jack_wissen_ernte.py",
    "jack_errors_status.py",
    "jack_budget_status.py",
    "jack_freigabe.py",
    "jack_stress.py",
}
