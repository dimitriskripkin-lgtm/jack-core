"""P3 Tool-Calling: System-Tools fuer LLM (Qwen 21.08.)
Wie jack_math.py, aber fuer System-Befehle. LLM kann Funktionen aufrufen."""
import os, subprocess, datetime

def get_battery_status():
    """Akku-Status vom Honor + Xiaomi."""
    try:
        with open('/sys/class/power_supply/battery/capacity') as f:
            honor_pct = f.read().strip()
        with open('/sys/class/power_supply/battery/status') as f:
            honor_status = f.read().strip()
        
        xiaomi_out = subprocess.run(['ssh', 'xiaomi-jack', 'su -c "dumpsys battery"'], 
                                    capture_output=True, text=True, timeout=10).stdout
        xiaomi_pct = "?"
        for line in xiaomi_out.split('\n'):
            if 'level:' in line:
                xiaomi_pct = line.split(':')[1].strip()
                break
        
        return f"Honor: {honor_pct}% ({honor_status}) | Xiaomi: {xiaomi_pct}%"
    except Exception as e:
        return f"Fehler: {e}"

def get_system_load():
    """CPU/RAM Load."""
    try:
        ram = next((int(l.split()[1])//1024 for l in open('/proc/meminfo') if 'MemAvailable' in l), 0)
        load = open('/proc/loadavg').read().split()[0]
        return f"RAM: {ram}MB frei | Load: {load}"
    except Exception as e:
        return f"Fehler: {e}"

def get_xiaomi_uptime():
    """Xiaomi Uptime."""
    try:
        out = subprocess.run(['ssh', 'xiaomi-jack', 'uptime'], 
                            capture_output=True, text=True, timeout=10).stdout
        return out.strip()
    except Exception as e:
        return f"Fehler: {e}"

def check_wifi_connection():
    """WiFi Status pruefen."""
    try:
        out = subprocess.run(['ip', 'addr', 'show', 'wlan0'], 
                            capture_output=True, text=True, timeout=5).stdout
        if 'inet ' in out:
            ip = [l.split()[1] for l in out.split('\n') if 'inet ' in l][0]
            return f"WiFi: {ip}"
        else:
            return "WiFi: Nicht verbunden"
    except Exception as e:
        return f"Fehler: {e}"

# Registry fuer LLM
TOOLS = {
    'get_battery_status': {'func': get_battery_status, 'desc': 'Akku-Status von Honor + Xiaomi'},
    'get_system_load': {'func': get_system_load, 'desc': 'CPU/RAM Load'},
    'get_xiaomi_uptime': {'func': get_xiaomi_uptime, 'desc': 'Xiaomi Uptime'},
    'check_wifi_connection': {'func': check_wifi_connection, 'desc': 'WiFi Status'},
}

def call_tool(name):
    """Tool aufrufen."""
    if name in TOOLS:
        return TOOLS[name]['func']()
    return f"Tool '{name}' nicht gefunden"
