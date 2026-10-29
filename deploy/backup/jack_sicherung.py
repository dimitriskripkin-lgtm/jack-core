"""ENTWURF. Nur lokal nach Review; keine Dienste/Netz/Produktions-Restores.
backup PLAN.json NEUER_ORDNER --quiesced | probe GENERATION NEUER_TESTORDNER
Plan: {"files":{"memory":"/abs/jack_memory.db",...},"lock":"/abs/logs/.gedaechtnis_git.lock"}
HONOR: labels memory,graph,skills,config,gedaechtnis erforderlich.
XIAOMI-Container: labels n8n_key,n8n_data,playlist; n8n_data/database.sqlite Pflicht.
"""
from pathlib import Path
import contextlib,fcntl,hashlib,json,os,shutil,sqlite3,stat,sys

def regular(p):
    s=p.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid():raise ValueError('Keine eigene regulaere Datei')

def check_path(p):
    if not p.is_absolute():raise ValueError('Absoluter Pfad erforderlich')
    for part in [p,*p.parents]:
        if part.is_symlink():raise ValueError('Symlink-Pfad abgelehnt')

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def integrity(p):
    with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=5) as c:
        if c.execute('PRAGMA integrity_check').fetchall()!=[('ok',)]:raise ValueError('SQLite Integritaet fehlgeschlagen')

def fresh(dest):
    check_path(dest)
    dest.mkdir(mode=0o700)  # niemals existierenden Ordner verwenden

@contextlib.contextmanager
def lock(path):
    if path is None:
        yield;return
    p=Path(path);check_path(p)
    fd=os.open(p,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX);yield
    finally:
        fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

def snapshot(plan,dest):
    files={k:Path(v) for k,v in plan['files'].items()}
    required={'memory','graph','skills','config','gedaechtnis'}
    if any(k.startswith('n8n') for k in files):
        required={'n8n_key','n8n_data','playlist'}
        if not (files.get('n8n_data',Path('/nonexistent'))/'database.sqlite').is_file():raise ValueError('n8n DB fehlt')
    elif not plan.get('lock'):raise ValueError('Gedaechtnis-Lock erforderlich')
    if not required<=files.keys():raise ValueError('Unvollstaendige Sicherungsgruppe')
    for k,p in files.items():
        if not k.replace('_','').isalnum():raise ValueError('Ungueltiges Label')
        check_path(p)
        if not p.exists():raise ValueError('Pflichtquelle fehlt')
        if dest==p or p in dest.parents or dest in p.parents:raise ValueError('Quelle/Ziel ueberlappen')
    fresh(dest);entries={}
    with lock(plan.get('lock')):
        for label,src in files.items():
            items=[src] if src.is_file() else sorted(src.rglob('*'))
            for p in items:
                check_path(p)
                rel=Path(label) if src.is_file() else Path(label)/p.relative_to(src)
                out=dest/rel
                if p.is_dir():out.mkdir(mode=0o700,parents=True,exist_ok=True);continue
                regular(p)
                if p.name.endswith(('-wal','-shm','-journal')):continue
                out.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
                db=p.suffix in {'.db','.sqlite','.sqlite3'}
                if db:
                    with sqlite3.connect(p.as_uri()+'?mode=ro',uri=True,timeout=5) as a, sqlite3.connect(out) as b:a.backup(b,pages=256,sleep=0.05)
                    integrity(out)
                else:shutil.copyfile(p,out)
                os.chmod(out,0o600)
                entries[rel.as_posix()]={'sha256':digest(out),'sqlite':db}
        m=dest/'manifest.json';m.write_text(json.dumps({'version':1,'files':entries},sort_keys=True));os.chmod(m,0o600)
        # COMPLETE bindet das Manifest, keine Signatur/Angreifer-Abwehr.
        c=dest/'COMPLETE';c.write_text(digest(m));os.chmod(c,0o600)
    return len(entries)

def probe(src,dest):
    check_path(src);regular(src/'manifest.json');regular(src/'COMPLETE')
    if digest(src/'manifest.json')!=(src/'COMPLETE').read_text():raise ValueError('Manifest beschaedigt')
    m=json.loads((src/'manifest.json').read_text())
    if m.get('version')!=1:raise ValueError('Version')
    for rel,meta in m['files'].items():
        p=Path(rel)
        if p.is_absolute() or '..' in p.parts or not p.parts:raise ValueError('Unsicherer Restorepfad')
        f=src/p;check_path(f);regular(f)
        if digest(f)!=meta['sha256']:raise ValueError('Sicherung beschaedigt')
    if src==dest or src in dest.parents or dest in src.parents:raise ValueError('Ueberlappung')
    fresh(dest)
    for rel,meta in m['files'].items():
        f=dest/rel;f.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        shutil.copyfile(src/rel,f);os.chmod(f,0o600)
        if digest(f)!=meta['sha256']:raise ValueError('Restore beschaedigt')
        if meta['sqlite']:integrity(f)
    return len(m['files'])

if __name__=='__main__':
    try:
        os.umask(0o077)
        if len(sys.argv)==5 and sys.argv[1]=='backup' and sys.argv[4]=='--quiesced':
            n=snapshot(json.loads(Path(sys.argv[2]).read_text()),Path(sys.argv[3]))
        elif len(sys.argv)==4 and sys.argv[1]=='probe':n=probe(Path(sys.argv[2]),Path(sys.argv[3]))
        else:raise ValueError('Aufruf gemaess Kopf; Schreiber muessen kontrolliert ruhen')
        print('OK: Dateien geprueft:',n,'; keine Dienste gestartet')
    except Exception:
        print('ABBRUCH: keine erfolgreiche Sicherung/Probe bestaetigt; private Teilgeneration lokal pruefen',file=sys.stderr);sys.exit(1)
