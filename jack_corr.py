MODULE_VERSION = 1
import uuid
_cur="-"
def new(mid=""):
    global _cur
    _cur=(str(mid)[:40]+"-"+uuid.uuid4().hex[:8]) if mid else uuid.uuid4().hex[:12]
    return _cur
def get():
    return _cur
def tag(s):
    return "[%s] %s"%(_cur,s)
