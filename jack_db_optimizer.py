#!/usr/bin/env python3
"""JACK DB Optimizer: Erzwingt busy_timeout=5000 und managed WAL-Checkpointing."""
import os
import sqlite3
import py_compile
import shutil

JACK_DIR = os.path.expanduser("~/jack")
DB_PATH = os.path.join(JACK_DIR, "jack_memory.db")
WAL_PATH = DB_PATH + "-wal"

def enforce_pragmas():
    """Setzt busy_timeout und wal_mode, falls nicht korrekt."""
    if not os.path.exists(DB_PATH):
        return False, "DB nicht gefunden"
    
    backup_path = DB_PATH + ".bak"
    try:
        # 1. Backup
        shutil.copy2(DB_PATH, backup_path)
        
        # 2. Verbindung mit Timeout (Fallback, falls in DB noch 0 steht)
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        
        # 3. Pragmas setzen
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        
        # 4. Verifizieren
        res_timeout = conn.execute("PRAGMA busy_timeout;").fetchone()[0]
        res_wal = conn.execute("PRAGMA journal_mode;").fetchone()[0].lower()
        
        conn.close()
        
        if res_timeout >= 5000 and res_wal == 'wal':
            return True, f"Pragmas gesetzt: timeout={res_timeout}, mode={res_wal}"
        else:
            return False, f"Pragma-Check fehlgeschlagen: timeout={res_timeout}, mode={res_wal}"
            
    except Exception as e:
        # Rollback
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DB_PATH)
        return False, f"Fehler: {str(e)[:80]}"

def optimize_wal(min_ram_mb=800, max_wal_mb=2):
    """Führt WAL-Checkpoint durch, wenn Datei zu groß wird UND RAM ausreicht."""
    if not os.path.exists(WAL_PATH):
        return True, "Kein WAL-File vorhanden, nichts zu tun."
    
    wal_size_mb = os.path.getsize(WAL_PATH) / (1024 * 1024)
    if wal_size_mb < max_wal_mb:
        return True, f"WAL-File klein genug ({wal_size_mb:.2f} MB)"
    
    # RAM-Check (vereinfacht, wie in jack_queue)
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if 'MemAvailable' in line:
                    ram_mb = int(line.split()[1]) // 1024
                    if ram_mb < min_ram_mb:
                        return False, f"RAM zu niedrig für WAL-Checkpoint ({ram_mb}MB < {min_ram_mb}MB)"
    except Exception:
        pass # Fallback: erlauben
    
    try:
        backup_path = DB_PATH + ".bak"
        shutil.copy2(DB_PATH, backup_path)
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        conn.close()
        
        return True, f"WAL-Checkpoint erfolgreich (vorher {wal_size_mb:.2f} MB)"
    except Exception as e:
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, DB_PATH)
        return False, f"Checkpoint-Fehler: {str(e)[:80]}"

if __name__ == "__main__":
    print("[1/2] Prüfe und fixen Pragmas...")
    success, msg = enforce_pragmas()
    print(f"  {'[OK]' if success else '[FEHLER]'} {msg}")
    
    print("[2/2] Prüfe WAL-Status...")
    success, msg = optimize_wal()
    print(f"  {'[OK]' if success else '[WARN]'} {msg}")
    
    # py_compile Selbsttest
    script_path = os.path.join(os.environ.get('PREFIX', '/data/data/com.termux/files/usr'), "tmp", "jack_db_optimizer.py")
    try:
        py_compile.compile(script_path, doraise=True)
        print("[OK] Syntax validiert (py_compile).")
    except Exception as e:
        print(f"[FEHLER] Syntax: {e}")
