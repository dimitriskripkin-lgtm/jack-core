"""Window-Events via Shizuku rish (P6 real v3, Qwen 22.08.)
Pollt mCurrentFocus alle 5s. Kein Fake-Shizuku mehr."""
import subprocess, json, time, os

J = os.path.expanduser("~/jack")
LOG = os.path.join(J, "accessibility_events.json")
RISH = "/data/data/com.termux/files/usr/bin/rish"

def shizuku_cmd(cmd):
    try:
        r = subprocess.run(["sh", RISH, "-c", cmd], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return None

def get_focus():
    out = shizuku_cmd("dumpsys window 2>/dev/null | grep -m1 mCurrentFocus")
    if out and "u0 " in out:
        return out.split("u0 ")[-1].split("}")[0].strip()
    if out:
        return out.split()[-1].split("}")[0].strip()
    return None

def log_event(ev):
    try:
        events = []
        if os.path.exists(LOG):
            with open(LOG, encoding="utf-8") as f:
                events = json.load(f)
        events.append(ev)
        with open(LOG, "w", encoding="utf-8") as f:
            json.dump(events[-1000:], f, indent=2)
    except Exception:
        pass

def main():
    if not os.path.exists(RISH):
        print("P6: rish fehlt. Beende.")
        return
    test = shizuku_cmd("id")
    if not test:
        print("P6: rish ohne Antwort - Termux in Shizuku-App autorisieren. Beende.")
        return
    print(f"P6: rish OK ({test[:40]}), Listener laeuft...")
    last = None
    while True:
        focus = get_focus()
        if focus and focus != last:
            log_event({"type": "window_change", "package": focus, "timestamp": time.time()})
            print(f"Event: {focus}")
            last = focus
        time.sleep(5)

if __name__ == "__main__":
    main()
