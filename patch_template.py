#!/usr/bin/env python
"""
PATCH TEMPLATE fuer JACK
========================
Dieses Template zeigt, wie ein Patch mit harness.py durchgefuehrt wird.
Jeder Patch muss diese Stages durchlaufen:
1. BACKUP - Altes File sichern
2. PATCH - Code aendern
3. COMPILE - Syntax pruefen
4. RESTART - Dienst neu starten
5. PROBE - Testen ob es funktioniert

Nutzung:
    python patch_template.py --stage=all
    python patch_template.py --stage=backup
    python patch_template.py --stage=probe
"""

import sys
import os
import shutil
import subprocess
import argparse

jack_dir = "/data/data/com.termux/files/home/jack"
sys.path.insert(0, jack_dir)

try:
    import harness
except ImportError:
    print("FEHLER: harness.py nicht gefunden")
    sys.exit(1)

def stage_backup(source_file, backup_name):
    """Stage 1: Backup erstellen"""
    stage_name = "BACKUP_" + backup_name
    harness.stage_start(stage_name, {"file": source_file})
    
    try:
        attic = os.path.join(jack_dir, "attic")
        os.makedirs(attic, exist_ok=True)
        backup_path = os.path.join(attic, backup_name + ".bak")
        shutil.copy(source_file, backup_path)
        
        harness.stage_end(stage_name, "PASSED", {"backup_path": backup_path})
        print("BACKUP_OK: " + backup_path)
        return True
    except Exception as e:
        harness.stage_end(stage_name, "FAILED", error=str(e))
        print("BACKUP_FEHLER: " + str(e))
        return False

def stage_patch(target_file, patch_function):
    """Stage 2: Code aendern"""
    stage_name = "PATCH"
    harness.stage_start(stage_name, {"file": target_file})
    
    try:
        # pycache loeschen
        pycache = os.path.join(jack_dir, "__pycache__")
        if os.path.exists(pycache):
            shutil.rmtree(pycache)
            harness.log_evidence(stage_name, "pycache_deleted", {})
        
        # Patch anwenden
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = patch_function(content)
        
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        harness.stage_end(stage_name, "PASSED")
        print("PATCH_OK")
        return True
    except Exception as e:
        harness.stage_end(stage_name, "FAILED", error=str(e))
        print("PATCH_FEHLER: " + str(e))
        return False

def stage_compile(target_file):
    """Stage 3: Syntax pruefen"""
    stage_name = "COMPILE"
    harness.stage_start(stage_name, {"file": target_file})
    
    try:
        res = subprocess.run(
            [sys.executable, "-m", "py_compile", target_file],
            capture_output=True,
            text=True
        )
        
        if res.returncode == 0:
            harness.stage_end(stage_name, "PASSED")
            print("COMPILE_OK")
            return True
        else:
            harness.stage_end(stage_name, "FAILED", error=res.stderr)
            print("COMPILE_FEHLER: " + res.stderr)
            return False
    except Exception as e:
        harness.stage_end(stage_name, "FAILED", error=str(e))
        print("COMPILE_FEHLER: " + str(e))
        return False

def stage_restart(service_name):
    """Stage 4: Dienst neu starten"""
    stage_name = "RESTART"
    harness.stage_start(stage_name, {"service": service_name})
    
    try:
        service_dir = "/data/data/com.termux/files/usr/var/service"
        if not os.path.exists(service_dir):
            harness.stage_end(stage_name, "FAILED", error="Service-Verzeichnis fehlt")
            return False
        
        services = os.listdir(service_dir)
        if service_name not in services:
            harness.stage_end(stage_name, "FAILED", error="Dienst nicht gefunden")
            return False
        
        import time
        res = subprocess.run(["sv", "restart", service_name], capture_output=True, text=True)
        time.sleep(2)
        
        status_res = subprocess.run(["sv", "status", service_name], capture_output=True, text=True)
        
        if "run:" in status_res.stdout:
            harness.stage_end(stage_name, "PASSED", {"status": status_res.stdout.strip()})
            print("RESTART_OK: " + status_res.stdout.strip())
            return True
        else:
            harness.stage_end(stage_name, "FAILED", error=status_res.stdout)
            print("RESTART_FEHLER: " + status_res.stdout)
            return False
    except Exception as e:
        harness.stage_end(stage_name, "FAILED", error=str(e))
        print("RESTART_FEHLER: " + str(e))
        return False

def stage_probe(probe_function):
    """Stage 5: Testen"""
    stage_name = "PROBE"
    harness.stage_start(stage_name, {})
    
    try:
        result = probe_function()
        
        if result.get("success"):
            harness.stage_end(stage_name, "PASSED", result)
            print("PROBE_OK")
            return True
        else:
            harness.stage_end(stage_name, "FAILED", error=result.get("error", "Probe fehlgeschlagen"))
            print("PROBE_FEHLER: " + str(result))
            return False
    except Exception as e:
        harness.stage_end(stage_name, "FAILED", error=str(e))
        print("PROBE_FEHLER: " + str(e))
        return False

def run_all_stages(source_file, backup_name, patch_function, service_name, probe_function):
    """Alle Stages hintereinander ausfuehren"""
    print("=== PATCH PIPELINE START ===")
    print()
    
    if not stage_backup(source_file, backup_name):
        return False
    
    if not stage_patch(source_file, patch_function):
        return False
    
    if not stage_compile(source_file):
        print("ROLLBACK: Compile fehlgeschlagen, restore backup")
        attic = os.path.join(jack_dir, "attic")
        backup_path = os.path.join(attic, backup_name + ".bak")
        if os.path.exists(backup_path):
            shutil.copy(backup_path, source_file)
        return False
    
    if not stage_restart(service_name):
        print("ROLLBACK: Restart fehlgeschlagen, restore backup")
        attic = os.path.join(jack_dir, "attic")
        backup_path = os.path.join(attic, backup_name + ".bak")
        if os.path.exists(backup_path):
            shutil.copy(backup_path, source_file)
        return False
    
    if not stage_probe(probe_function):
        print("ROLLBACK: Probe fehlgeschlagen, restore backup")
        attic = os.path.join(jack_dir, "attic")
        backup_path = os.path.join(attic, backup_name + ".bak")
        if os.path.exists(backup_path):
            shutil.copy(backup_path, source_file)
        stage_restart(service_name)  # Dienst mit altem Code neu starten
        return False
    
    print()
    print("=== PATCH PIPELINE SUCCESS ===")
    return True

def show_recent_logs():
    """Zeigt die letzten Harness-Logs"""
    stages = harness.get_recent_stages(10)
    print("LETZTE_10_STAGES:")
    for s in stages:
        print("  " + s.get("stage", "?") + " | " + s.get("status", "?") + " | " + s.get("started_ts", "?"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JACK Patch Template")
    parser.add_argument("--stage", choices=["backup", "patch", "compile", "restart", "probe", "all", "logs"], 
                       default="all", help="Welche Stage ausfuehren")
    parser.add_argument("--source", help="Quelldatei fuer den Patch")
    parser.add_argument("--backup-name", help="Name fuer das Backup")
    parser.add_argument("--service", help="Dienstname fuer Restart")
    
    args = parser.parse_args()
    
    if args.stage == "logs":
        show_recent_logs()
    elif args.stage == "all":
        if not args.source or not args.backup_name or not args.service:
            print("FEHLER: --source, --backup-name und --service sind erforderlich")
            sys.exit(1)
        
        # Beispiel-Patch-Funktion
        def example_patch(content):
            return content  # Kein Aenderung
        
        # Beispiel-Probe-Funktion
        def example_probe():
            return {"success": True, "message": "Beispiel-Probe erfolgreich"}
        
        success = run_all_stages(args.source, args.backup_name, example_patch, args.service, example_probe)
        sys.exit(0 if success else 1)
    else:
        print("FEHLER: Einzelne Stages noch nicht implementiert")
        sys.exit(1)
