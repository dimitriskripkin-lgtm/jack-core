#!/usr/bin/env python3
"""jack_health_monitor.py — Nach Approve: Selftest, Score gesunken → Rollback."""
MODULE_VERSION = 1

import os, sys, json, time, shutil, subprocess
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
LOG = os.path.join(J, "health_monitor.log")
ROLLBACK_LOG = os.path.join(J, "rollbacks.log")
SCORE_STATE = os.path.join(J, "last_selftest_score.json")

def _log(msg, f=None):
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    line = f"{ts} {msg}\n"
    with open(f or LOG, "a") as fh: fh.write(line)

def get_current_score():
    try:
        r = subprocess.run(["python3", os.path.join(J,"jack_selftest.py")],
            capture_output=True, text=True, timeout=30)
        for line in r.stdout.splitlines():
            if "Score:" in line:
                import re
                m = re.search(r"(\d+)%", line)
                if m: return int(m.group(1))
    except Exception as e:
        _log(f"Selftest-Fehler: {e}")
    return None

def save_score(score):
    json.dump({"score": score, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
        open(SCORE_STATE,"w"))

def load_last_score():
    try:
        return json.load(open(SCORE_STATE)).get("score", 100)
    except Exception: return 100

def rollback(fpath):
    bak = fpath + ".fix.bak"
    if os.path.exists(bak):
        shutil.copy2(bak, fpath)
        os.remove(bak)
        _log(f"ROLLBACK: {os.path.basename(fpath)}", ROLLBACK_LOG)
        return True
    return False

def notify(msg):
    try:
        import jack_notify as _jn
        _jn.notify(msg)
    except Exception: pass

def check_after_approve(approved_file=None):
    """Wird nach jedem Approve aufgerufen. Prüft ob Score gesunken."""
    last = load_last_score()
    time.sleep(5)  # Kurz warten damit Dienste neu starten können
    current = get_current_score()
    if current is None:
        _log("Score nicht ermittelbar — skip")
        return

    _log(f"Score: {last}% → {current}%")
    save_score(current)

    if current < last - 5:  # Score um mehr als 5% gesunken
        _log(f"WARNUNG: Score gesunken {last}% → {current}%")
        if approved_file and rollback(approved_file):
            notify(f"⚠️ Rollback: {os.path.basename(approved_file)}\nScore: {last}% → {current}%\nFix rückgängig gemacht.")
            _log(f"Rollback erfolgreich: {approved_file}")
        else:
            notify(f"⚠️ Score gesunken: {last}% → {current}%\nKein .bak gefunden — manuell prüfen.")
    elif current == 100:
        _log("Score 100% — alles sauber")

def run():
    """Regelmäßiger Check — Score speichern."""
    score = get_current_score()
    if score is not None:
        save_score(score)
        _log(f"Score: {score}%")
    return score

if __name__ == "__main__":
    s = run()
    print(f"Health-Monitor: Score {s}%")
