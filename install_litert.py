import subprocess, sys, time, threading
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

def temp():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp") as f:
            return int(f.read().strip()) / 1000
    except:
        return 0

done = False

def monitor():
    start = time.time()
    while not done:
        t = temp()
        elapsed = time.time() - start
        m, s = divmod(int(elapsed), 60)
        if t > 52:
            print(f"\n🔥 ÜBER 52°C ({t:.1f}°C) - JETZT ABRECHEN MIT STRG+C")
        elif t > 50:
            print(f"\r⚠️  [{m:02d}:{s:02d}] Temp: {t:.1f}°C HEISS", end="", flush=True)
        else:
            print(f"\r[{m:02d}:{s:02d}] Temp: {t:.1f}°C", end="", flush=True)
        time.sleep(5)

print("Starte pip install litert-lm")
print("STRG+C zum Abbrechen (Temperatur sinkt dann)")
print("=" * 40)

threading.Thread(target=monitor, daemon=True).start()

try:
    proc = subprocess.Popen(
        [sys.executable, "-m", "pip", "install", "litert-lm"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        print("\r" + line, end="", flush=True)
    proc.wait()
    done = True
    if proc.returncode == 0:
        print("\n✅ Installation erfolgreich")
    else:
        print(f"\n❌ Fehler Exit-Code {proc.returncode}")
except KeyboardInterrupt:
    done = True
    if 'proc' in locals():
        proc.kill()
    print("\n⛔ Abgebrochen. Temperatur sinkt jetzt.")
