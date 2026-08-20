import os, configparser
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

DEFAULT = {
    'NETWORK': {'ssh_port': '8022', 'rescue_port': '8023', 'keepalive_interval': '20', 'xiaomi_ip': '10.58.220.131', 'xiaomi_port': '43199'},
    'STORAGE': {'db_path': '/data/data/com.termux/files/home/jack/jack_errors.db'}
}

config = configparser.ConfigParser()
path = os.path.expanduser('~/jack/config.ini')

if os.path.exists(path):
    try: config.read(path)
    except: config.read_dict(DEFAULT)
else: config.read_dict(DEFAULT)

def get_param(sec, key, is_int=False):
    try:
        val = config.get(sec, key)
        return int(val) if is_int else val
    except:
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
