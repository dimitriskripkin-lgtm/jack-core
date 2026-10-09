# JACK_TUNE_DIMASIG: Signatur fuer Dima-Freigaben (Telegram -> Runner)
import hmac, hashlib, os
_P = "/data/data/com.termux/files/home/jack/.dima_secret"
def _key():
    if not os.path.isfile(_P):
        try:
            fd = os.open(_P, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd, os.urandom(32).hex().encode()); os.close(fd)
        except FileExistsError:
            pass
    with open(_P, "rb") as f:
        return f.read().strip()
def sign(mid, pid):
    return hmac.new(_key(), (str(mid) + "|" + str(pid)).encode(), hashlib.sha256).hexdigest()
def verify(mid, pid, sig):
    try:
        return bool(sig) and hmac.compare_digest(sign(mid, pid), str(sig))
    except Exception:
        return False
