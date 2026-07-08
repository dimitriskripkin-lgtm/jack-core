#!/usr/bin/env python3
import os, sys, json, sqlite3, hashlib, time, subprocess, urllib.request
from datetime import datetime, date

sys.path.append(os.path.expanduser('~/jack'))
import jack_config, jack_gemini_bridge, jack_vecdb

ERRORS_DB = jack_config.get_param('STORAGE', 'db_path')
JACK_HOME = "/data/data/com.termux/files/home/jack"
RATE_FILE = f"{JACK_HOME}/.learning_rate"
SEEN_FILE = f"{JACK_HOME}/.learning_seen"
MAX_CALLS_PER_DAY = 20
HEARTBEAT = 1800  # 30 Minuten

HIGH_RISK = [
    "os.remove", "os.unlink", "shutil.rmtree", "shutil.rmdir",
    "rm -rf", "DROP TABLE", "DELETE FROM", "truncate", "wipe"
]

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}][LEARN][{level}] {msg}")

def rate_check():
    today = str(date.today())
    try:
        data = json.load(open(RATE_FILE))
        if data.get("date") != today:
            data = {"date": today, "count": 0}
    except:
        data = {"date": today, "count": 0}
    if data["count"] >= MAX_CALLS_PER_DAY:
        log(f"Rate-Limit erreicht ({MAX_CALLS_PER_DAY}/Tag)", "WARN")
        return False
    data["count"] += 1
    json.dump(data, open(RATE_FILE, "w"))
    log(f"API-Call {data['count']}/{MAX_CALLS_PER_DAY} heute")
    return True

def already_seen(error_msg):
    h = hashlib.md5(error_msg.encode()).hexdigest()
    try:
        seen = set(open(SEEN_FILE).read().splitlines())
    except:
        seen = set()
    if h in seen:
        return True
    with open(SEEN_FILE, "a") as f:
        f.write(h + "\n")
    return False


def ask_and_embed(error_id, module, err_type, err_msg, file_path, line_num, context):
    if not rate_check():
        return None
    prompt = (
        f"Python-Fehler in JACK (Android/Termux).\n"
        f"Modul: {module} | Typ: {err_type}\n"
        f"Datei: {file_path}:{line_num}\n"
        f"Fehler: {err_msg}\n"
        f"Kontext: {context}\n\n"
        f"Gib NUR korrigierten Python-Code zurück. Kein Markdown, keine Erklärung. "
        f"Falls nicht fixbar: antworte exakt CANNOT_FIX."
    )
    try:
        answer = jack_gemini_bridge.ask_gemini(prompt)
        log(f"Gemini geantwortet ({len(answer)} Zeichen)")
        emb = jack_gemini_bridge.get_embedding(answer) if hasattr(jack_gemini_bridge, 'get_embedding') else None
        if emb:
            jack_vecdb.save_vec(prompt, answer, emb)
            log("Antwort embedded + gespeichert")
        return answer
    except Exception as e:
        log(f"Gemini-Fehler: {e}", "ERROR")
        return None


def is_high_risk(code):
    return any(p in code for p in HIGH_RISK)

def apply_fix(error_id, file_path, fix_code):
    if not file_path or not os.path.exists(file_path):
        log(f"Datei nicht gefunden: {file_path}", "WARN")
        return False
    if is_high_risk(fix_code):
        log(f"HIGH-RISK Pattern — überspringe Error #{error_id}", "WARN")
        return False
    backup = file_path + f".bak_{int(time.time())}"
    try:
        import shutil
        shutil.copy2(file_path, backup)
        with open(file_path, 'w') as f:
            f.write(fix_code)
        result = subprocess.run(
            ["python3", "-m", "py_compile", file_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            shutil.copy2(backup, file_path)
            log(f"Syntax-Fehler im Fix — Rollback auf {backup}", "ERROR")
            return False
        con = sqlite3.connect(ERRORS_DB)
        con.execute(
            "UPDATE errors SET resolved=1, fix_applied=1, fix_ts=? WHERE id=?",
            (datetime.now().isoformat(), error_id)
        )
        con.commit(); con.close()
        log(f"✓ Error #{error_id} autonom gefixt: {file_path}")
        return True
    except Exception as e:
        log(f"Apply-Fehler: {e}", "ERROR")
        return False


def run_cycle():
    log("=== Lern-Zyklus gestartet ===")
    try:
        con = sqlite3.connect(ERRORS_DB)
        errors = con.execute(
            "SELECT id, module, error_type, error_msg, file_path, line_num, context "
            "FROM errors WHERE resolved=0 AND file_path IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT 5"
        ).fetchall()
        con.close()
    except Exception as e:
        log(f"DB-Fehler: {e}", "ERROR")
        return

    if not errors:
        log("Keine neuen Fehler mit file_path — nichts zu tun")
        return

    log(f"{len(errors)} Fehler gefunden")
    for row in errors:
        err_id, module, err_type, err_msg, file_path, line_num, context = row
        if already_seen(err_msg):
            log(f"Error #{err_id} bereits verarbeitet — skip")
            continue
        log(f"Verarbeite #{err_id}: {module} @ {file_path}:{line_num}")
        fix = ask_and_embed(err_id, module, err_type, err_msg, file_path, line_num, context)
        if not fix or fix.strip() == "CANNOT_FIX":
            log(f"Kein Fix für #{err_id}")
            continue
        apply_fix(err_id, file_path, fix)
        time.sleep(2)

def main():
    log("JACK Learning Loop gestartet — Heartbeat alle 30 Min")
    while True:
        try:
            run_cycle()
        except Exception as e:
            log(f"Zyklus-Fehler: {e}", "ERROR")
        log(f"Schlafe {HEARTBEAT}s bis zum nächsten Zyklus")
        time.sleep(HEARTBEAT)

if __name__ == "__main__":
    main()
