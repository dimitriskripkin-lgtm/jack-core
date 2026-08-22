"""Accessibility Events via Shizuku (P6, Qwen 22.08.)
Ersetzt jack_focus_monitor.py - fängt echte Accessibility Events ab."""
import subprocess, json, time, os

J = os.path.expanduser("~/jack")

def start_listener():
    """Startet Shizuku Accessibility Service Listener."""
    # Shizuku muss installiert und aktiviert sein
    try:
        result = subprocess.run(
            ["sh", "-c", "shizuku start-service com.example.accessibility"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print("Shizuku Accessibility Service gestartet")
            return True
        else:
            print(f"Shizuku FEHLER: {result.stderr}")
            return False
    except Exception as e:
        print(f"Shizuku nicht verfügbar: {e}")
        return False

def get_events():
    """Holt Accessibility Events von Shizuku."""
    try:
        result = subprocess.run(
            ["sh", "-c", "shizuku get-events"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            events = json.loads(result.stdout) if result.stdout.strip() else []
            return events
        return []
    except:
        return []

def process_event(event):
    """Verarbeitet ein Accessibility Event."""
    event_type = event.get("type", "unknown")
    package = event.get("package", "unknown")
    timestamp = event.get("timestamp", time.time())
    
    # Log to file
    log_file = os.path.join(J, "accessibility_events.json")
    try:
        events = []
        if os.path.exists(log_file):
            with open(log_file, encoding="utf-8") as f:
                events = json.load(f)
        events.append(event)
        # Keep only last 1000 events
        events = events[-1000:]
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
    except:
        pass
    
    print(f"Event: {event_type} | {package} | {timestamp}")
    return True

def main():
    """Haupt-Loop: Pollt Events von Shizuku."""
    if not start_listener():
        print("Shizuku nicht verfügbar - fallback zu jack_focus_monitor")
        return
    
    print("Accessibility Listener läuft...")
    while True:
        events = get_events()
        for event in events:
            process_event(event)
        time.sleep(2)

if __name__ == "__main__":
    main()
