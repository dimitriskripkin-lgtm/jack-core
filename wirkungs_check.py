import subprocess, os, time

def _ip():
    try:
        import configparser
        c = configparser.ConfigParser()
        c.read(os.path.expanduser("~/jack/config.ini"))
        return c.get("NETWORK", "xiaomi_ip", fallback="10.229.239.131")
    except Exception:
        return "10.229.239.131"

def check_ui():
    """True=ok, False=ALARM, None=Xiaomi offline (fail-safe!)"""
    try:
        key = os.path.expanduser("~/.ssh/id_jack")
        r = subprocess.run(
            ["ssh", "-i", key, "-p", "8022",
             "-o", "ConnectTimeout=4", "-o", "BatchMode=yes",
             "-o", "StrictHostKeyChecking=no",
             "root@" + _ip(),
             "dumpsys activity activities | grep mResumedActivity"],
            capture_output=True, text=True, timeout=8)
        if r.returncode != 0 or not r.stdout.strip():
            return None
        bad = ["systemui", "emergency", "sos", "SosActivity"]
        return not any(b.lower() in r.stdout.lower() for b in bad)
    except Exception:
        return None

if __name__ == "__main__":
    r = check_ui()
    print({True:"OK - keine Notfall-Activity",False:"ALARM!",None:"OFFLINE"}.get(r,r))
