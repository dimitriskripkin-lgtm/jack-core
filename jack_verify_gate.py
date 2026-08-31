#!/data/data/com.termux/files/usr/bin/python3
"""Shadow/Verify-Gate: wiederholen bis n OK, sonst kein Erfolg."""
import time, subprocess

def repeat_ok(fn, n=3, delay=0.8):
    """fn() -> (ok:bool, msg:str). Braucht n Erfolge in Folge."""
    last=""
    for i in range(n):
        ok, msg = fn()
        last = msg
        if not ok:
            return False, "fail@%d/%d %s" % (i+1, n, msg)
        if i < n-1:
            time.sleep(delay)
    return True, "okx%d %s" % (n, last)

def _ssh(cmd, t=20):
    r=subprocess.run(
        ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack", cmd],
        capture_output=True, text=True, timeout=t)
    return r.returncode, (r.stdout or "")+(r.stderr or "")

def app_open_verified(pkg, times=3):
    """Unlock -> monkey -> times x foreground==pkg."""
    try:
        import jack_xiaomi_unlock as xu
        xu.ensure_unlocked()
    except Exception as e:
        return False, "unlock_err %s" % e
    cmd = "su -c 'monkey -p %s -c android.intent.category.LAUNCHER 1'" % pkg
    rc, out = _ssh(cmd)
    if rc != 0:
        return False, "monkey rc=%s %s" % (rc, out[:120])
    time.sleep(1.2)
    def check():
        try:
            import jack_ui_session as ui
            fg = ui.get_foreground()
            got = (fg.get("pkg") or "")
            ok = got == pkg or got.startswith(pkg)
            return ok, "fg=%s want=%s" % (got, pkg)
        except Exception as e:
            return False, str(e)
    return repeat_ok(check, n=times, delay=0.7)
