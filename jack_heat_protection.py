"""Heat-Protection: Verhindert Handy-Überhitzung (Qwen 21.08.)
3 Stufen: Warnung (55°C), Blockade (65°C), Notfall (75°C)."""
import os, subprocess, sys

def get_temp():
    """Liest CPU-Temperatur."""
    try:
        return int(open('/sys/class/thermal/thermal_zone0/temp').read().strip()) / 1000
    except:
        return 0

def check_heat(level="normal"):
    """Prüft Temperatur und gibt True zurück wenn Aktion erlaubt."""
    temp = get_temp()
    
    if level == "shadow":
        # Shadow-Fixer nur bei < 55°C
        if temp > 55:
            print(f"HEAT-PROTECT: Shadow-Fixer übersprungen (CPU {temp:.1f}°C > 55°C)")
            return False
    elif level == "ollama":
        # Ollama-Calls nur bei < 65°C
        if temp > 65:
            print(f"HEAT-PROTECT: Ollama-Call blockiert (CPU {temp:.1f}°C > 65°C)")
            return False
    elif level == "emergency":
        # Notfall: Bei > 75°C ollama + llama-server killen
        if temp > 75:
            print(f"HEAT-EMERGENCY: CPU {temp:.1f}°C > 75°C - Kille ollama + llama-server")
            subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
            subprocess.run(["pkill", "-9", "-f", "ollama"], capture_output=True)
            return False
    
    return True

def emergency_shutdown():
    """Notfall-Shutdown: Killt alle Ollama-Prozesse."""
    subprocess.run(["pkill", "-9", "-f", "llama-server"], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "ollama"], capture_output=True)
    print("HEAT-EMERGENCY: Alle Ollama-Prozesse gekillt")
