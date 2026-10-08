import os, configparser
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

DEFAULT = {
    'NETWORK': {'ssh_port': '8022', 'rescue_port': '8023', 'keepalive_interval': '20', 'xiaomi_ip': '10.176.117.131', 'xiaomi_port': '43199'},
    'STORAGE': {'db_path': '/data/data/com.termux/files/home/jack/jack_errors.db'}
}

config = configparser.ConfigParser()
path = os.path.expanduser('~/jack/config.ini')

if os.path.exists(path):
    try: config.read(path)
    except Exception: config.read_dict(DEFAULT)
else: config.read_dict(DEFAULT)

def get_param(sec, key, is_int=False):
    if key == "xiaomi_ip" and not is_int:  # JACK_TUNE_XIDYN: zuletzt gefundene IP geht vor (DHCP-Wechsel)
        try:
            _c = open(os.path.expanduser('~/jack/.last_xiaomi_ip')).read().strip()
            if _c.count(".") == 3:
                return _c
        except Exception:
            pass
    try:
        val = config.get(sec, key)
        return int(val) if is_int else val
    except Exception:
        return int(DEFAULT[sec][key]) if is_int else DEFAULT[sec][key]

def get_val(section, key, fallback=None):
    """Alias fuer get_param - Kompatibilitaet."""
    try:
        return get_param(section, key)
    except Exception:
        return fallback

def feature_enabled(name, default=True):
    try:
        val = config.get('FEATURES', name).strip().lower()
        return val in ('true','1','yes','on')
    except Exception:
        return default
