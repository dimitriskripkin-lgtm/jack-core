import sys, time, subprocess
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
from jack_vision_selector import dump_screen, list_elements

def su(cmd):
    r = subprocess.run(["ssh", "xiaomi-jack", "su", "-c", cmd], capture_output=True, text=True, timeout=20)
    return (r.stdout or "") + (r.stderr or "")

def mid_bounds(chunk):
    a = chunk.find("[")
    b = chunk.find("]", a)
    c = chunk.find("[", b)
    d = chunk.find("]", c)
    if a < 0 or d < 0:
        return None
    x1, y1 = chunk[a+1:b].split(",")
    x2, y2 = chunk[c+1:d].split(",")
    return (int(x1)+int(x2))//2, (int(y1)+int(y2))//2

def find_q(xml, query):
    if not xml:
        return None
    q = query.lower()
    low = xml.lower()
    start = 0
    while True:
        i = low.find(q, start)
        if i < 0:
            return None
        ns = xml.rfind("<", 0, i)
        ne = xml.find(">", i)
        if ns >= 0 and ne > ns:
            node = xml[ns:ne+1]
            bi = node.find("bounds=")
            if bi >= 0:
                p = mid_bounds(node[bi:])
                if p:
                    return p
        start = i + 1

def unlock():
    su("input keyevent 224")
    time.sleep(0.2)
    su("input keyevent 82")
    time.sleep(0.15)
    su("input swipe 540 1550 540 850 200")
    time.sleep(0.45)

def focus():
    for ln in su("dumpsys window").splitlines():
        if "mCurrentFocus" in ln:
            return ln.strip()
    return "?"

def playing():
    s = su("dumpsys media_session")
    return "package=com.android.chrome" in s and "state=3" in s.replace(" ", "")

def classify(els, foc):
    b = " ".join(els).lower()
    f = foc.lower()
    if "entsperren" in b or "notrufe" in b or "aod" in f:
        return "lock"
    if "neuer tab" in b or "web-ansicht" in b:
        return "chrome_menu"
    if "youtube-mix" in b or "alben" in b:
        return "yt_search"
    if playing() and "chrome" in f:
        return "playing"
    if "chrome" in f:
        return "chrome"
    if "miui.home" in f or "soundboks" in b:
        return "launcher"
    return "unknown"

INTENT = "am start -f 0x30000000 -a android.intent.action.VIEW -d https://www.youtube.com/results?search_query=Sido -n com.android.chrome/com.google.android.apps.chrome.Main"
fails = 0
for i in range(1, 9):
    els = list_elements() or []
    foc = focus()
    st = classify(els, foc)
    print("ZYKLUS", i, "STATE", st)
    print(" FOCUS", foc)
    print(" SICHTBAR", els[:10])
    print(" PLAYING", playing())
    if st == "playing":
        print("ERFOLG")
        raise SystemExit(0)
    if st == "lock":
        print("AKTION unlock")
        unlock()
        continue
    if st == "chrome_menu":
        print("SELFHEAL menu -> BACK")
        su("input keyevent 4")
        time.sleep(0.6)
        continue
    if st == "launcher":
        print("AKTION intent")
        su(INTENT)
        time.sleep(3)
        continue
    xml = dump_screen() or ""
    q = "ISSA" if fails >= 2 else "YOUTUBE-MIX"
    pos = find_q(xml, q)
    print("POS", q, pos, "in_list", any(q.lower() in x.lower() for x in els))
    if pos is None:
        print("SELFHEAL no bounds, try ISSA")
        pos = find_q(xml, "ISSA")
        q = "ISSA"
        fails += 1
    if pos is None:
        fails += 1
        print("SELFHEAL still none")
        continue
    print("AKTION su-tap", q, pos)
    su("input tap %d %d" % (pos[0], pos[1]))
    time.sleep(2)
    if not playing():
        fails += 1
        print("SELFHEAL tap_no_play", fails)
print("FEHLGESCHLAGEN")
