MODULE_VERSION = 1
import uuid
_cur="-"
def new(mid=""):
    global _cur
    _cur=(str(mid)[:40]+"-"+uuid.uuid4().hex[:8]) if mid else uuid.uuid4().hex[:12]
    try:
        with open(LASTC,"w") as _lf: _lf.write(_aj.dumps({"corr":_cur,"ts":_at.time()}))
    except Exception: pass
    return _cur
def get():
    return _cur
def tag(s):
    return "[%s] %s"%(_cur,s)

# JACK_TUNE_AUDIT1 — Sequenz + Journal (17.09.)
LASTC="/data/data/com.termux/files/home/jack/reports/last_corr.json"
def active(max_age=900):
    if _cur!="-": return _cur
    try:
        d=_aj.loads(open(LASTC,encoding="utf-8").read())
        if _at.time()-d.get("ts",0)<=max_age: return d.get("corr","-")
    except Exception: pass
    return "-"
import json as _aj, fcntl as _af, time as _at, os as _ao
AUDIT="/data/data/com.termux/files/home/jack/reports/audit_journal.jsonl"
SEQF="/data/data/com.termux/files/home/jack/reports/audit_seq.txt"
def _seq_next():
    fd=_ao.open(SEQF,_ao.O_RDWR|_ao.O_CREAT,0o600)
    try:
        _af.flock(fd,_af.LOCK_EX)
        raw=_ao.read(fd,32).decode().strip()
        n=(int(raw) if raw.isdigit() else 0)+1
        _ao.lseek(fd,0,0); _ao.ftruncate(fd,0); _ao.write(fd,str(n).encode())
    finally:
        _af.flock(fd,_af.LOCK_UN); _ao.close(fd)
    return n
def audit(aktion,ziel,grund,aktor=""):
    try:
        rec={"seq":_seq_next(),"ts":_at.strftime("%Y-%m-%dT%H:%M:%S"),"corr":active(),"aktor":aktor or "?","aktion":aktion,"ziel":ziel,"grund":grund[:200]}
        with open(AUDIT,"a",encoding="utf-8") as f: f.write(_aj.dumps(rec,ensure_ascii=False)+chr(10))
        return rec["seq"]
    except Exception:
        return -1
