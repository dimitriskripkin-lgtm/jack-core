#!/usr/bin/env python3
"""jack_selftest.py — Ein Kommando, kompletter JACK-Systemcheck."""
MODULE_VERSION = 1

import os, sys, time, json
JACK = os.path.expanduser("~/jack")
sys.path.insert(0, JACK)

results = {}

def chk(name, fn, target=None):
    dest = results if target is None else target
    try:
        t0 = time.time()
        ok, info = fn()
        ms = int((time.time()-t0)*1000)
        dest[name] = {"ok": ok, "info": str(info)[:80], "ms": ms}
    except Exception as e:
        dest[name] = {"ok": False, "info": str(e)[:80], "ms": 0}

# Services
def _svcs():
    import subprocess
    # JACK_TUNE_SOLL — Freeze-Soll: nur Dienste die laufen MUESSEN.
    # Bewusst unten: jack_autolearn, jack_publisher, ssh_tunnel_ollama
    # jack_missions = Pflicht im Selftest  # JACK_TUNE_K4NOTE
    SVCS = ["jack_cortex","jack_telegram","jack_waechter","jack_missions"]  # JACK_TUNE_F1SVCS
    dead = []
    for s in SVCS:
        r = subprocess.run(["sv","status",s], capture_output=True, text=True, timeout=5)
        if "run:" not in r.stdout: dead.append(s)
    return len(dead)==0, f"{len(SVCS)-len(dead)}/{len(SVCS)} laufen" + (f" DEAD:{dead}" if dead else "")

# Xiaomi SSH
def _xiaomi():
    import jack_heartbeat
    ok = jack_heartbeat.is_xiaomi_alive()
    return ok, "SSH-Port erreichbar" if ok else "SSH-Port TOT"

# Ollama HTTP
def _ollama():
    """Lock = Soll. Binary nur wenn kein Lock. JACK_TUNE_STOLL"""
    import os
    if os.path.isfile("/data/data/com.termux/files/home/jack/.ollama_lock"):
        return True, "Lock liegt — aus by design"
    try:
        import jack_heartbeat
        if not jack_heartbeat.is_xiaomi_alive():
            return False, "SSH tot — Gate nicht erreichbar"
        import subprocess
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5",
             "xiaomi-jack", "ls /data/data/com.termux/files/usr/bin/ollama"],
            capture_output=True, text=True, timeout=8)
        if r.returncode == 0:
            return True, "Binary OK, Gate bereit (off by design)"
        return False, "Binary nicht gefunden"
    except Exception as e:
        return False, str(e)[:60]

# Graph
def _graph():
    import jack_graph as _g
    r = _g.recall("Dima")
    return bool(r), f"{len((r or '').splitlines())} Einträge"

# Heartbeats
def _beats():
    import jack_heartbeat
    SVCS = ["jack_cortex","jack_telegram","jack_waechter","jack_missions"]  # JACK_TUNE_F1SVCS  # JACK_TUNE_SOLL
    stale = []
    for s in SVCS:
        a = jack_heartbeat.age(s)
        if a is None or a > 600: stale.append(s)
    return len(stale)==0, f"{len(SVCS)-len(stale)}/{len(SVCS)} frisch" + (f" STALE:{stale}" if stale else "")

# Missions
def _missions():
    p = os.path.join(JACK,"missions","pending")
    d = os.path.join(JACK,"missions","done")
    f = os.path.join(JACK,"missions","fail")
    pending = len(os.listdir(p)) if os.path.exists(p) else 0
    done = len(os.listdir(d)) if os.path.exists(d) else 0
    fail = len(os.listdir(f)) if os.path.exists(f) else 0
    # JACK_TUNE_SELFTEST24H (24.10.2026): frueher zaehlte fail<25 alle Fehlschlaege seit Juli (932) -> jeden Morgen 85 %.
    # Jetzt nur die letzten 24 h und nur echte Aktionen. Pruef-Acts (grep_count, sv_ok, hb_ok, file_exists, diag, fact,
    # compile_ok, ro_*) melden ok=false, wenn die gepruefte Bedingung nicht zutrifft. Das ist kein Defekt.
    import re as _re
    _grenze = time.time() - 86400
    _pruef = ("grep_count", "sv_ok", "hb_ok", "file_exists", "diag", "fact", "compile_ok", "ro_")
    echt = 0
    if os.path.exists(f):
        for _n in os.listdir(f):
            try:
                if os.path.getmtime(os.path.join(f, _n)) < _grenze:
                    continue
            except OSError:
                continue
            _m = _re.match(r"m_(.+?)_\d{8}_\d{6}", _n)
            if _m and _m.group(1).startswith(_pruef):
                continue
            echt += 1
    return echt < 25, f"pending={pending} done={done} fail={fail} (24h echt: {echt})"

# Config
def _config():
    cfg = os.path.join(JACK,"config.ini")
    return os.path.exists(cfg), "vorhanden" if os.path.exists(cfg) else "FEHLT"

def _extended():  # JACK_TUNE_SELFTEST_W3: nur expliziter Tageslauf
    import subprocess, stat, shutil
    out = {}
    def add(name, fn):
        chk(name, fn, target=out)
    def command(args, timeout=6):
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    def service(name):
        r = command(['sv', 'status', '/data/data/com.termux/files/usr/var/service/' + name])
        return r.returncode == 0 and r.stdout.startswith('run:'), 'Hauptprozess geprueft'
    def private_config():
        s = os.lstat(os.path.join(JACK, 'config.ini'))
        return stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid() and not s.st_mode & 0o077, 'nur Rechte'
    def queue():
        p = os.path.join(JACK, 'missions', 'pending')
        ages = [time.time()-os.stat(os.path.join(p,n)).st_mtime for n in os.listdir(p) if n.endswith('.json')]
        return not ages or max(ages) <= 900, 'Queue-Alter <=15min'
    def pin():
        r = command(['ssh', '-G', 'xiaomi-jack'])
        d = dict(l.split(None,1) for l in r.stdout.splitlines() if ' ' in l)
        good = r.returncode == 0 and d.get('stricthostkeychecking') in ('yes','true')
        good = good and d.get('hostkeyalias') == 'xiaomi-jack' and d.get('checkhostip') in ('no','false')
        good = good and d.get('userknownhostsfile') == os.path.expanduser('~/.ssh/known_hosts_xiaomi')
        good = good and d.get('hostkeyalgorithms') == 'ssh-ed25519' and '/xi23/' in d.get('controlpath','')
        return bool(good), 'Policy; kein frischer Handshake'
    def n8n():
        import jack_xiaomi
        r = jack_xiaomi.run_shell("python3 -c \"import urllib.request; r=urllib.request.urlopen('http://127.0.0.1:5678/healthz',timeout=4); print(r.status)\"", as_root=False, timeout=8)
        return r.get('success') is True and r.get('stdout','').strip() == '200', 'HTTP healthz; kein Kalender-Test'
    def spotify():
        import jack_spotify_s1_play
        err = jack_spotify_s1_play._vorpruefung()
        return err is None, 'Vorpruefung OK' if err is None else 'Vorpruefung fehlgeschlagen'
    def rish():
        r = command(['rish','-c','id -u'],timeout=6)
        return r.returncode == 0 and r.stdout.strip() == '2000', 'UID-Pruefung'
    def lage():
        p = os.path.expanduser('~/jack-gedaechtnis/lage/aktuell.md')
        age = time.time()-os.stat(p).st_mtime
        return 0 <= age <= 10800, 'Dateialter <=3h'
    def playlist():
        r = command(['crontab','-l'])
        if r.returncode: return None, 'Crontab nicht pruefbar'
        active = any('jack_musik_gut.py' in l and not l.lstrip().startswith('#') for l in r.stdout.splitlines())
        return (True,'Cron vorhanden; kein Fortschrittsbeweis') if active else (None,'Cron fehlt; Abschluss lokal pruefen')
    def logs():
        names = ['jack_cortex','jack_focus_monitor','jack_honor_watch','jack_telegram','jack_mcp','cloudflared']
        checks = [service(n+'/log')[0] for n in names]
        return all(checks), str(sum(checks))+'/6 Logprozesse'
    def skills():
        s = os.lstat(os.path.join(JACK,'jack_skills.db'))
        return stat.S_ISREG(s.st_mode) and s.st_size > 0, 'Datei vorhanden; keine Wirkungspruefung'
    for name in ['jack_mcp','cloudflared','crond']:
        add(name,lambda n=name:service(n))
    add('disk',lambda:(shutil.disk_usage(JACK).free >= 1073741824,'frei >=1GiB'))
    add('config_rights',private_config)
    add('queue_age',queue)
    add('xiaomi_pin_policy',pin)
    add('xiaomi_pin_fresh',lambda:(None,'SKIP: separater frischer Handshake erforderlich'))
    add('n8n_health',n8n)
    add('calendar_dryrun',lambda:(None,'SKIP: kein seiteneffektfreier Dryrun vorhanden'))
    add('spotify_preflight',spotify)
    add('rish',rish)
    add('lage_fresh',lage)
    add('playlist_cron',playlist)
    add('svlogd',logs)
    add('backup_restore',lambda:(None,'SKIP: W2 echte Restore-Abnahme offen'))
    add('google_oauth',lambda:(None,'SKIP: Google-Produktionsstatus separat pruefen'))
    add('skills_file',skills)
    return out


chk("services", _svcs)
chk("xiaomi_ssh", _xiaomi)
chk("ollama", _ollama)
chk("graph", _graph)
chk("heartbeats", _beats)
chk("missions", _missions)
chk("config", _config)

# Auswertung
ok_n = sum(1 for v in results.values() if v["ok"])
total = len(results)
score = int(ok_n/total*100)

print(f"\n{'='*40}")
print(f"JACK SELFTEST — Score: {score}% ({ok_n}/{total})")
print(f"{'='*40}")
for name, r in results.items():
    sym = "✓" if r["ok"] else "✗"
    print(f"  {sym} {name:<16} {r['info']} ({r['ms']}ms)")
print(f"{'='*40}\n")

snap = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "score": score,
    "nodes": results
}
if __name__ == "__main__":
    if '--extended' in sys.argv:  # JACK_TUNE_SELFTEST_W3
        snap['extended'] = _extended()
        vals = list(snap['extended'].values())
        counts = [sum(v['ok'] is state for v in vals) for state in (True, False, None)]
        print('TAGESCHECK: PASS=%d FAIL=%d SKIP=%d' % tuple(counts))
        for name, value in snap['extended'].items():
            print('  %s: %s' % (name, 'SKIP' if value['ok'] is None else ('PASS' if value['ok'] else 'FAIL')))
    json.dump(snap, open(os.path.join(JACK,"jack_diag_snapshot.json"),"w"), indent=2)
    print("Snapshot: ~/jack/jack_diag_snapshot.json")
    sys.exit(0 if score==100 and not any(v['ok'] is False for v in snap.get('extended', {}).values()) else 1)
