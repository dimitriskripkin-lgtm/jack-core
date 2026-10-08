import subprocess, os, time

def _ip():
    try:
        import configparser
        c = configparser.ConfigParser()
        c.read(os.path.expanduser("~/jack/config.ini"))
        return c.get("NETWORK", "xiaomi_ip", fallback="")
    except Exception:
        return ""

def check_ui():
    """True=ok, False=ALARM, None=Xiaomi offline (fail-safe!)"""
    try:
        import jack_xiaomi as _jx  # JACK_TUNE_GATEWAY
        _r = _jx.run_shell("dumpsys activity activities | grep mResumedActivity", as_root=False, timeout=8)
        _out = _r.get("stdout") or ""
        if not _r.get("success") or not _out.strip():
            return None
        bad = ["systemui", "emergency", "sos", "SosActivity"]
        return not any(b.lower() in _out.lower() for b in bad)
    except Exception:
        return None

if __name__ == "__main__":
    r = check_ui()
    print({True:"OK - keine Notfall-Activity",False:"ALARM!",None:"OFFLINE"}.get(r,r))
