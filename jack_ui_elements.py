#!/usr/bin/env python3
"""Element-Agent mit hartem Ziel (AppAgent-Light)."""
import os, re, time, json, subprocess, urllib.request
import sys
sys.path.insert(0, "/data/data/com.termux/files/home/jack/ui_agent")
from capture import capture
from logger import log_transition

H = "/data/data/com.termux/files/home/jack"
LOG = H + "/ui_elements.log"
HOME = "/data/data/com.termux/files/home"
SSH = "/data/data/com.termux/files/usr/bin/ssh"
STEPS = 10
GOAL = "Ollama auf Android/Termux verstehen: seriose Seite lesen, nicht Werbung, keine Formulare"
SEARCH_Q = "Ollama Android Termux install local LLM"

BAD = (
    "advertisement", "werbung", "zustimmen und weiter", "abonnieren",
    "startseite oeffnen", "startseite öffnen", "cookie", "datenschutzhinweise",
    "spontacts", "enpal", "festpreis", "bundesland", "login", "anmelden",
)

def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def sh(cmd, timeout=20):
    env = os.environ.copy()
    env["HOME"] = HOME
    env["PATH"] = "/data/data/com.termux/files/usr/bin"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()

def su(cmd):
    return sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "su -c \'%s\'"' % (
        SSH, cmd.replace("'", "'\"'\"'")))

def unlock():
    su("input keyevent 224")
    time.sleep(0.2)
    su("input keyevent 82")
    time.sleep(0.15)
    su("input swipe 540 1500 540 1000 160")
    time.sleep(0.4)
    log("UNLOCK")

def dump_xml():
    su("rm -f /sdcard/screen.xml; uiautomator dump /sdcard/screen.xml")
    time.sleep(0.45)
    rc, xml = sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "cat /sdcard/screen.xml"' % SSH)
    return xml if rc == 0 else ""

def parse_elements(xml):
    els = []
    for m in re.finditer(r"<node [^>]+>", xml or ""):
        tag = m.group(0)
        clickable = 'clickable="true"' in tag
        text = ""
        dm = re.search(r'text="([^"]*)"', tag)
        if dm:
            text = dm.group(1).strip()
        cm = re.search(r'content-desc="([^"]*)"', tag)
        desc = cm.group(1).strip() if cm else ""
        label = text or desc
        if not label or len(label) < 2:
            continue
        label = label.replace("&#10;", " ")[:55]
        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', tag)
        if not bm:
            continue
        x1, y1, x2, y2 = map(int, bm.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if cx < 30 or cy < 70:
            continue
        w, h = x2 - x1, y2 - y1
        if not clickable and (w < 40 or h < 28):
            continue
        els.append({"label": label, "x": cx, "y": cy, "clickable": clickable})
    out, seen = [], set()
    for e in els:
        key = (e["label"][:30], e["x"] // 50, e["y"] // 50)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
        if len(out) >= 22:
            break
    return out

def focus():
    st = capture()
    return "%s/%s" % (st.get("package", "?"), st.get("activity", "?"))
def is_bad_label(label):
    low = label.lower()
    return any(b in low for b in BAD)

def open_search(q):
    url = "https://www.google.com/search?q=" + q.replace(" ", "+")
    su("am start -a android.intent.action.VIEW -d %s -n com.android.chrome/com.google.android.apps.chrome.Main" % repr(url))
    log("SEARCH %s" % q)

def think(elements, step, history, foc):
    lines = []
    for i, e in enumerate(elements, 1):
        mark = " [BAD]" if is_bad_label(e["label"]) else ""
        lines.append("%d) %s%s" % (i, e["label"], mark))
    system = (
        "Du bist JACK auf Dimas Xiaomi. Er schaut zu.\n"
        "ZIEL (nie vergessen): %s\n"
        "Regeln: Keine Werbung, keine Formulare, kein Login. "
        "Elemente mit [BAD] nicht tippen — lieber SWIPE_UP, BACK oder OPEN_SEARCH.\n"
        "Antwort EXAKT 2 Zeilen:\n"
        "AKTION: TAP:<nummer>|SWIPE_UP|SWIPE_DOWN|BACK|HOME|OPEN_SEARCH:<worte>|DONE\n"
        "WARUM: <bezogen auf ZIEL>\n"
        "TAP nur Nummer ohne [BAD]. DONE nur wenn du zum Thema gelesen hast."
    ) % GOAL
    user = "Schritt %d/%d\nFOCUS: %s\nELEMENTE:\n%s\n\nBisher:\n%s" % (
        step, STEPS, foc,
        "\n".join(lines) if lines else "(leer)",
        "\n".join(history[-6:]) or "(start)")
    try:
        import sys
        sys.path.insert(0, H)
        import jack_groq_bridge as groq
        ans = groq.ask_groq(system, user, timeout=28)
        if ans and not ans.startswith("[Groq"):
            return ans
        log("Groq: %s" % (ans or "")[:70])
    except Exception as e:
        log("Groq err %s" % e)
    try:
        data = json.dumps({
            "model": "llama3.2:3b",
            "prompt": system + "\n\n" + user,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read()).get("response", "")
    except Exception as e:
        return "AKTION: DONE\nWARUM: kein modell (%s)" % e

def parse_action(ans):
    aktion, warum = "DONE", "?"
    for line in (ans or "").splitlines():
        line = line.strip()
        if line.upper().startswith("AKTION:"):
            aktion = line.split(":", 1)[1].strip().split("|")[0].strip()
        if line.upper().startswith("WARUM:"):
            warum = line.split(":", 1)[1].strip()
    return aktion, warum

def do_action(aktion, elements):
    up = aktion.upper().strip()
    before = capture()
    before_h = before.get("hash", "unknown")
    ok = False
    target = aktion

    if up.startswith("OPEN_SEARCH:"):
        open_search(aktion.split(":", 1)[1].strip())
        ok = True
        target = "OPEN_SEARCH"
    elif up.startswith("TAP:"):
        raw = up.split(":", 1)[1].strip()
        try:
            i = int(re.sub(r"[^0-9]", "", raw))
        except ValueError:
            log("TAP bad %s" % raw)
            return False
        if i < 1 or i > len(elements):
            log("TAP range %d" % i)
            return False
        e = elements[i - 1]
        if is_bad_label(e["label"]):
            log("TAP block BAD: %s" % e["label"])
            return False
        su("input tap %d %d" % (e["x"], e["y"]))
        log("TAP #%d %s @(%d,%d)" % (i, e["label"], e["x"], e["y"]))
        ok = True
        target = e["label"][:60]
    elif up == "SWIPE_UP":
        su("input swipe 540 1300 540 800 180")
        ok = True
        target = "SWIPE_UP"
    elif up == "SWIPE_DOWN":
        su("input swipe 540 800 540 1300 180")
        ok = True
        target = "SWIPE_DOWN"
    elif up == "BACK":
        su("input keyevent 4")
        ok = True
        target = "BACK"
    elif up == "HOME":
        su("input keyevent 3")
        ok = True
        target = "HOME"
    elif up == "DONE":
        return True
    else:
        log("unbekannt %s" % aktion)
        return False

    time.sleep(1.2)
    after = capture()
    after_h = after.get("hash", "unknown")
    success = ok and (after_h != before_h)
    log_transition(before_h, up.split(":")[0], target, after_h, success)
    return ok
    if up == "SWIPE_UP":
        su("input swipe 540 1300 540 800 180")
        return True
    if up == "SWIPE_DOWN":
        su("input swipe 540 800 540 1300 180")
        return True
    if up == "BACK":
        su("input keyevent 4")
        return True
    if up == "HOME":
        su("input keyevent 3")
        return True
    if up == "DONE":
        return True
    log("unbekannt %s" % aktion)
    return False

def drifted(foc, els):
    blob = (foc + " " + " ".join(e["label"] for e in els)).lower()
    if any(x in blob for x in ("spontacts", "enpal", "bremen chat", "solaranlage")):
        return True
    return False

def main():
    log("=== UI GOAL AGENT ===")
    log("GOAL: %s" % GOAL)
    unlock()
    history = []
    open_search(SEARCH_Q)
    history.append("0:SEARCH:" + SEARCH_Q)
    time.sleep(2.8)

    for step in range(1, STEPS + 1):
        st = capture()
        foc = "%s/%s" % (st.get("package","?"), st.get("activity","?"))
        els = st.get("elements", [])
        if not els:
            time.sleep(1.0)
            st = capture()
            foc = "%s/%s" % (st.get("package","?"), st.get("activity","?"))
            els = st.get("elements", [])
            log("RETRY els=%d" % len(els))
        if not els:
            log("LEER -> BACK")
            su("input keyevent 4")
            history.append("%d:FORCE_BACK" % step)
            time.sleep(1.2)
            continue
        if drifted(foc, els):
            log("DRIFT -> BACK + SEARCH")
            su("input keyevent 4")
            time.sleep(0.6)
            open_search(SEARCH_Q)
            history.append("%d:DRIFT_RECOVER" % step)
            time.sleep(2.0)
            continue

        log("FOCUS %s" % foc)
        log("ELEMENTE: %s" % " | ".join("%d:%s" % (i + 1, e["label"][:28]) for i, e in enumerate(els[:10])))
        ans = think(els, step, history, foc)
        log("DENKEN: %s" % ans.replace("\n", " | ")[:230])
        aktion, warum = parse_action(ans)
        log("SCHRITT %d: %s | %s" % (step, aktion, warum))
        if aktion.upper() == "DONE":
            log("DONE")
            break
        ok = do_action(aktion, els)
        history.append("%d:%s:%s" % (step, aktion[:36], "ok" if ok else "fail"))

        # Intelligenz-Schutz: 3x gleicher Screen + nur Swipe → abbrechen
        recent = [h for h in history[-4:] if "SWIPE" in h]
        if len(recent) >= 3:
            log("SCHUTZ: 3x hintereinander nur Swipe → DONE (kein Fortschritt)")
            break

        time.sleep(2.0)
    log("=== ENDE ===")

if __name__ == "__main__":
    main()
