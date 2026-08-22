"""Heat-Protection + Worker-Target (Qwen 22.08. P4)
3 Stufen: Warnung (55°C), Blockade (65°C), Notfall (75°C).
+ worker_target(): entscheidet automatisch Honor vs Xiaomi."""
import os, subprocess, sys, json

HONOR_TEMP_WARN = 55
HONOR_TEMP_BLOCK = 65
HONOR_TEMP_EMERGENCY = 75

def get_temp(device="honor"):
    """Liest CPU-Temperatur."""
    try:
        if device == "honor":
            return int(open('/sys/class/thermal/thermal_zone0/temp').read().strip()) / 1000
        else:
            r = subprocess.run(["ssh","xiaomi-jack","cat /sys/class/thermal/thermal_zone0/temp"],
                              capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return int(r.stdout.strip()) / 1000
    except:
        return 0
    return 0

def xiaomi_online():
    """Prueft ob Xiaomi via SSH erreichbar ist."""
    try:
        r = subprocess.run(["ssh","-o","ConnectTimeout=5","xiaomi-jack","echo ok"],
                          capture_output=True, text=True, timeout=8)
        return r.returncode == 0 and "ok" in r.stdout
    except:
        return False

def worker_target():
    """ENTSCHEIDET: Wo soll der naechste Job laufen?
    Rueckgabe: 'xiaomi' oder 'honor' (fallback).
    Logik:
      - Honor > 55°C -> Xiaomi (wenn online)
      - Honor <= 55°C -> Honor (lokale Ausfuehrung ist billiger)
      - Xiaomi offline -> Honor (mit Heat-Protection)
    """
    honor_temp = get_temp("honor")
    
    if honor_temp <= HONOR_TEMP_WARN:
        return "honor"  # Honor ist kuehl genug
    
    # Honor ist heiss -> Xiaomi wenn moeglich
    if xiaomi_online():
        xiaomi_temp = get_temp("xiaomi")
        if xiaomi_temp > 0 and xiaomi_temp < HONOR_TEMP_BLOCK:
            print(f"WORKER-TARGET: Xiaomi (Honor {honor_temp:.1f}°C > {HONOR_TEMP_WARN}°C, Xiaomi {xiaomi_temp:.1f}°C)")
            return "xiaomi"
    
    # Fallback: Honor trotz Hitze (mit Heat-Protection)
    print(f"WORKER-TARGET: Honor-FALLBACK (Honor {honor_temp:.1f}°C, Xiaomi offline oder zu heiss)")
    return "honor"

def check_heat(level="normal"):
    """Prueft Temperatur und gibt True zurueck wenn Aktion erlaubt."""
    temp = get_temp("honor")
    
    if level == "shadow":
        if temp > HONOR_TEMP_WARN:
            print(f"HEAT-PROTECT: Shadow-Fixer uebersprungen (CPU {temp:.1f}°C > {HONOR_TEMP_WARN}°C)")
            return False
    elif level == "ollama":
        if temp > HONOR_TEMP_BLOCK:
            print(f"HEAT-PROTECT: Ollama-Call blockiert (CPU {temp:.1f}°C > {HONOR_TEMP_BLOCK}°C)")
            return False
    elif level == "emergency":
        if temp > HONOR_TEMP_EMERGENCY:
            print(f"HEAT-EMERGENCY: CPU {temp:.1f}°C > {HONOR_TEMP_EMERGENCY}°C - Kille ollama + llama-server")
            subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "ollama"], capture_output=True)
            return False
    return True

def emergency_shutdown():
    """Notfall-Shutdown: Killt alle Ollama-Prozesse."""
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "ollama"], capture_output=True)
    print("HEAT-EMERGENCY: Alle Ollama-Prozesse gekillt")

def get_status():
    """Kompakter Status fuer /status oder /selftest."""
    h_temp = get_temp("honor")
    x_online = xiaomi_online()
    x_temp = get_temp("xiaomi") if x_online else 0
    target = worker_target()
    return {
        "honor_temp_c": round(h_temp, 1),
        "xiaomi_online": x_online,
        "xiaomi_temp_c": round(x_temp, 1),
        "next_worker": target,
        "thresholds": {"warn": HONOR_TEMP_WARN, "block": HONOR_TEMP_BLOCK, "emergency": HONOR_TEMP_EMERGENCY}
    }
