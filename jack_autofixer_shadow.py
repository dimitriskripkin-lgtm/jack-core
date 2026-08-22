#!/usr/bin/env python3
"""JACK AutoFixer mit Shadow-Execution und Ollama-Loop.
Geschlossener Lern-Kreislauf: scan errors.db -> Ollama Fix -> Shadow-Test -> Apply oder Eskalation."""
import os,sqlite3,subprocess,shutil,json,time
from datetime import datetime

DB=os.path.expanduser("~/jack/jack_errors.db")
SHADOW=os.path.expanduser("~/.prefix/tmp") if os.path.exists("/data/data/com.termux/files/usr/tmp") else os.path.expanduser("~/jack/.shadow_tmp")
BACKUP=os.path.expanduser("~/jack/backups/")
OLLAMA="http://localhost:11434/api/generate"
MODEL="llama3.2:3b"
MAX_RETRIES=3

os.makedirs(SHADOW,exist_ok=True)
os.makedirs(BACKUP,exist_ok=True)

def _log(msg,level="INFO"):
    ts=datetime.now().strftime("%H:%M:%S")
    line=f"[{ts}][SHADOW-FIXER][{level}] {msg}"
    print(line)
    try:
        import jack_log; jack_log.log_decision("SHADOW-FIXER",msg[:120])
    except Exception: pass

def _get_open_errors(limit=5):
    try:
        c=sqlite3.connect(DB)
        rows=c.execute(
            "SELECT id,module,error_type,error_msg,file_path,line_num,context "            "FROM errors WHERE resolved=0 AND file_path != '' ORDER BY timestamp DESC LIMIT ?",
            (limit,)).fetchall()
        c.close(); return rows
    except Exception as e: _log(f"DB-Fehler: {e}","ERROR"); return []

def _ollama_fix(module,err_type,err_msg,file_path,line_num,context,original):
    import urllib.request
    orig_short=original[:1500].replace("\n"," ")
    prompt=(f"Du bist JACK Bug-Fixer. Nur SEARCH/REPLACE Bloecke ausgeben."
        f" Modul: {module} Fehler: {err_type}: {err_msg} Zeile: {line_num}."
        f" Kontext: {context[:200]}. Code: {orig_short}"
        " Format: <<<<<<< SEARCH (exakter Text) ======= (neuer Text) >>>>>>> REPLACE"
        " Wenn nicht fixbar: CANNOT_FIX")
    data=json.dumps({"model":MODEL,"prompt":prompt,"stream":False}).encode()
    req=urllib.request.Request(OLLAMA,data=data,headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.loads(r.read()).get("response","").strip()
    except Exception as e: _log(f"Ollama-Fehler: {e}","ERROR"); return None

def _shadow_test(file_path,patch_response):
    try:
        import jack_patch
        shadow_path=os.path.join(SHADOW,"shadow_"+os.path.basename(file_path))
        shutil.copy2(file_path,shadow_path)
        ok,msg,preview=jack_patch.safe_patch(shadow_path,patch_response)
        if not ok: return False,f"Patch fehlgeschlagen: {msg}",None
        r=subprocess.run(["python3","-m","py_compile",shadow_path],
            capture_output=True,text=True,timeout=15)
        if r.returncode!=0: return False,f"SyntaxError: {r.stderr.strip()}",None
        return True,"Shadow OK",shadow_path
    except Exception as e: return False,str(e),None

VORSCHLAEGE = os.path.expanduser("~/jack/patch_vorschlaege")

def _sha(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""): h.update(b)
    return h.hexdigest()

def _apply(file_path, shadow_path, err_id, summary):
    """GATE CRIT-001: veraendert NIE eine Produktivdatei. Nur Vorschlag + Metadaten."""
    import uuid as _uu
    try:
        if os.path.islink(file_path) or os.path.islink(shadow_path):
            _log("Symlink erkannt - blockiert", "WARN"); return
        if not os.path.isfile(shadow_path):
            _log("Shadow fehlt - blockiert", "WARN"); return
        real = os.path.realpath(file_path)
        os.makedirs(VORSCHLAEGE, exist_ok=True); os.chmod(VORSCHLAEGE, 0o700)
        uid = _uu.uuid4().hex[:12]
        base = os.path.basename(real) + "." + uid
        ziel = os.path.join(VORSCHLAEGE, base + ".vorschlag")
        fd = os.open(ziel, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as out, open(shadow_path, "rb") as src:
            shutil.copyfileobj(src, out)
        meta = {"error_id": err_id, "source_realpath": real,
                "created_at": datetime.now().isoformat(),
                "source_sha256": _sha(real), "proposal_sha256": _sha(ziel),
                "summary": str(summary)[:300], "status": "wartet_freigabe"}
        mp = os.path.join(VORSCHLAEGE, base + ".meta.json")
        fd2 = os.open(mp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd2, "w") as m: json.dump(meta, m, indent=2)
        _log("VORSCHLAG #" + str(err_id) + " -> " + base + " (nicht angewandt)")
        try:
            import jack_guard
            jack_guard.notify("AutoFixer Vorschlag wartet: " + os.path.basename(real))
        except Exception: pass
    except Exception as e:
        _log("Vorschlag fehlgeschlagen: " + str(e)[:120], "WARN")
    return

def _apply_ORIGINAL_DEAKTIVIERT(file_path,shadow_path,err_id,summary):
    ts=int(time.time())
    bak=os.path.join(BACKUP,os.path.basename(file_path)+f".bak_{ts}")
    shutil.copy2(file_path,bak)
    shutil.copy2(shadow_path,file_path)
    try:
        c=sqlite3.connect(DB)
        c.execute("UPDATE errors SET resolved=1,fix_applied=1,fix_ts=? WHERE id=?",
            (datetime.now().isoformat(),err_id))
        c.commit(); c.close()
    except Exception as e: _log(f"Mark-resolved Fehler: {e}","WARN")
    _log(f"FIXED #{err_id}: {summary}")
    try:
        import jack_guard; jack_guard.notify(f"AutoFixer: {summary[:100]}")
    except Exception: pass

def _check_resources():
    try:
        import jack_guard; ram=jack_guard.mem_available_mb()
        if ram>0 and ram<800: return False,f"RAM zu niedrig: {ram}MB"
    except Exception: pass
    return True,"OK"

def run(limit=5):
    try:
        import jack_circuit_breaker as cb
        if not cb.check_allowed():
            print("Shadow-Fixer durch Circuit-Breaker gestoppt")
            return []
    except Exception as e:
        print(f"CB-Fehler: {e}")
    try:
        import jack_heat_protection
        if not jack_heat_protection.check_heat("shadow"):
            print("Shadow-Fixer übersprungen (Hitze)")
            return []
    except: pass

    # HEAT-PROTECT (Qwen 21.08.): Shadow-Fixer nur bei < 55°C
    try:
        import jack_heat_protection
        if not jack_heat_protection.check_heat("shadow"):
            print("Shadow-Fixer run() übersprungen (Hitze)")
            return []
    except Exception as e:
        print(f"Heat-Check-Fehler: {e}")

    ok,reason=_check_resources()
    if not ok: _log(f"Ressourcen kritisch - abgebrochen: {reason}","WARN"); return
    errors=_get_open_errors(limit)
    if not errors: _log("Keine offenen Fehler"); return
    _log(f"{len(errors)} Fehler gefunden")
    fixed=0; skipped=0; escalated=0
    for row in errors:
        err_id,module,err_type,err_msg,file_path,line_num,context=row
        if not file_path or not os.path.exists(file_path):
            _log(f"#{err_id}: Datei nicht gefunden {file_path}","WARN"); skipped+=1; continue
        original=open(file_path,encoding="utf-8",errors="replace").read()
        success=False
        for attempt in range(MAX_RETRIES):
            _log(f"#{err_id} {module} Versuch {attempt+1}/{MAX_RETRIES}")
            patch=_ollama_fix(module,err_type,err_msg,file_path,line_num,context,original)
            if not patch or "CANNOT_FIX" in patch:
                _log(f"#{err_id}: Ollama kann nicht fixen","WARN"); break
            ok2,msg2,shadow=_shadow_test(file_path,patch)
            if ok2:
                _apply(file_path,shadow,err_id,f"{module} {err_type} @ {line_num}")
                fixed+=1; success=True; break
            _log(f"#{err_id} Versuch {attempt+1} fehlgeschlagen: {msg2}","WARN")
        if not success and not (not patch or "CANNOT_FIX" in (patch or "")):
            escalated+=1
            try:
                import jack_guard; jack_guard.notify(
                    f"AutoFixer: #{err_id} {module} nach {MAX_RETRIES}x nicht fixbar - bitte pruefen")
            except Exception: pass
            skipped+=1
    _log(f"Fertig: {fixed} fixed, {skipped} skipped, {escalated} eskaliert")
    return {"fixed":fixed,"skipped":skipped,"escalated":escalated}

if __name__=="__main__":
    import json as _j; print(_j.dumps(run(),indent=2,ensure_ascii=False))
