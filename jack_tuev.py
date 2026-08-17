#!/usr/bin/env python3
"""JACK TUEV: Read-only Pruefstand. Verifiziert Dienste, Fixes, Kanaele, DBs, SSH, Repo-Hygiene.
Ausgabe: [OK]/[WARN]/[FAIL] pro Pruefung + Scorecard. Aendert NICHTS (ausser eigenem Testfehler-Roundtrip)."""
import os, sys, subprocess, sqlite3, json, time, datetime
sys.path.insert(0, os.path.expanduser('~/jack'))
H = os.path.expanduser('~/jack')
R = {'OK': 0, 'WARN': 0, 'FAIL': 0}

def p(status, gruppe, text):
    R[status] += 1
    print(f"[{status}] {gruppe}: {text}")

def sh(cmd, t=10):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t, cwd=H)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, '', str(e)

print("=" * 50)
print("JACK TUEV " + datetime.datetime.now().strftime('%d.%m.%Y %H:%M'))
print("=" * 50)

# 1 DIENSTE
for d in ['jack_cortex', 'jack_telegram', 'jack_waechter', 'ollama']:
    rc, out, _ = sh(f'sv status {d}')
    p('OK' if out.startswith('run:') else 'FAIL', 'DIENST', d + ' ' + out[:40])

# 2 IMPORTS (findet was py_compile uebersieht)
for m in ['jack_log', 'jack_gemini_bridge', 'jack_cortex', 'jack_intent', 'jack_chains',
          'jack_telegram', 'jack_talk', 'jack_autonomous', 'jack_skill_trainer',
          'jack_skill_builder', 'jack_autofixer_shadow', 'jack_publish', 'jack_briefing']:
    try:
        __import__(m); p('OK', 'IMPORT', m)
    except Exception as e:
        p('FAIL', 'IMPORT', m + ' -> ' + str(e)[:80])

# 3 FIX-MARKER in Dateien
FIXES = [
    ('jack_gemini_bridge.py', '_CB_COOLDOWN', 'Circuit-Breaker Cooldown'),
    ('jack_gemini_bridge.py', '_cb_reset_check', 'CB Reset-Funktion'),
    ('jack_gemini_bridge.py', 'WAHRHEITSREGEL', 'Anti-Halluzination'),
    ('jack_gemini_bridge.py', 'KONSISTENZ:', 'Prompt-Konsistenz'),
    ('jack_gemini_bridge.py', 'MARKER-VERBOT', 'Marker-Verbot'),
    ('jack_gemini_bridge.py', '"temperature": 0.7', 'Temperature 0.7'),
    ('jack_gemini_bridge.py', '_load_persona', 'Persona-Auslagerung'),
    ('jack_telegram.py', "_rt == '/budget'", 'Befehls-Router'),
    ('jack_telegram.py', 'Unbekannter Befehl:', 'Gemini-Catch-All'),
    ('jack_telegram.py', 'callback_data.startswith("cmd:")', 'Button-Callback'),
    ('jack_telegram.py', "text.strip() == '/kette'", '/kette Handler'),
    ('jack_telegram.py', "text.strip() == '/bugfix'", '/bugfix Handler'),
    ('jack_log.py', '_log_decision_orig', 'Fehler-Spiegel-Mantel'),
    ('jack_autofixer_shadow.py', "file_path != ''", 'Fixer-Filter'),
    ('jack_cortex.py', 'ip","neigh', 'ARP-Discovery'),
    ('jack_cortex.py', 'jack_errors.db', 'Cortex errors.db'),
    ('jack_skill_builder.py', 'Ueberschrieben: schreibt ins echte Schema', 'Builder-Mantel'),
    ('jack_intent.py', "cfg.getint(\"AUTONOMIE\"", 'Level aus config.ini'),
]
for fn, marker, name in FIXES:
    try:
        ok = marker in open(os.path.join(H, fn)).read()
        p('OK' if ok else 'FAIL', 'FIX', name + (' in ' + fn if not ok else ''))
    except Exception as e:
        p('FAIL', 'FIX', fn + ' unlesbar: ' + str(e)[:50])

# 4 ANTI-MUSTER (darf NICHT mehr da sein)
ANTI = [('jack_cortex.py', '"ping"', 'ping im Cortex'),
        ('jack_cortex.py', '10.234.166', 'altes Subnetz 10.234'),
        ('jack_cortex.py', '10.244.147', 'altes Subnetz 10.244'),
        ('jack_gemini_bridge.py', 'VARIANZ:', 'alter Varianz-Prompt'),
        ('jack_gemini_bridge.py', 'Burnout', 'Privates in Bridge'),
        ('jack_talk.py', 'Burnout', 'Privates in Talk')]
for fn, marker, name in ANTI:
    try:
        bad = marker in open(os.path.join(H, fn)).read()
        p('FAIL' if bad else 'OK', 'ANTI', name + (' NOCH DRIN' if bad else ' entfernt'))
    except Exception:
        p('WARN', 'ANTI', fn + ' unlesbar')

# 5 ROUTER LIVE (kein Gemini fuer Slash-Befehle)
try:
    import jack_telegram as jt
    r1 = str(jt.handle('/budget') or '')
    p('OK' if r1 and 'Gemini' not in r1 else 'FAIL', 'ROUTER', '/budget -> ' + r1[:60])
    r2 = str(jt.handle('/xyz_gibtsnicht') or '')
    p('OK' if r2.startswith('Unbekannter Befehl') else 'FAIL', 'ROUTER', 'Catch-All -> ' + r2[:60])
    r3 = str(jt.handle('/audit') or '')
    p('OK' if r3 and 'Fehler:' not in r3[:20] and 'Gemini' not in r3 else 'WARN', 'ROUTER', '/audit -> ' + r3[:60])
except Exception as e:
    p('FAIL', 'ROUTER', str(e)[:100])

# 6 FEHLERKANAL ROUNDTRIP
try:
    import jack_log
    jack_log.log_decision('TUEV-ERR', 'Kanaltest')
    con = sqlite3.connect(os.path.join(H, 'jack_errors.db'), timeout=5)
    row = con.execute("SELECT id FROM errors WHERE error_msg='Kanaltest' AND resolved=0 ORDER BY id DESC LIMIT 1").fetchone()
    if row:
        con.execute("UPDATE errors SET resolved=1 WHERE id=?", (row[0],)); con.commit()
        p('OK', 'KANAL', 'log_decision -> errors.db -> resolved (Roundtrip)')
    else:
        p('FAIL', 'KANAL', 'Spiegel schreibt nicht in errors.db')
    n_open = con.execute("SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
    con.close()
    p('OK' if n_open == 0 else 'WARN', 'KANAL', f'{n_open} offene Fehler in errors.db')
    if n_open:
        con = sqlite3.connect(os.path.join(H, 'jack_errors.db'), timeout=5)
        for r in con.execute("SELECT module, error_msg, timestamp FROM errors WHERE resolved=0 ORDER BY id DESC LIMIT 3"):
            print('       offen: ' + str(r)[:120])
        con.close()
except Exception as e:
    p('FAIL', 'KANAL', str(e)[:100])

# 7 DATENBANKEN (lesbar + WAL)
for f in sorted(x for x in os.listdir(H) if x.endswith('.db')):
    try:
        con = sqlite3.connect(os.path.join(H, f), timeout=5)
        mode = con.execute('PRAGMA journal_mode').fetchone()[0]
        con.execute('SELECT 1').fetchone(); con.close()
        p('OK' if mode == 'wal' else 'WARN', 'DB', f + ' mode=' + mode)
    except Exception as e:
        p('FAIL', 'DB', f + ' ' + str(e)[:60])

# 8 SSH XIAOMI
rc, _, _ = sh('ssh -o ConnectTimeout=4 xiaomi-jack true', 12)
p('OK' if rc == 0 else 'FAIL', 'SSH', 'xiaomi-jack erreichbar rc=' + str(rc))
t0 = time.time(); sh('ssh -o ConnectTimeout=4 xiaomi-jack true', 12); ms = (time.time() - t0) * 1000
p('OK' if ms < 200 else 'WARN', 'SSH', f'Latenz {ms:.0f}ms (Multiplexing {"aktiv" if ms < 200 else "PRUEFEN"})')

# 9 REPO-HYGIENE
rc, out, _ = sh("git ls-files | grep -v jack_publish.py | grep -v jack_tuev.py | xargs grep -l 'Burnout\\|Michi\\|Kiyosaki\\|Dalhoff\\|ghp_[A-Za-z0-9]' 2>/dev/null", 20)
p('OK' if not out else 'FAIL', 'REPO', 'private Begriffe: ' + (out.replace(chr(10), ', ')[:80] if out else 'keine'))
rc, out, _ = sh('git ls-files | grep -E "\\.db($|-)|jack_persona\\.|jack_identity|dima_profil|repo_export|personality\\.json|handshake_v[0-9]|^CLAUDE\\.md$"')
p('OK' if not out else 'FAIL', 'REPO', 'sensible Dateien getrackt: ' + (out.replace(chr(10), ', ')[:80] if out else 'keine'))
rc, out, _ = sh('git status --porcelain | head -5')
p('OK' if not out else 'WARN', 'REPO', 'uncommitted: ' + (out.replace(chr(10), ' | ')[:80] if out else 'sauber'))

# 10 CONFIG-KONSISTENZ
try:
    import jack_intent
    lvl = jack_intent.get_level()
    p('OK' if lvl == 4 else 'WARN', 'CONFIG', f'Autonomie-Level {lvl} (aus config.ini)')
except Exception as e:
    p('FAIL', 'CONFIG', str(e)[:80])

# 11 CRONTAB
rc, out, _ = sh('crontab -l')
p('OK' if 'skill_trainer' in out else 'FAIL', 'CRON', 'Trainer-Job ' + ('drin' if 'skill_trainer' in out else 'FEHLT'))
np = out.count('jack_publish')
p('OK' if np == 0 else 'WARN', 'CRON', f'publish-Cron {np}x (0 korrekt, Thread macht es)')

# 12 PUBLISHER-FRISCHE + SKILLS
try:
    ctx = os.path.expanduser('~/jack-context/context.md')
    age = (time.time() - os.path.getmtime(ctx)) / 60
    p('OK' if age < 10 else 'WARN', 'PUBLISH', f'context.md {age:.0f}min alt')
except Exception as e:
    p('WARN', 'PUBLISH', str(e)[:60])
try:
    con = sqlite3.connect(os.path.join(H, 'jack_skills.db'), timeout=5)
    rows = dict(con.execute('SELECT state, COUNT(*) FROM skills GROUP BY state').fetchall())
    ok_test = con.execute("SELECT state FROM skills WHERE name='router_test_skill'").fetchone()
    con.close()
    p('OK', 'SKILLS', str(rows))
    p('OK' if ok_test else 'WARN', 'SKILLS', 'Builder-Testskill: ' + str(ok_test))
except Exception as e:
    p('FAIL', 'SKILLS', str(e)[:80])

print("=" * 50)
total = sum(R.values())
print(f"SCORECARD: {R['OK']} OK | {R['WARN']} WARN | {R['FAIL']} FAIL  (von {total})")
print("URTEIL: " + ("SYSTEM ORDENTLICH - abgenommen" if R['FAIL'] == 0 else str(R['FAIL']) + " FAIL - NICHT abgenommen, oben pruefen"))
print("=" * 50)
