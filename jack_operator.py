#!/usr/bin/env python3
from jack_approval import confirm_action
import os, sys, json, subprocess, re
from datetime import datetime

JACK_HOME = "/data/data/com.termux/files/home"

class JackOperator:
    def __init__(self):
        self.cortex_cmd = "python ~/jack_cortex.py"
    
    def get_report(self):
        """Holt aktuellen Report von cortex."""
        result = subprocess.run(f"{self.cortex_cmd} report", shell=True, capture_output=True, text=True)
        try:
            return json.loads(result.stdout)
        except:
            return None
    
    def diagnose(self, report):
        """Analysiert Report — gibt Diagnose & empfohlene Aktionen zurück."""
        diagnosis = {
            "timestamp": report.get("timestamp"),
            "status": "OK",
            "issues": [],
            "recommended_actions": [],
            "severity": "INFO"
        }
        
        if report["errors_found"] == 0:
            diagnosis["status"] = "✓ SAUBER"
            diagnosis["message"] = "Alle Systeme laufen normal."
            return diagnosis
        
        # Critical Issues
        if report["critical"]:
            diagnosis["severity"] = "CRITICAL"
            diagnosis["status"] = "⚠ KRITISCH"
        else:
            diagnosis["severity"] = "WARNING"
            diagnosis["status"] = "⚠ FEHLER"
        
        # Analysiere Fehler
        for logfile, info in report.get("logs", {}).items():
            fname = os.path.basename(logfile)
            for err in info.get("errors", []):
                text = err.get("text", "")
                
                # Pattern-Matching für bekannte Fehler
                if "titan" in text.lower() and "crash" in text.lower():
                    diagnosis["issues"].append(f"TITAN: Crash erkannt in {fname}")
                    diagnosis["recommended_actions"].append("Kill TITAN: pkill -f titan")
                    diagnosis["recommended_actions"].append("Restart JACK: python ~/jack_loop_v3.py")
                
                elif "connection" in text.lower() and "lost" in text.lower():
                    diagnosis["issues"].append(f"ADB: Verbindung verloren ({fname})")
                    diagnosis["recommended_actions"].append("ADB reconnect: adb connect 192.168.178.154:9999")
                
                elif "memory" in text.lower() and "error" in text.lower():
                    diagnosis["issues"].append(f"MEMORY: Fehler erkannt ({fname})")
                    diagnosis["recommended_actions"].append("Check DB: sqlite3 ~/jack/jack_memory.db 'SELECT COUNT(*) FROM vision_log;'")
                
                elif "timeout" in text.lower():
                    diagnosis["issues"].append(f"TIMEOUT: {fname}")
                    diagnosis["recommended_actions"].append("System langsam — Prozesse checken: ps aux")
                
                else:
                    diagnosis["issues"].append(f"{fname}: {text[:60]}")
        
        return diagnosis
    
    def propose_action(self, diagnosis):
        """Präsentiert Diagnose und fragt nach Bestätigung."""
        print("\n" + "="*70)
        print(f"[JACK OPERATOR] {diagnosis['timestamp']}")
        print("="*70)
        print(f"\n📊 STATUS: {diagnosis['status']}")
        print(f"🔴 SEVERITY: {diagnosis['severity']}")
        
        if diagnosis.get("message"):
            print(f"\n✓ {diagnosis['message']}")
            print("\n" + "="*70 + "\n")
            return None
        
        print(f"\n⚠ ISSUES ({len(diagnosis['issues'])}):")
        for issue in diagnosis["issues"]:
            print(f"  • {issue}")
        
        if not diagnosis["recommended_actions"]:
            print("\n✓ Keine automatischen Aktionen nötig.")
            print("="*70 + "\n")
            return None
        
        print(f"\n📝 EMPFOHLENE AKTIONEN ({len(diagnosis['recommended_actions'])}):")
        for i, action in enumerate(diagnosis["recommended_actions"], 1):
            print(f"  {i}. {action}")
        
        print("\n" + "="*70)
        print("Soll ich diese Aktionen ausführen?")
        approved = confirm_action(f"{len(diagnosis['recommended_actions'])} Aktion(en) ausfuehren"); response = "ja" if approved else "nein"
        
        if response == "show":
            print("\n[FULL REPORT]")
            print(json.dumps(diagnosis, indent=2))
            approved2 = confirm_action("Aktionen nach Full-Report ausfuehren"); response = "ja" if approved2 else "nein"
        
        if response in ["ja", "y", "yes"]:
            return diagnosis["recommended_actions"]
        else:
            print("[OPERATOR] Abgebrochen.")
            return None
    
    def execute_actions(self, actions):
        """Führt die genehmigten Aktionen aus."""
        print(f"\n[OPERATOR] Führe {len(actions)} Aktionen aus ...\n")
        results = []
        
        for i, action in enumerate(actions, 1):
            print(f"[{i}/{len(actions)}] $ {action}")
            try:
                result = subprocess.run(action, shell=True, capture_output=True, text=True, timeout=15)
                output = result.stdout.strip() + result.stderr.strip()
                success = result.returncode == 0
                
                if success:
                    print(f"  ✓ OK")
                else:
                    print(f"  ✗ Error (code {result.returncode})")
                
                if output:
                    print(f"  > {output[:100]}")
                
                results.append({
                    "action": action,
                    "returncode": result.returncode,
                    "output": output,
                    "success": success
                })
            except subprocess.TimeoutExpired:
                print(f"  ✗ TIMEOUT")
                results.append({"action": action, "success": False, "error": "TIMEOUT"})
            except Exception as e:
                print(f"  ✗ {e}")
                results.append({"action": action, "success": False, "error": str(e)})
        
        return results
    
    def report_results(self, results):
        """Berichtet Ausführungs-Resultat."""
        success_count = sum(1 for r in results if r["success"])
        print(f"\n{'='*70}")
        print(f"[OPERATOR] Resultat: {success_count}/{len(results)} erfolgreich")
        print("="*70)
        
        for r in results:
            status = "✓" if r["success"] else "✗"
            print(f"{status} {r['action'][:60]}")
        
        print()
    
    def run_once(self):
        """Einmalige Diagnose & Ausführung."""
        print("[OPERATOR] Scanning ...\n")
        report = self.get_report()
        
        if not report:
            print("[ERROR] Report konnte nicht gelesen werden.")
            return
        
        diagnosis = self.diagnose(report)
        actions = self.propose_action(diagnosis)
        
        if actions:
            results = self.execute_actions(actions)
            self.report_results(results)
            
            # Neuen Report nach Aktionen
            print("[OPERATOR] Neuer Report nach Aktionen ...\n")
            new_report = self.get_report()
            new_diagnosis = self.diagnose(new_report)
            print(f"📊 NEUER STATUS: {new_diagnosis['status']}\n")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="JACK Operator — Autonomer Debugger mit Bestätigung")
    ap.add_argument("mode", nargs="?", default="run", choices=["run", "report", "diagnose"])
    args = ap.parse_args()
    
    op = JackOperator()
    
    if args.mode == "run":
        op.run_once()
    elif args.mode == "report":
        report = op.get_report()
        print(json.dumps(report, indent=2))
    elif args.mode == "diagnose":
        report = op.get_report()
        diagnosis = op.diagnose(report)
        print(json.dumps(diagnosis, indent=2))
