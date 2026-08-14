#!/usr/bin/env python3
import datetime
import os
import json

def get_current_rhythm():
    now = datetime.datetime.now()
    hour = now.hour
    
    # Rhythmus-Logik (Dahlhoff Nachtschicht / Schlaf / Power-Time)
    if 22 <= hour or hour < 6:
        state = "NACHTSCHICHT"
    elif 6 <= hour < 14:
        state = "SCHLAF_REST"
    else:
        state = "POWER_TIME"
        
    data = {
        "rhythm_state": state,
        "updated_at": now.isoformat(),
        "hour": hour
    }
    
    out_path = os.path.expanduser("~/jack/jack_rhythm_state.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    return state

if __name__ == "__main__":
    current = get_current_rhythm()
    print(f"[OK] Tagesrhythmus erkannt: {current}")
