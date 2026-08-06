import subprocess
import sys
import time
import threading
import signal

TEMP_LIMIT = 85.0
stop_flag = False
process = None

def get_temp():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            return int(f.read().strip()) / 1000.0
    except:
        return 0.0

def temperature_monitor():
    global stop_flag, process
    start = time.time()
    print("🔥 Temperatur-Watchdog aktiv (Limit: 85°C)")
    while not stop_flag:
        temp = get_temp()
        elapsed = time.time() - start
        print(f"\r⏱️  [{elapsed:.1f}s] 🌡️  {temp:.1f}°C", end="", flush=True)
        
        if temp >= TEMP_LIMIT:
            print(f"\n\n🚨 TEMPERATUR-LIMIT ERREICHT ({temp:.1f}°C >= {TEMP_LIMIT}°C)")
            print("⛔ Breche Prozess ab...")
            stop_flag = True
            if process:
                process.kill()
            break
        
        time.sleep(1)

def signal_handler(sig, frame):
    global stop_flag, process
    print("\n\n⛔ Manuell abgebrochen (Strg+C)")
    stop_flag = True
    if process:
        process.kill()
    sys.exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    
    print("📋 Starte LiteRT-LM mit Temperatur-Überwachung")
    print(f"🎯 Prompt: {' '.join(sys.argv[1:])}")
    print()
    
    monitor_thread = threading.Thread(target=temperature_monitor, daemon=True)
    monitor_thread.start()
    
    cmd = ['litert-lm', 'run', 'gemma4-web', '--backend', 'gpu'] + sys.argv[1:]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    output = []
    for line in process.stdout:
        output.append(line)
        print(line, end='')
    
    process.wait()
    stop_flag = True
    monitor_thread.join(timeout=2)
    
    if process.returncode != 0:
        print(f"\n❌ Prozess wurde abgebrochen oder ist fehlgeschlagen (Exit-Code: {process.returncode})")
    else:
        print(f"\n✅ Prozess erfolgreich abgeschlossen")
