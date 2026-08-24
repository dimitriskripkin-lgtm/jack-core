#!/usr/bin/env python3
"""ui_agent/package_mapper.py - Alle launchtbaren Apps + MAIN-Activity in SQLite."""
import sys, time, sqlite3, re
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")

from capture import _su, _ssh

DB = "/data/data/com.termux/files/home/jack/jack_memory.db"

def ensure_table():
    con = sqlite3.connect(DB)
    con.execute("""
        CREATE TABLE IF NOT EXISTS app_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package TEXT UNIQUE,
            activity TEXT,
            label TEXT,
            updated_ts TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_app_pkg ON app_packages(package)")
    con.commit()
    con.close()

def get_third_party_packages():
    out, rc = _su("pm list packages -3")
    if rc != 0 or not out:
        out, _ = _ssh("pm list packages -3")
    pkgs = []
    for line in (out or "").splitlines():
        line = line.strip()
        if line.startswith("package:"):
            pkgs.append(line.split("package:")[1].strip())
    return pkgs

def resolve_launcher_activity(package):
    # versucht die MAIN/LAUNCHER Activity zu finden
    cmd = f"cmd package resolve-activity --brief {package} 2>/dev/null | tail -1"
    out, rc = _su(cmd)
    if rc == 0 and out and "/" in out:
        return out.strip()
    # Fallback
    cmd2 = f"dumpsys package {package} 2>/dev/null | grep -A1 'android.intent.action.MAIN' | grep -m1 'android.intent.category.LAUNCHER' -B1 | head -1"
    out2, _ = _su(cmd2)
    if out2 and package in out2:
        m = re.search(rf"{re.escape(package)}/([a-zA-Z0-9_$.]+)", out2)
        if m:
            return f"{package}/{m.group(1)}"
    return None

def get_label(package):
    out, _ = _su(f"pm dump {package} 2>/dev/null | grep -m1 'applicationLabel=' || true")
    if out and "applicationLabel=" in out:
        return out.split("applicationLabel=")[-1].strip()[:60]
    return package.split(".")[-1]

def build_index():
    ensure_table()
    pkgs = get_third_party_packages()
    print(f"Gefundene 3rd-Party Packages: {len(pkgs)}")
    con = sqlite3.connect(DB)
    count = 0
    for i, pkg in enumerate(pkgs, 1):
        act = resolve_launcher_activity(pkg)
        if not act:
            continue
        label = get_label(pkg)
        con.execute(
            "INSERT OR REPLACE INTO app_packages (package, activity, label, updated_ts) VALUES (?,?,?,?)",
            (pkg, act, label, time.strftime("%Y-%m-%dT%H:%M:%S"))
        )
        count += 1
        if i % 15 == 0:
            print(f"  … {i}/{len(pkgs)} verarbeitet, {count} mit Activity")
            con.commit()
    con.commit()
    total = con.execute("SELECT COUNT(*) FROM app_packages").fetchone()[0]
    con.close()
    print(f"Fertig. app_packages: {total} Einträge")
    return total

def list_apps(limit=30):
    con = sqlite3.connect(DB)
    rows = con.execute("SELECT package, activity, label FROM app_packages ORDER BY label LIMIT ?", (limit,)).fetchall()
    con.close()
    return rows

def find_app(query):
    q = f"%{query}%"
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT package, activity, label FROM app_packages WHERE label LIKE ? OR package LIKE ? LIMIT 10",
        (q, q)
    ).fetchall()
    con.close()
    return rows

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        for r in list_apps(40):
            print(f"{r[2][:25]:25}  {r[0]}")
    elif len(sys.argv) > 1 and sys.argv[1] == "find":
        q = " ".join(sys.argv[2:]) or "chrome"
        for r in find_app(q):
            print(r)
    else:
        build_index()
