"""Multi-Worker Registry (P11, Qwen 22.08.)
Verwaltet mehrere Worker-Devices für Load-Balancing."""
import subprocess, json, time, os

WORKERS_FILE = os.path.expanduser("~/jack/workers.json")

def load_workers():
    """Lädt Worker-Registry aus JSON."""
    if not os.path.exists(WORKERS_FILE):
        return []
    try:
        with open(WORKERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []

def save_workers(workers):
    """Speichert Worker-Registry als JSON."""
    with open(WORKERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(workers, f, indent=2)

def add_worker(name, ssh_alias, description=""):
    """Fügt neuen Worker zur Registry hinzu."""
    workers = load_workers()
    # Prüfe ob Worker schon existiert
    for w in workers:
        if w['name'] == name:
            print(f"Worker {name} existiert bereits")
            return
    worker = {
        'name': name,
        'ssh_alias': ssh_alias,
        'description': description,
        'added': time.strftime('%Y-%m-%d %H:%M:%S'),
        'last_check': None,
        'online': False,
        'temp': 0
    }
    workers.append(worker)
    save_workers(workers)
    print(f"Worker {name} hinzugefügt")

def check_worker_health(worker):
    """Prüft ob Worker online ist und holt Temperatur."""
    try:
        # SSH-Connect-Test
        r = subprocess.run(
            ["ssh", worker['ssh_alias'], "echo ok"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode != 0 or "ok" not in r.stdout:
            worker['online'] = False
            worker['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
            return worker
        
        # Temperatur holen
        r2 = subprocess.run(
            ["ssh", worker['ssh_alias'], "cat /sys/class/thermal/thermal_zone0/temp"],
            capture_output=True, text=True, timeout=5
        )
        if r2.returncode == 0 and r2.stdout.strip().isdigit():
            worker['temp'] = int(r2.stdout.strip()) / 1000
        else:
            worker['temp'] = 0
        
        worker['online'] = True
        worker['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        worker['online'] = False
        worker['last_check'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    return worker

def check_all_workers():
    """Checkt alle Worker und aktualisiert Status."""
    workers = load_workers()
    for w in workers:
        check_worker_health(w)
    save_workers(workers)
    return workers

def get_best_worker(honor_temp):
    """Wählt besten Worker basierend auf Temperatur und Verfügbarkeit.
    
    Logik:
    - Honor <= 55°C: Kein Worker nötig, return None
    - Honor > 55°C: Wähle Worker mit niedrigster Temperatur
    
    Returns:
        Worker-Dict oder None (wenn lokal ausführen)
    """
    if honor_temp <= 55:
        return None  # Honor ist kühl genug
    
    workers = load_workers()
    # Nur online Worker mit temp < 60°C berücksichtigen
    candidates = [w for w in workers if w.get('online') and w.get('temp', 999) < 60]
    
    if not candidates:
        return None  # Kein Worker verfügbar, Fallback lokal
    
    # Wähle Worker mit niedrigster Temperatur
    best = min(candidates, key=lambda w: w.get('temp', 999))
    return best

def list_workers():
    """Listet alle Worker mit Status."""
    workers = load_workers()
    if not workers:
        print("Keine Worker konfiguriert")
        return
    
    print(f"Worker-Registry ({len(workers)} Worker):")
    for w in workers:
        status = "🟢 ONLINE" if w.get('online') else "🔴 OFFLINE"
        temp = f"{w.get('temp', 0):.1f}°C" if w.get('temp') else "?"
        print(f"  {w['name']}: {status} | {temp} | {w['ssh_alias']}")

# Initialisiere mit xiaomi-jack als erstem Worker
if __name__ == "__main__":
    if not os.path.exists(WORKERS_FILE):
        add_worker("xiaomi", "xiaomi-jack", "Xiaomi 11T Pro - Snapdragon 888, 8GB RAM")
    check_all_workers()
    list_workers()
