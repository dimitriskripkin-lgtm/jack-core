import os, configparser

DEFAULT = {
    'NETWORK': {'ssh_port': '8022', 'rescue_port': '8023', 'keepalive_interval': '20', 'xiaomi_ip': '192.168.178.154', 'xiaomi_port': '43199'},
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
