"""Circuit-Breaker: Shadow-Fixer nach 3x Fail komplett stoppen (Qwen 22.08.)"""
import os, json, datetime
J = os.path.expanduser("~/jack")
STATE_FILE = os.path.join(J, ".circuit_breaker_state.json")

def load_state():
    try:
        if os.path.exists(STATE_FILE):
            return json.load(open(STATE_FILE, encoding="utf-8"))
    except Exception: pass
    return {"fail_count": 0, "disabled": False, "disabled_at": None}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception: pass

def check_allowed():
    state = load_state()
    if state["disabled"]:
        print(f"CIRCUIT-BREAKER: Shadow-Fixer deaktiviert seit {state['disabled_at']}")
        return False
    return True

def record_failure():
    state = load_state()
    state["fail_count"] += 1
    print(f"CIRCUIT-BREAKER: Fail #{state['fail_count']}/3")
    if state["fail_count"] >= 3:
        state["disabled"] = True
        state["disabled_at"] = datetime.datetime.now().isoformat()
        print("CIRCUIT-BREAKER: Shadow-Fixer nach 3 Fails DEAKTIVIERT")
    save_state(state)

def reset():
    state = {"fail_count": 0, "disabled": False, "disabled_at": None}
    save_state(state)
    print("CIRCUIT-BREAKER: Zurückgesetzt")

def get_status():
    state = load_state()
    if state["disabled"]:
        return f"DEAKTIVIERT seit {state['disabled_at']}"
    return f"Aktiv ({state['fail_count']}/3 Fails)"
