#!/data/data/com.termux/files/usr/bin/python3
# JACK_YT_HYBRID — Lock/Home → RVX → Suche → OCR-Check → UI-Dump-Tap
import os, re, time, json, subprocess
from urllib.parse import quote

J = "/data/data/com.termux/files/home/jack"
OUT = os.path.join(J, "ui_learn")
YT = "app.rvx.android.youtube"
os.makedirs(OUT, exist_ok=True)

def ssh(cmd, t=30):
    r = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "xiaomi-jack", cmd],
        capture_output=True, text=True, timeout=t,
    )
    return r.returncode, (r.stdout or "") + (r.stderr or "")

def focus():
    rc, o = ssh("su -c \"dumpsys window | grep -E 'mCurrentFocus|mShowingLockscreen|isStatusBarKeyguard'\"")
    low = o.lower()
    locked = ("keyguard" in low and "true" in low) or ("lockscreen" in low and "true" in low)
    home = ("miui.home" in o) or ("launcher.Launcher" in o)
    yt = (YT in o) or ("youtube" in low)
    return locked, home, yt

def ensure_unlock(force=False):
    locked, home, yt = focus()
    if not (locked or force):
        return locked, home, yt
    # 1) aufwecken
    ssh("su -c 'input keyevent 224'")  # WAKEUP
    time.sleep(0.3)
    ssh("su -c 'input keyevent 82'")
    time.sleep(0.2)
    # 2) mehrere Swipe-Varianten (MIUI + AOSP)
    for y1,y2,dur in ((2100,350,320),(2000,400,280),(1900,500,250),(1800,600,220)):
        ssh("su -c 'input swipe 540 %d 540 %d %d'" % (y1,y2,dur))
        time.sleep(0.55)
        locked, home, yt = focus()
        if not locked:
            break
    # 3) falls noch Keyguard: BACK + nochmal swipe
    if locked:
        ssh("su -c 'input keyevent 4'")
        time.sleep(0.2)
        ssh("su -c 'input swipe 540 2000 540 300 350'")
        time.sleep(0.7)
        locked, home, yt = focus()
    return locked, home, yt

def page_ocr_ok(query):
    ssh("su -c 'screencap -p /sdcard/jack_cap.png'")
    full = os.path.join(OUT, "yt_full.png")
    img = os.path.join(OUT, "yt_small.jpg")
    subprocess.run(["scp", "-o", "BatchMode=yes", "xiaomi-jack:/sdcard/jack_cap.png", full], timeout=40)
    subprocess.run(["ffmpeg", "-y", "-i", full, "-vf", "scale=720:-1", "-q:v", "6", img],
                   capture_output=True, timeout=25)
    if not os.path.isfile(img):
        return False
    r = subprocess.run(["tesseract", img, "stdout", "-l", "deu+eng", "--psm", "11"],
                       capture_output=True, text=True, timeout=60)
    ot = (r.stdout or "").lower()
    q = (query or "").lower()
    return (q and q in ot) or ("ergebnis" in ot) or ("mix" in ot)

def dump_cands(query):
    rc, xml = ssh("su -c 'uiautomator dump /sdcard/jack_ui.xml >/dev/null && cat /sdcard/jack_ui.xml'")
    nodes = re.findall(r"<node[^>]+>", xml)
    q = (query or "").lower()
    keys = [w for w in re.split(r"\W+", q) if len(w) > 2] or ([q] if q else [])
    ban = ("abonn", "kanal aufrufen", "youtube music", "startseite", "shorts",
           "benachricht", "weitere information")
    cands = []
    for n in nodes:
        if 'clickable="true"' not in n:
            continue
        tx = re.search(r'text="([^"]*)"', n)
        cd = re.search(r'content-desc="([^"]*)"', n)
        lab = ((tx.group(1) if tx else "") + " " + (cd.group(1) if cd else "")).strip()
        if len(lab) < 3:
            continue
        low = lab.lower()
        if any(b in low for b in ban):
            continue
        m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', n)
        if not m:
            continue
        x1, y1, x2, y2 = map(int, m.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        h = y2 - y1
        if cy < 280 or cy > 1900 or h < 80:
            continue
        sc = sum(1 for w in keys if w in low)
        if "mix" in low:
            sc += 1
        if h > 150:
            sc += 1
        if sc:
            cands.append((sc, h, cy, cx, lab[:80]))
    cands.sort(reverse=True)
    return cands

def play(query="sido", save_recipe=True):
    ensure_unlock(force=True)
    ssh("su -c 'monkey -p %s -c android.intent.category.LAUNCHER 1'" % YT)
    time.sleep(1.4)
    url = "https://www.youtube.com/results?search_query=" + quote(query)
    ssh("su -c \"am start -a android.intent.action.VIEW -d '%s' -p %s\"" % (url, YT))
    time.sleep(2.6)
    locked, home, yt = focus()
    ok = page_ocr_ok(query)
    cands = dump_cands(query)
    if not cands:
        return {"ok": False, "reason": "no_cands", "page_ok": ok, "yt_focus": yt}
    sc, h, cy, cx, lab = cands[0]
    ssh("su -c 'input tap %d %d'" % (cx, cy))
    rec = {
        "ok": True, "app": YT, "query": query, "label": lab,
        "tap": [cx, cy], "page_ok": ok, "yt_focus": yt,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if save_recipe:
        path = os.path.join(OUT, "recipe_yt_%s.json" % re.sub(r"\W+", "_", query)[:40])
        open(path, "w", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False, indent=2))
        rec["recipe"] = path
    return rec

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "sido"
    print(json.dumps(play(q), ensure_ascii=False, indent=2))
