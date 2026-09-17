#!/usr/bin/env python
import subprocess
import time
import json
import sys

log_path = "/data/data/com.termux/files/home/jack/reports/max_run_test.log"
start_time = time.time()

def log(msg):
    with open(log_path, "a") as f:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")
    print(f"[{ts}] {msg}")

log("=== MAX_RUN_TEST_START ===")
log(f"Test gestartet um {time.strftime('%Y-%m-%d %H:%M:%S')}")
log("Ziel: Pruefen ob MAX_RUN 300s Gitter greift")
log("")

# 2. Haengenden Ollama-Call starten (der nie antwortet)
log("Starte haengenden Ollama-Call auf Xiaomi...")
try:
    # Ein Call der absichtlich haengt (sehr grosser Prompt oder invalides Modell)
    cmd = [
        "ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack",
        "curl -s --max-time 600 http://localhost:11434/api/chat -d '{"model":"invalid-model-does-not-exist","messages":[{"role":"user","content":"test"}],"stream":false}'"
    ]
    
    log(f"Call gestartet mit PID {os.getpid()}")
    log("Warte auf Antwort oder MAX_RUN Kill...")
    
    # Starte den Call
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    
    elapsed = time.time() - start_time
    log(f"Call beendet nach {elapsed:.1f}s")
    log(f"Return code: {result.returncode}")
    log(f"Stdout: {result.stdout[:200] if result.stdout else '(leer)'}")
    log(f"Stderr: {result.stderr[:200] if result.stderr else '(leer)'}")
    
except subprocess.TimeoutExpired:
    elapsed = time.time() - start_time
    log(f"TIMEOUT nach {elapsed:.1f}s - Call haengt noch")
    log("STATUS: MAX_RUN Gitter hat NICHT gegriffen (oder Call ist auf Honor, nicht Xiaomi)")
except Exception as e:
    elapsed = time.time() - start_time
    log(f"FEHLER nach {elapsed:.1f}s: {str(e)[:200]}")

log("")
log("=== MAX_RUN_TEST_ENDE ===")
log("")

# 3. Pruefe ob Ollama auf Xiaomi noch laeuft
log("Pruefe Ollama-Status auf Xiaomi nach Test:")
try:
    status = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack",
         "sv status /data/data/com.termux/files/usr/var/service/ollama"],
        capture_output=True, text=True, timeout=15
    )
    log(f"Ollama Status: {status.stdout.strip()}")
except Exception as e:
    log(f"Status-Check fehlgeschlagen: {str(e)[:100]}")

# 4. Pruefe uptime von Ollama
log("")
log("Pruefe Ollama-Uptime:")
try:
    uptime = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "xiaomi-jack",
         "ps aux | grep 'ollama serve' | grep -v grep"],
        capture_output=True, text=True, timeout=10
    )
    log(f"Ollama Prozess: {uptime.stdout.strip()[:150]}")
except Exception as e:
    log(f"Uptime-Check fehlgeschlagen: {str(e)[:100]}")

log("")
log("Test abgeschlossen. Log-Datei: " + log_path)
