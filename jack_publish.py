#!/usr/bin/env python3
"""Veroeffentlicht SANITIERTEN JACK-Kontext oeffentlich fuer Claude/andere KIs.
NIEMALS Secrets/Keys/Tokens - nur Struktur, Status, Logbuch-Zusammenfassung."""
import os, subprocess, datetime, re
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None
H=os.path.expanduser("~/jack")
OUT=os.path.expanduser("~/jack-context")
BAD=re.compile(r'(AQ\.[A-Za-z0-9_-]{10}|sk_[a-zA-Z0-9]{10}|AIza[A-Za-z0-9_-]{10}|gh[ps]_[A-Za-z0-9]{10}|[0-9]{9,10}:AA[A-Za-z0-9_-]{10})')

def sh(c,cwd=None):
    try: return subprocess.run(c,shell=True,capture_output=True,text=True,timeout=25,cwd=cwd).stdout.strip()
    except Exception: return ""

def _lade_filter():
    """CRIT-P4: private Begriffe NIE im Repo. Fehlt die Datei -> fail-closed."""
    fp = os.path.expanduser("~/.jack_private_filter")
    if not os.path.isfile(fp) or os.path.islink(fp): return None
    w = [z.strip() for z in open(fp, encoding="utf-8") if z.strip()]
    return w or None

def _filter_private(t):
    worte = _lade_filter()
    if worte is None:
        return "[EXPORT BLOCKIERT: ~/.jack_private_filter fehlt oder leer]"
    out = []; skip = False
    for l in t.split("\n"):
        if any(x in l for x in worte):
            skip = True; out.append("[PRIVAT GEFILTERT]"); continue
        if skip and l.startswith("- ") or (skip and l.strip() == ""): continue
        skip = False; out.append(l)
    return "\n".join(out)

def scrub(t):
    return "\n".join("[ZEILE ENTFERNT: Secret]" if BAD.search(l) else l for l in t.split("\n"))

def _copytree_scrub(src, dst):
    if not os.path.isdir(src): return
    os.makedirs(dst, exist_ok=True)
    for fn in os.listdir(src):
        sp=os.path.join(src,fn)
        if os.path.isfile(sp) and fn.rsplit(".",1)[-1] in ("py","txt","md","log","json"):
            try: open(os.path.join(dst,fn),"w").write(scrub(open(sp,encoding="utf-8",errors="ignore").read()))
            except Exception as _e:
                import jack_log; jack_log.log_decision('SILENT-FAIL jack_publish', str(_e)[:120])

def build():
    sh(f"cd {H} && python3 jack_snapshot.py")
    p=[f"# JACK LIVE-KONTEXT (auto, {datetime.datetime.now().isoformat()})\n"]
    try: p.append(open(f"{H}/jack_context.md").read())
    except Exception as e: p.append(f"(snapshot fehlt: {e})")
    p.append("\n## Letzte 20 Aktionen (Logbuch)\n")
    p.append(sh(f"tail -20 {H}/jack_decisions.log") or "(kein Log)")
    try:
        import jack_budget; p.append("\n## Budget heute\n"+jack_budget.status())
    except Exception: pass
    text=_filter_private(scrub("\n".join(p)))
    os.makedirs(OUT,exist_ok=True)
    open(f"{OUT}/context.md","w").write(text)
    _copytree_scrub(os.path.expanduser("~/jack_werkstatt"), f"{OUT}/werkstatt")
    _copytree_scrub(os.path.expanduser("~/jack_skills"), f"{OUT}/skills")
    try: open(f"{OUT}/decisions.log","w").write(scrub(open(f"{H}/jack_decisions.log").read()))
    except Exception: pass
    try: open(f"{OUT}/CLAUDE.md","w").write(scrub(open(f"{H}/CLAUDE.md").read()))
    except Exception: pass
    open(f"{OUT}/module_list.txt","w").write(sh(f"ls -la {H}/*.py"))
    return text

def push():  # JACK_TUNE_CRIT002
    """Context bauen und ins oeffentliche Repo pushen."""
    try:
        import hashlib as _hh, os as _os
        _hp="/data/data/com.termux/files/home/jack/.publisher_hash"
        _h=_hh.sha256()
        for _f in ("jack_decisions.log","CLAUDE.md","jack_skills.db"):  # JACK_TUNE_HASH2
            _p="/data/data/com.termux/files/home/jack/"+_f
            if _os.path.isfile(_p):
                _st=_os.stat(_p); _h.update(str(_st.st_mtime_ns).encode()+str(_st.st_size).encode())
        _sig=_h.hexdigest(); _old=open(_hp).read().strip() if _os.path.isfile(_hp) else ""
        if _sig==_old: return "SKIP-UNCHANGED"  # JACK_TUNE_HASH
        open(_hp,"w").write(_sig)
    except Exception:
        pass
    build()
    import subprocess, os
    OUT = os.path.expanduser("~/jack-context")
    r = subprocess.run(
        "git add -A && git commit -m \'auto-context\' && git push origin main",
        shell=True, capture_output=True, text=True, cwd=OUT, timeout=30
    )
    if r.returncode == 0:
        import jack_log; jack_log.log_decision("PUBLISHER-PUSH", "OK")
        return "GEPUSHT"
    elif "nothing to commit" in r.stdout + r.stderr:
        return "NICHTS NEU"
    else:
        import jack_log; jack_log.log_decision("PUBLISHER-FEHLER", r.stderr[:100])
        return f"FEHLER: {r.stderr[:100]}"

if __name__=="__main__":
    print(push() or "(nichts neu)")
