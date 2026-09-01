#!/data/data/com.termux/files/usr/bin/python3
"""APK Lab: inventar / pull+backup. Kein Patch ohne spaeteren Gate."""
import os, sys, json, time, subprocess, hashlib, shutil
J="/data/data/com.termux/files/home/jack"
LAB=os.path.join(J,"apk_lab")

def sh(cmd, t=60):
    r=subprocess.run(cmd, capture_output=True, text=True, timeout=t)
    return r.returncode, (r.stdout or "")+(r.stderr or "")

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def pull_backup(pkg):
    """APK vom Xiaomi holen, backup+checksum."""
    rc, out = sh(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack",
                  "su -c 'pm path %s'" % pkg], 30)
    paths=[l.split(":",1)[1].strip() for l in out.splitlines() if l.startswith("package:")]
    if not paths:
        return False, "kein pm path: "+out[:200]
    remote=paths[0]
    ts=time.strftime("%Y%m%d_%H%M%S")
    dest=os.path.join(LAB, pkg.replace(".","_"), ts)
    os.makedirs(dest, exist_ok=True)
    local=os.path.join(dest, "base.apk")
    rc2, out2 = sh(["scp","-o","BatchMode=yes","-o","ConnectTimeout=10",
                    "xiaomi-jack:%s" % remote, local], 120)
    if rc2!=0 or not os.path.isfile(local):
        # scp as root path may fail; try cat via ssh
        rc3, _ = sh(["ssh","-o","BatchMode=yes","xiaomi-jack",
                     "su -c 'cat %s'" % remote], 120)
        # binary via ssh cat is messy; report
        return False, "pull fail scp rc=%s %s" % (rc2, out2[:200])
    digest=sha256(local)
    meta={"pkg":pkg,"remote":remote,"ts":ts,"sha256":digest,"size":os.path.getsize(local)}
    open(os.path.join(dest,"meta.json"),"w",encoding="utf-8").write(json.dumps(meta,indent=2))
    # last_good pointer
    lg=os.path.join(LAB, pkg.replace(".","_"), "last_good")
    os.makedirs(lg, exist_ok=True)
    shutil.copy2(local, os.path.join(lg,"base.apk"))
    open(os.path.join(lg,"meta.json"),"w",encoding="utf-8").write(json.dumps(meta,indent=2))
    return True, meta

if __name__=="__main__":
    if len(sys.argv)<3 or sys.argv[1]!="pull":
        print("usage: jack_apk_lab.py pull <package>")
        sys.exit(2)
    ok, info = pull_backup(sys.argv[2])
    print("ok", ok)
    print(info)
    sys.exit(0 if ok else 1)
