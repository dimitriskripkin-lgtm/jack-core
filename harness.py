import json
import time
import os

HARNESS_LOG = "/data/data/com.termux/files/home/jack/reports/harness.jsonl"

def stage_start(stage_name, metadata=None):
    """Startet eine Stage und loggt den Beginn."""
    entry = {
        "stage": stage_name,
        "status": "RUNNING",
        "started_at": time.time(),
        "started_ts": time.strftime("%Y-%m-%d_%H:%M:%S"),
        "metadata": metadata or {}
    }
    with open(HARNESS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + chr(10))
    return entry

def stage_end(stage_name, status, evidence=None, error=None):
    """Beendet eine Stage und loggt das Ergebnis mit Evidence."""
    if status not in ["PASSED", "FAILED", "ROLLED_BACK"]:
        raise ValueError("Status muss PASSED, FAILED oder ROLLED_BACK sein")
    
    entry = {
        "stage": stage_name,
        "status": status,
        "ended_at": time.time(),
        "ended_ts": time.strftime("%Y-%m-%d_%H:%M:%S"),
        "evidence": evidence or [],
        "error": error
    }
    with open(HARNESS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + chr(10))
    return entry

def log_evidence(stage_name, evidence_type, content):
    """Fügt Evidence zu einer laufenden Stage hinzu."""
    entry = {
        "stage": stage_name,
        "evidence_type": evidence_type,
        "content": content,
        "logged_at": time.time(),
        "logged_ts": time.strftime("%Y-%m-%d_%H:%M:%S")
    }
    with open(HARNESS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + chr(10))
    return entry

def get_recent_stages(n=10):
    """Liest die letzten n Stages aus dem Log."""
    if not os.path.exists(HARNESS_LOG):
        return []
    
    stages = []
    with open(HARNESS_LOG, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                stages.append(entry)
            except json.JSONDecodeError:
                pass
    
    return stages[-n:]

def get_current_state():
    """Gibt den aktuellen State zurück (letzte Stage pro Stage-Name)."""
    stages = get_recent_stages(n=100)
    state = {}
    for s in stages:
        if "stage" in s:
            state[s["stage"]] = s.get("status", "UNBEKANNT")
    return state

def validate_pipeline(required_stages):
    """Prüft, ob alle erforderlichen Stages PASSED sind."""
    state = get_current_state()
    for stage in required_stages:
        if state.get(stage) != "PASSED":
            return False, f"Stage {stage} ist nicht PASSED (Status: {state.get(stage, 'FEHLT')})"
    return True, "Alle Stages PASSED"

if __name__ == "__main__":
    print("HARNESS_MODUL_GELADEN")
    print("Verfügbare Funktionen:")
    print("- stage_start(stage_name, metadata)")
    print("- stage_end(stage_name, status, evidence, error)")
    print("- log_evidence(stage_name, evidence_type, content)")
    print("- get_recent_stages(n)")
    print("- get_current_state()")
    print("- validate_pipeline(required_stages)")
