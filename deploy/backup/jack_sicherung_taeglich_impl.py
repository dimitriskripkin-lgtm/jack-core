#!/usr/bin/env python3
"""Z3b Honor; Offline-Entwurf, Cron 03:43, SQLite pro DB konsistent."""
from pathlib import Path
import contextlib, fcntl, hashlib, json, os, secrets, shlex, shutil, subprocess, sys
from datetime import datetime
HOME=Path.home(); J=HOME/'jack'; BACK=HOME/'jack_backups'
PLAN=BACK/'plan_honor.json'
REMOTE='/data/data/com.termux/files/home/jack_backups_honor'
MAX_ACTIVE=7

def safe_dir(p):
    if p.is_symlink() or not p.is_dir():
        raise RuntimeError('Kein regulaerer Ordner')

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):
            h.update(chunk)
    return h.hexdigest()

@contextlib.contextmanager
def exclusive():
    BACK.mkdir(mode=0o700,parents=True,exist_ok=True)
    safe_dir(BACK)
    fd=os.open(BACK/'.daily.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield
    finally:
        os.close(fd)

def remote_script():
    return r'''import pathlib,sys,json,hashlib,sqlite3
p=pathlib.Path(sys.argv[1]); m=p/'manifest.json'; c=p/'COMPLETE'
def h(f):
 z=hashlib.sha256()
 with open(f,'rb') as inp:
  for chunk in iter(lambda:inp.read(1048576),b''):z.update(chunk)
 return z.hexdigest()
assert p.is_dir() and not p.is_symlink() and m.is_file() and c.is_file()
assert h(m)==c.read_text()
d=json.loads(m.read_text()); assert d['version']==1
for rel,info in d['files'].items():
 part=pathlib.PurePosixPath(rel); assert not part.is_absolute() and '..' not in part.parts
 f=p/part; assert f.is_file() and not f.is_symlink() and h(f)==info['sha256']
 if info.get('sqlite'):
  with sqlite3.connect(f.as_uri()+'?mode=ro',uri=True) as db:
   assert db.execute('PRAGMA integrity_check').fetchall()==[('ok',)]
print('REMOTE_OK',len(d['files']))'''

def remote_retention_script():
    return r'''import pathlib,sys
root=pathlib.Path(sys.argv[1])
attic=root/'Attic'
attic.mkdir(mode=0o700,exist_ok=True)
assert root.is_dir() and not root.is_symlink() and not attic.is_symlink()
a=sorted(root.glob('honor_*'),reverse=True)
for p in a[int(sys.argv[2]):]:
 if not p.is_dir() or p.is_symlink() or not (p/'COMPLETE').is_file():continue
 dest=attic/p.name
 if dest.exists():raise RuntimeError('Attic collision')
 p.rename(dest)
print('REMOTE_ACTIVE')'''

def ssh_cmd(ip, code, *args):
    import jack_xiaomi as xi
    remote='python3 -c '+shlex.quote(code)+' '+' '.join(shlex.quote(str(x)) for x in args)
    a=['ssh']+list(xi.SSH_OPTS)+['-p',str(xi.XIAOMI_SSH_PORT),'root@'+ip,remote]
    return subprocess.run(a,check=True,capture_output=True,text=True,timeout=180)

def transfer(gen):
    import jack_xiaomi as xi
    ip=xi._quick_ip() or xi._get_xiaomi_ip()
    if not ip:raise RuntimeError('Keine Xiaomi-IP')
    mkdir='mkdir -p -- '+shlex.quote(REMOTE)
    subprocess.run(['ssh']+list(xi.SSH_OPTS)+['-p',str(xi.XIAOMI_SSH_PORT),'root@'+ip,mkdir],
                   check=True,capture_output=True,text=True,timeout=35)
    # Classic SCP: Xiaomi sshd hat KEIN konfiguriertes SFTP-Subsystem.
    subprocess.run(['scp','-O','-r']+list(xi.SSH_OPTS)+['-P',str(xi.XIAOMI_SSH_PORT),str(gen),
                   'root@'+ip+':'+REMOTE+'/'],check=True,capture_output=True,text=True,timeout=600)
    res=ssh_cmd(ip,remote_script(),REMOTE+'/'+gen.name)
    if not res.stdout.startswith('REMOTE_OK '):
        raise RuntimeError('Remote-Manifest und SQLite-Probe fehlgeschlagen')

def trigger_n8n():
    import jack_xiaomi as xi
    cfg_path=BACK/'n8n_trigger.json'
    if not cfg_path.is_file() or cfg_path.is_symlink():
        raise RuntimeError('n8n Pfad-Konfiguration fehlt')
    cfg=json.loads(cfg_path.read_text())
    keys=('script','data','config','playlist','root')
    if set(cfg)!=set(keys) or any(not isinstance(cfg[k],str) or not cfg[k].startswith('/') for k in keys):
        raise RuntimeError('n8n Pfade nicht freigegeben')
    # Gemessen 31.10.: N8N_USER_FOLDER=/home/n8n, n8n haengt .n8n an.
    if cfg['data']!='/home/n8n/.n8n' or cfg['config']!='/home/n8n/.config/jack-n8n':
        raise RuntimeError('Falscher Daten-/Key-Pfad')
    cmd='proot-distro login ubuntu --user n8n -- python3 '+' '.join(
        shlex.quote(x) for x in [cfg['script'],'--run',cfg['data'],cfg['config'],cfg['playlist'],cfg['root']])
    r=xi.run_shell(cmd,as_root=False,timeout=600)
    if not r.get('success') or 'N8N_BACKUP_OK ' not in (r.get('stdout') or ''):
        raise RuntimeError('n8n-Sicherung nicht bestaetigt')

def retain_remote():
    import jack_xiaomi as xi
    ip=xi._quick_ip() or xi._get_xiaomi_ip()
    if not ip:raise RuntimeError('Keine Xiaomi-IP fuer Retention')
    ssh_cmd(ip,remote_retention_script(),REMOTE,MAX_ACTIVE)

def retain_local():
    attic=BACK/'Attic'
    attic.mkdir(mode=0o700,exist_ok=True);safe_dir(attic)
    gens=sorted((p for p in BACK.iterdir() if p.is_dir() and not p.is_symlink()
        and p.name.startswith('honor_') and (p/'COMPLETE').is_file()),
        key=lambda p:p.name,reverse=True)
    for old in gens[MAX_ACTIVE:]:
        target=attic/old.name
        if target.exists():raise RuntimeError('Attic Ziel existiert')
        old.rename(target)

def run():
    import importlib.util
    src=J/'deploy'/'backup'/'jack_sicherung.py'
    spec=importlib.util.spec_from_file_location('jack_sicherung_z3b',src)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with exclusive():
        safe_dir(BACK)
        if not PLAN.is_file() or PLAN.is_symlink():
            raise RuntimeError('Backup-Plan fehlt')
        if shutil.disk_usage(BACK).free < 128*1024**2:
            raise RuntimeError('Wenig freier Speicher')
        gen=BACK/('honor_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+secrets.token_hex(3))
        data=json.loads(PLAN.read_text())
        mod.snapshot(data,gen)
        (gen/'ONLINE_PER_DB_ONLY').write_text('Keine atomare Gesamtsicht.\n')
        probe=BACK/('.probe_'+gen.name)
        try:
            mod.probe(gen,probe)
        finally:
            if probe.is_dir() and not probe.is_symlink():
                shutil.rmtree(probe)
        transfer(gen)
        trigger_n8n()
        retain_remote()
        retain_local()
        print('BACKUP_OK',gen.name,'ONLINE_PER_DB_ONLY',flush=True)

if __name__ == '__main__':
    run()
