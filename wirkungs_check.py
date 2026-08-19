import subprocess, time
def check_ui():
    try:
        # Xiaomi muss erreichbar sein!
        r = subprocess.run(
            ["ssh", "-i", "~/.ssh/id_jack", "-p", "8022", "root@10.58.220.131",
             "dumpsys activity activities | grep mResumedActivity"],
            capture_output=True, text=True, timeout=5
        )
        return "com.android.systemui" not in r.stdout
    except:
        return False

if __name__ == "__main__":
    print("BEFORE:", check_ui())
    time.sleep(2)
    print("AFTER:", check_ui())
