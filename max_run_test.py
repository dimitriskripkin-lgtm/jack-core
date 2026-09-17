#!/usr/bin/env python
import sys, os, time, subprocess
sys.path.insert(0, "/data/data/com.termux/files/home/jack")

log = "/data/data/com.termux/files/home/jack/reports/max_run_test.log"
start = time.time()

def w(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with open(log, "a") as f:
        f.write(line + "\n")

w("MAX_RUN_TEST_START")
w("Ziel: Pruefe ob MAX_RUN=300s Gitter in jack_ollama_gate greift")

# Import das Gate-Modul
try:
    import jack_ollama_gate as gate
    w("GATE_MODUL_GELADEN")
    w("MAX_RUN = %d" % gate.MAX_RUN)
    w("IDLE_STOP = %d" % gate.IDLE_STOP)
except Exception as e:
    w("GATE_LADE_FEHLER: %s" % str(e))
    sys.exit(1)

# Pruefe Ollama-Status vorher
w("--- VORHER ---")
try:
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack",
                        "sv status /data/data/com.termux/files/usr/var/service/ollama"],
                       capture_output=True, text=True, timeout=15)
    w("Ollama vorher: %s" % r.stdout.strip())
except Exception as e:
    w("Status-Check Fehler: %s" % str(e)[:100])

# Versuche den Gate-Timer zu triggern
w("--- TIMER_TEST ---")
w("Versuche _schedule_stop() zu triggern...")
try:
    gate._start_ts = time.time()
    gate._schedule_stop()
    w("Timer gesetzt. Warte 100s auf IDLE_STOP (90s)...")
    
    # Alle 15s Status-Update
    for i in range(7):
        time.sleep(15)
        elapsed = time.time() - start
        try:
            r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "xiaomi-jack",
                                "sv status /data/data/com.termux/files/usr/var/service/ollama 2>&1 | head -1"],
                               capture_output=True, text=True, timeout=10)
            w("t+%ds: %s" % (int(elapsed), r.stdout.strip()[:80]))
        except:
            w("t+%ds: status-check timeout" % int(elapsed))
    
    w("--- NACHHER ---")
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack",
                        "sv status /data/data/com.termux/files/usr/var/service/ollama"],
                       capture_output=True, text=True, timeout=15)
    w("Ollama nachher: %s" % r.stdout.strip())
    
    if "down:" in r.stdout:
        w("ERGEBNIS: IDLE_STOP_HAT_GEGRIFFEN - Gitter funktioniert")
    else:
        w("ERGEBNIS: IDLE_STOP_HAT_NICHT_GEGRIFFEN - Timer evtl. nicht aktiv")
        
except Exception as e:
    w("FEHLER: %s" % str(e)[:200])

w("MAX_RUN_TEST_ENDE")
w("Dauer: %ds" % int(time.time() - start))
