#!/data/data/com.termux/files/usr/bin/python3
"""Finde Xiaomi im aktuellen Hotspot-Subnetz, update SSH-Config + config.ini."""
import re, subprocess, time
from pathlib import Path

H = Path("/data/data/com.termux/files/home/jack")
SSH_CONFIG = Path("/data/data/com.termux/files/home/.ssh/config")
CONFIG_INI = H / "config.ini"
KEY = "/data/data/com.termux/files/home/.ssh/id_jack"
PORT = 8022

def sh(cmd, t=8):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return ((p.stdout or "") + (p.stderr or "")).strip()
    except Exception as e:
        return str(e)

def honor_hotspot_ip():
    out = sh("ip -4 addr show 2>/dev/null")
    # Alle 10.x und 192.168.43/50 Hotspot-typische
    found = re.findall(r"inet (10\.\d+\.\d+\.\d+)/(\d+)", out)
    found += re.findall(r"inet (192\.168\.(?:43|50|137)\.\d+)/(\d+)", out)
    for ip, _ in found:
        if not ip.endswith(".1") and not ip.endswith(".97"):  # grob Heim raus
            return ip, "hotspot"
    # Letzte bekannte aus SSH-Config
    try:
        cfg = Path("/data/data/com.termux/files/home/.ssh/config").read_text()
        m = re.search(r"HostName\s+(\d+\.\d+\.\d+\.\d+)", cfg)
        if m:
            return m.group(1), "ssh_config"
    except Exception:
        pass
    return "10.229.239.203", "fallback"

def candidates(gateway_ip):
    if not gateway_ip:
        return []
    base = ".".join(gateway_ip.split(".")[:3])
    # Häufige statische Endungen + kurzer ARP-Blick
    ips = [f"{base}.{i}" for i in (131, 100, 101, 102, 50, 20, 10)]
    arp = sh("cat /proc/net/arp 2>/dev/null")
    for m in re.finditer(rf"({re.escape(base)}\.\d+)\s+", arp):
        ips.append(m.group(1))
    # unique, gateway raus
    seen = set()
    out = []
    for ip in ips:
        if ip != gateway_ip and ip not in seen:
            seen.add(ip); out.append(ip)
    return out

def probe(ip):
    r = subprocess.run(
        ["ssh", "-i", KEY, "-o", "BatchMode=yes", "-o", "ConnectTimeout=3",
         "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
         "-p", str(PORT), ip, "echo", "JACK_OK"],
        capture_output=True, text=True, timeout=6,
    )
    return r.returncode == 0 and "JACK_OK" in ((r.stdout or "") + (r.stderr or ""))

def update_ssh(ip):
    cfg = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    if "Host xiaomi-jack" in cfg:
        cfg = re.sub(r"(Host xiaomi-jack\s*\n(?:.*\n)*?\s*HostName\s+)\S+",
                     r"\g<1>" + ip, cfg, count=1)
    else:
        cfg += f"""
Host xiaomi-jack
    HostName {ip}
    Port {PORT}
    IdentityFile {KEY}
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
    ConnectTimeout 8
    ControlMaster auto
    ControlPath /data/data/com.termux/files/home/.ssh/sockets/%r@%h:%p
    ControlPersist 120s
"""
    SSH_CONFIG.write_text(cfg)
    SSH_CONFIG.chmod(0o600)

def update_ini(ip):
    if not CONFIG_INI.exists():
        return
    t = CONFIG_INI.read_text()
    t = re.sub(r"(xiaomi_ip\s*=\s*)\S+", r"\g<1>" + ip, t)
    t = re.sub(r"(host\s*=\s*)10\.\d+\.\d+\.\d+", r"\g<1>" + ip, t)
    CONFIG_INI.write_text(t)

def current_hostname():
    try:
        cfg = Path("/data/data/com.termux/files/home/.ssh/config").read_text()
        m = re.search(r"Host xiaomi-jack.*?HostName\s+(\d+\.\d+\.\d+\.\d+)", cfg, re.S)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None

def main():
    # 1) Aktuelle Config-IP zuerst
    cur = current_hostname()
    ordered = []
    if cur:
        ordered.append(cur)
    gw, iface = honor_hotspot_ip()
    print("gateway", gw, "iface", iface, "current", cur)
    for ip in candidates(gw if gw and gw != cur else "10.229.239.203"):
        if ip not in ordered:
            ordered.append(ip)
    # bekannte Endung 131 immer
    base = ".".join((gw or "10.229.239.203").split(".")[:3])
    for end in (131, 100, 101, 50):
        ip = f"{base}.{end}"
        if ip not in ordered:
            ordered.append(ip)
    for ip in ordered:
        print("probe", ip, "...")
        if probe(ip):
            print("FOUND", ip)
            update_ssh(ip)
            update_ini(ip)
            print("UPDATED ssh config + config.ini")
            return 0
    print("NOT_FOUND")
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
