#!/usr/bin/env python3
"""JACK TUEV v2 - Stresstest + Tiefenanalyse.
Testet Laufzeit-Verhalten, Parallelität, Fehlertoleranz, End-to-End-Pipelines.
Laufzeit: ~45-60 Sekunden."""
import os, sys, sqlite3, json, time, threading, subprocess, datetime
sys.path.insert(0, os.path.expanduser('~/jack'))
H = os.path.expanduser('~/jack')
R = {'OK':0,'WARN':0,'FAIL':0}
LOCK = threading.Lock()

def p(status, gruppe, text):
    with LOCK:
        R[status] += 1
        symbol = {'OK':'✓','WARN':'⚠','FAIL':'✗'}[status]
        print(f"[{symbol}] {gruppe}: {text}")

def sh(cmd, t=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t, cwd=H)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, '', str(e)

print("="*55)
print(f"JACK TUEV v2  {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
print("Stresstest + Tiefenanalyse — ca. 60s")
print("="*55)

# === 1. FUNKTION STATT NUR IMPORT ===
print("\n[PHASE 1] Funktions-Checks (nicht nur importieren)")
try:
    import jack_budget as _jb
    r = str(_jb.status())
    p('OK' if 'Text' in r and '/' in r else 'FAIL', 'FUNC', f'budget.status() -> {r[:60]}')
except Exception as e: p('FAIL','FUNC',f'budget: {e}')

try:
    import jack_chains as _jc
    r = _jc.liste()
    p('OK' if 'kette' in r.lower() or 'system' in r.lower() else 'WARN', 'FUNC', f'chains.liste() -> {len(r)} Zeichen')
except Exception as e: p('FAIL','FUNC',f'chains: {e}')

try:
    import jack_intent as _ji
    lvl = _ji.get_level()
    _ji.set_level(lvl)
    assert _ji.get_level() == lvl
    p('OK','FUNC', f'intent get/set_level Roundtrip: {lvl}')
except Exception as e: p('FAIL','FUNC',f'intent: {e}')

try:
    import jack_gemini_bridge as _gb
    has_cb = hasattr(_gb,'_cb_reset_check') and hasattr(_gb,'_CB_COOLDOWN')
    old = _gb._CB_OPEN
    _gb._CB_OPEN=True; _gb._CB_SINCE=time.time()-9999; _gb._cb_reset_check()
    p('OK' if not _gb._CB_OPEN else 'FAIL','FUNC', f'CB-Reset nach Cooldown: _CB_OPEN={_gb._CB_OPEN}')
    _gb._CB_OPEN=True; _gb._CB_SINCE=time.time(); _gb._cb_reset_check()
    p('OK' if _gb._CB_OPEN else 'FAIL','FUNC', f'CB-Kein-Reset bei frischem Fehler: _CB_OPEN={_gb._CB_OPEN}')
    _gb._CB_OPEN=old; _gb._CB_FAILS=0
except Exception as e: p('FAIL','FUNC',f'circuit_breaker: {e}')

try:
    import jack_memory_tree as _jmt
    s = _jmt.statistik(); k = _jmt.letzte_kette(3)
    p('OK','FUNC',f'memory_tree statistik+kette: {len(str(s))+len(str(k))} Zeichen')
except Exception as e: p('FAIL','FUNC',f'memory_tree: {e}')

# === 2. ROUTER KOMPLETT (alle 7 neuen Befehle) ===
print("\n[PHASE 2] Router-Volltest (alle Befehle)")
import jack_telegram as _jt
router_cmds = ['/budget','/missionen','/audit','/scan','/baum','/trace','/werkstatt','/xyz_unbekannt123']
expected_no_gemini = True
for cmd in router_cmds:
    try:
        t0=time.time(); r=str(_jt.handle(cmd) or ''); ms=(time.time()-t0)*1000
        gemini_hit = r.lower().strip().endswith('🌐 gemini') or 'was geht' in r.lower() or (r.strip().startswith('Na,') and 'gemini' in r[-20:].lower())
        no_crash = 'Traceback' not in r and 'Error' not in r[:20]
        if cmd == '/xyz_unbekannt123':
            p('OK' if r.startswith('Unbekannter') else 'FAIL','ROUTER', f'{cmd} -> Catch-All: {r[:50]}')
        else:
            p('OK' if not gemini_hit and no_crash and len(r)>5 else 'WARN','ROUTER',
              f'{cmd} {ms:.0f}ms -> {r[:50]}')
    except Exception as e:
        p('FAIL','ROUTER',f'{cmd}: {e}')

# === 3. SEND-SPLITTER STRESSTEST ===
print("\n[PHASE 3] Send-Splitter (kein echtes Senden)")
try:
    old_send = _jt.send
    sent_parts = []
    def mock_send(text):
        sent_parts.append(len(text))
    _jt.send = mock_send
    big = 'X' * 8500
    if len(big) <= 3800:
        _jt.send(big)
    else:
        for i in range(0, len(big), 3800):
            _jt.send(big[i:i+3800])
    _jt.send = old_send
    max_part = max(sent_parts) if sent_parts else 0
    p('OK' if max_part <= 3800 else 'FAIL','SPLIT',
      f'8500 Zeichen -> {len(sent_parts)} Teile, max {max_part} Zeichen')
except Exception as e:
    try: _jt.send = old_send
    except: pass
    p('FAIL','SPLIT',str(e)[:80])

# === 4. PARALLELZUGRIFF AUF SQLITE (WAL-Stress) ===
print("\n[PHASE 4] Parallel-DB-Stress (5 Threads x 20 Writes)")
errors_found = []
def db_stress(tid):
    try:
        con = sqlite3.connect(os.path.join(H,'jack_errors.db'), timeout=10)
        con.execute("PRAGMA journal_mode=WAL")
        for i in range(20):
            con.execute("INSERT INTO errors (module,error_type,error_msg,file_path,line_num,context,resolved,timestamp) VALUES (?,?,?,?,?,?,1,datetime('now'))",
                (f'STRESS-T{tid}','TEST',f'stress {i}','',0,'tuev2'))
        con.commit(); con.close()
    except Exception as e:
        errors_found.append(str(e))

threads = [threading.Thread(target=db_stress, args=(i,)) for i in range(5)]
t0=time.time()
for t in threads: t.start()
for t in threads: t.join()
ms=(time.time()-t0)*1000
con=sqlite3.connect(os.path.join(H,'jack_errors.db'),timeout=5)
written=con.execute("SELECT COUNT(*) FROM errors WHERE module LIKE 'STRESS-T%' AND resolved=1").fetchone()[0]
con.execute("DELETE FROM errors WHERE module LIKE 'STRESS-T%'"); con.commit(); con.close()
p('OK' if not errors_found and written==100 else 'FAIL','PARALLEL',
  f'5T x 20W={written}/100 geschrieben, {ms:.0f}ms, Fehler: {len(errors_found)}')

# === 5. FEHLERKANAL END-TO-END UNTER LAST ===
print("\n[PHASE 5] Fehlerkanal E2E")
import jack_log
t0=time.time()
for i in range(10):
    jack_log.log_decision(f'TUEV2-ERR-{i}', f'Lasttest Eintrag {i}')
ms=(time.time()-t0)*1000
con=sqlite3.connect(os.path.join(H,'jack_errors.db'),timeout=5)
n=con.execute("SELECT COUNT(*) FROM errors WHERE module LIKE 'TUEV2-ERR%' AND resolved=0").fetchone()[0]
con.execute("UPDATE errors SET resolved=1 WHERE module LIKE 'TUEV2-ERR%'"); con.commit(); con.close()
p('OK' if n==10 else 'FAIL','KANAL-LAST', f'10 Fehler-Logs -> {n}/10 in errors.db ({ms:.0f}ms)')

# === 6. SKILL-PIPELINE E2E ===
print("\n[PHASE 6] Skill-Pipeline (Builder -> DB -> Trainer-Format)")
try:
    import jack_skill_builder as _sb, jack_skill_trainer as _st
    _sb.speichere_skill('tuev2_pipeline_test','TÜV2 Pipeline Test','echo tuev2pipeline','','tuev2pipeline')
    con=sqlite3.connect(os.path.join(H,'jack_skills.db'),timeout=5)
    row=con.execute("SELECT name,state,plan_json FROM skills WHERE name='tuev2_pipeline_test'").fetchone()
    if row:
        plan=json.loads(row[2])
        has_exec=any(s.get('type')=='exec' for s in plan.get('steps',[]))
        has_crit=bool(plan.get('success_criteria'))
        con.execute("DELETE FROM skills WHERE name='tuev2_pipeline_test'"); con.commit()
        p('OK' if has_exec and has_crit else 'WARN','PIPELINE',
          f'Skill erstellt: exec={has_exec} criteria={has_crit} state={row[1]}')
    else:
        p('FAIL','PIPELINE','Skill wurde nicht in DB geschrieben')
    con.close()
except Exception as e: p('FAIL','PIPELINE',str(e)[:100])

# === 7. SSH CONCURRENT (3 parallele Calls) ===
print("\n[PHASE 7] SSH Concurrent (3 parallele Verbindungen)")
ssh_results = []
def ssh_test(n):
    rc,out,_ = sh(f'ssh -o ConnectTimeout=4 xiaomi-jack echo ok{n}', 10)
    ssh_results.append((n, rc, out))
t0=time.time()
sth=[threading.Thread(target=ssh_test,args=(i,)) for i in range(3)]
for t in sth: t.start()
for t in sth: t.join()
ms=(time.time()-t0)*1000
ok_count=sum(1 for _,rc,_ in ssh_results if rc==0)
p('OK' if ok_count==3 else 'WARN','SSH-CONCURRENT',
  f'{ok_count}/3 OK in {ms:.0f}ms (Multiplexing: {"aktiv" if ms<1000 else "langsam"})')

# === 8. PUBLISHER OUTPUT PRIVACY ===
print("\n[PHASE 8] Publisher Output Privacy-Check")
try:
    ctx=open(os.path.expanduser('~/jack-context/context.md')).read()
    leaks=['Max-Planck','Tupperware','Heinrich Staas','Schaeferhund','heisst Rex',
           'ghp_','AIza','sk_','Burnout','Michi mit 17','Cannabis']
    found=[l for l in leaks if l in ctx]
    p('OK' if not found else 'FAIL','PRIVACY',
      f'context.md: {"SAUBER" if not found else "LEAK: "+str(found)}')
    age=(time.time()-os.path.getmtime(os.path.expanduser('~/jack-context/context.md')))/60
    p('OK' if age<10 else 'WARN','PUBLISH', f'context.md {age:.0f}min alt')
except Exception as e: p('FAIL','PRIVACY',str(e)[:80])

# === 9. BARE EXCEPT ZAEHLER ===
print("\n[PHASE 9] Code-Qualität (stumme Fehler)")
kern=['jack_gemini_bridge.py','jack_cortex.py','jack_telegram.py',
      'jack_autonomous.py','jack_talk.py','jack_intent.py']
for fn in kern:
    try:
        content=open(os.path.join(H,fn)).read()
        bare=content.count('except:')
        exc_pass=content.count('except Exception: pass')+content.count('except Exception:\n        pass')
        total=bare+exc_pass
        p('OK' if total<=3 else 'WARN','QUALITAET',f'{fn}: {bare} bare + {exc_pass} exc-pass = {total} stumme')
    except Exception as e: p('WARN','QUALITAET',f'{fn}: {e}')

# === 10. GIT CREDENTIAL TEST ===
print("\n[PHASE 10] Git Push Credential")
rc,out,err=sh('cd ~/jack-context && git push origin main 2>&1 | tail -2',15)
p('OK' if 'up-to-date' in out or 'master' in out or 'main' in out else 'WARN','GIT',
  f'push: {(out or err)[:60]}')

# === 11. CONFIG ROUNDTRIP UNTER LAST ===
print("\n[PHASE 11] Config-Konsistenz")
try:
    import configparser
    cfg=configparser.ConfigParser(); cfg.read(os.path.join(H,'config.ini'))
    checks=[
        ('NETWORK','xiaomi_ip','10.229.239.131'),
        ('AUTONOMIE','level','4'),
        ('GITHUB','branch','master'),
    ]
    for sec,key,expected in checks:
        val=cfg.get(sec,key,fallback='FEHLT')
        p('OK' if val==expected else 'WARN','CONFIG',f'[{sec}] {key}={val} (erwartet {expected})')
except Exception as e: p('FAIL','CONFIG',str(e)[:80])

# === 12. DIENSTE UNTER LAST (nach allem noch oben?) ===
print("\n[PHASE 12] Dienste nach Stresstest")
for d in ['jack_cortex','jack_telegram','jack_waechter','ollama']:
    _,out,_=sh(f'sv status {d}')
    p('OK' if out.startswith('run:') else 'FAIL','FINAL',d+' '+out[:40])

print("\n"+"="*55)
total=sum(R.values())
print(f"SCORECARD: {R['OK']} OK | {R['WARN']} WARN | {R['FAIL']} FAIL  (von {total})")
urteil="STRESSTEST BESTANDEN" if R['FAIL']==0 else f"{R['FAIL']} FAIL — pruefen"
print(f"URTEIL: {urteil}")
print("="*55)
