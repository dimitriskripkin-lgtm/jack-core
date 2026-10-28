#!/usr/bin/env python3
"""Skill-Trainer: fuehrt taeglich bis zu 3 sichere CANDIDATE/TESTING-Skills aus.
Sicher = Plan enthaelt NUR exec/wait Steps, jedes Kommando passiert die Blockliste.
Progression: 1 Erfolg -> TESTING, 3 Erfolge -> VERIFIED. UI-Skills bleiben unberuehrt."""
import os, json, sqlite3, subprocess, datetime, time, sys
sys.path.insert(0, os.path.expanduser('~/jack'))
DB = os.path.expanduser('~/jack/jack_skills.db')
SAFE_STEPS = {'exec', 'wait'}
BLOCK = ['rm -rf', 'rm -r /', 'mkfs', 'dd if=', '> /dev', 'reboot', 'shutdown',
         '.ssh', 'id_jack', 'api_key', 'secrets', 'config.ini', 'crontab',
         'sv down', 'kill -9', 'ghp_', 'AIza', 'git push', 'curl', 'wget']

def _cmd_ok(c):
    cl = c.lower()
    return not any(b in cl for b in BLOCK)

def _run_plan(plan):
    """JACK_TUNE_SKILLFAILCLOSED: kein shell=True aus Datenbankplaenen."""
    steps = plan.get('steps', []) if isinstance(plan, dict) else []
    if not isinstance(steps, list) or not steps:
        return False, 'SKILL_NO_EFFECT_PROOF:empty'
    for st in steps:
        if not isinstance(st, dict):
            return False, 'SKILL_NO_EFFECT_PROOF:invalid-step'
        if 'cmd' in st:
            return False, 'SKILL_CMD_BLOCK:manual-approval-required'
        if st.get('type') != 'wait':
            return False, 'SKILL_NO_EFFECT_PROOF:unsupported-step'
    return False, 'SKILL_NO_EFFECT_PROOF:wait-only'

def _check(plan, evidence):
    """Unbekannte oder fehlende Kriterien sind kein Erfolg."""
    if not isinstance(plan, dict) or not isinstance(evidence, str) or not evidence.strip():
        return False
    crits = plan.get('success_criteria')
    if not isinstance(crits, list) or not crits:
        return False
    for c in crits:
        if not isinstance(c, dict):
            return False
        kind = c.get('type')
        if kind == 'contains':
            value = str(c.get('value', ''))
            if not value or value not in evidence:
                return False
        elif kind == 'not_empty':
            if not evidence.strip():
                return False
        else:
            return False
    return True

def run(max_skills=3):
    h = datetime.datetime.now().hour
    if not (8 <= h < 15):
        print('Ausserhalb Power-Time, kein Training'); return []
    con = sqlite3.connect(DB, timeout=5)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT * FROM skills WHERE state IN ('CANDIDATE','TESTING') ORDER BY executions ASC, id ASC LIMIT 40").fetchall()
    done = []
    for r in rows:
        if len(done) >= max_skills: break
        try:
            plan = json.loads(r['plan_json'])
        except Exception:
            continue
        types = {s.get('type') for s in plan.get('steps', [])}
        if not types or not types.issubset(SAFE_STEPS):
            continue
        ok, ev = False, ''
        try:
            ok, ev = _run_plan(plan)
            if ok: ok = _check(plan, ev)
        except Exception as e:
            ev = str(e)[:150]
        succ = r['successes'] + (1 if ok else 0)
        state = r['state']
        if ok and succ >= 3: state = 'VERIFIED'
        elif ok and succ >= 1: state = 'TESTING'
        con.execute('UPDATE skills SET executions=executions+1, successes=?, state=?, last_ts=? WHERE id=?',
                    (succ, state, int(time.time()), r['id']))
        con.commit()
        done.append((r['name'], 'OK' if ok else 'FAIL', state, ev[:80]))
        try:
            import jack_log
            jack_log.log_decision('SKILL-TRAINER', r['name'] + ' -> ' + ('OK ' if ok else 'FAIL ') + state)
        except Exception: pass
    con.close()
    return done

if __name__ == '__main__':
    res = run()
    if not res: print('Keine sicheren Skills faellig')
    for n, o, s, e in res:
        print(n, '|', o, '|', s, '|', e)
