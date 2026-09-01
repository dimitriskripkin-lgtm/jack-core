#!/data/data/com.termux/files/usr/bin/python3
"""UI-Session: Vordergrund + optional UI-Dump vom Xiaomi. Lesen vor Schreiben."""
import re, subprocess, json, time, os
J="/data/data/com.termux/files/home/jack"

def sh(remote, t=25):
    r=subprocess.run(
        ["ssh","-o","BatchMode=yes","-o","ConnectTimeout=10","xiaomi-jack", remote],
        capture_output=True, text=True, timeout=t)
    return r.returncode, (r.stdout or "")+(r.stderr or "")

def get_foreground():
    remote = "su -c 'dumpsys window | grep mCurrentFocus; dumpsys window | grep mFocusedApp'"
    rc, out = sh(remote)
    pkg=act=None
    m=re.search(r"([a-zA-Z0-9_.]+)/([a-zA-Z0-9_.$]+)", out)
    if m:
        pkg, act = m.group(1), m.group(2)
    return {"ok": rc==0 and pkg is not None, "pkg": pkg, "activity": act, "raw": out[:400], "ts": time.strftime("%Y-%m-%d %H:%M:%S")}

def ui_dump(max_chars=120000):
    """uiautomator dump — Hierarchie der aktuellen UI."""
    remote = "su -c 'uiautomator dump /sdcard/jack_ui.xml >/dev/null 2>&1; cat /sdcard/jack_ui.xml'"
    rc, out = sh(remote, t=40)
    return {"ok": rc==0 and "<hierarchy" in out, "xml": out[:max_chars] if max_chars else out, "n": len(out), "ts": time.strftime("%Y-%m-%d %H:%M:%S")}

if __name__ == "__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="dump":
        print(json.dumps(ui_dump(max_chars=120000), ensure_ascii=False))
    else:
        print(json.dumps(get_foreground(), ensure_ascii=False))
