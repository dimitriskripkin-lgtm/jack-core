#!/usr/bin/env python3
"""Direkt Doku oeffnen, scrollen, Elemente tippen. Kein Google-Drift."""
import os, re, time, json, subprocess, urllib.request

H = "/data/data/com.termux/files/home/jack"
LOG = H + "/ui_read.log"
HOME = "/data/data/com.termux/files/home"
SSH = "/data/data/com.termux/files/usr/bin/ssh"
STEPS = 20
# bekannte, textreiche Seiten
URL = "https://raw.githubusercontent.com/ollama/ollama/main/README.md"
GOAL = "Ollama README (Rohtext) lesen, scrollen, Inhalt verstehen"

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
    su("input keyevent 224"); time.sleep(0.2)
    su("input keyevent 82"); time.sleep(0.15)
    su("input swipe 540 1500 540 1000 160"); time.sleep(0.4)

def open_url(url):
    su("am start -a android.intent.action.VIEW -d %s -n com.android.chrome/com.google.android.apps.chrome.Main" % repr(url))
    log("OPEN %s" % url)

def dump_xml():
    su("rm -f /sdcard/screen.xml; uiautomator dump /sdcard/screen.xml")
    time.sleep(0.5)
    rc, xml = sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "cat /sdcard/screen.xml"' % SSH)
    return xml if rc == 0 else ""

def parse_elements(xml):
    els = []
    for m in re.finditer(r"<node [^>]+>", xml or ""):
        tag = m.group(0)
        dm = re.search(r'text="([^"]*)"', tag)
        cm = re.search(r'content-desc="([^"]*)"', tag)
        label = ((dm.group(1) if dm else "") or (cm.group(1) if cm else "")).strip()
        if len(label) < 2:
            continue
        label = label.replace("&#10;", " ")[:50]
        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', tag)
        if not bm:
            continue
        x1, y1, x2, y2 = map(int, bm.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        if cy < 80 or cx < 20:
            continue
        els.append({"label": label, "x": cx, "y": cy})
    out, seen = [], set()
    for e in els:
        k = (e["label"][:25], e["y"] // 40)
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
        if len(out) >= 18:
            break
    return out

def think(els, step, history):
    lines = ["%d) %s" % (i + 1, e["label"]) for i, e in enumerate(els)]
    system = (
        "Du bist JACK. Ziel: %s\n"
        "Du bist auf GitHub Ollama. Scrollen (SWIPE_UP) zum Lesen ist gut. "
        "Keine Logins, keine Stars noetig. Cookie/Zustimmen nur wenn noetig.\n"
        "Antwort 2 Zeilen:\nAKTION: TAP:<nr>|SWIPE_UP|SWIPE_DOWN|BACK|DONE\nWARUM: ..."
    ) % GOAL
    user = "Schritt %d\nELEMENTE:\n%s\nBisher:\n%s" % (
        step, "\n".join(lines) or "(leer)", "\n".join(history[-5:]) or "-")
    try:
        import sys
        sys.path.insert(0, H)
        import jack_groq_bridge as groq
        ans = groq.ask_groq(system, user, timeout=25)
        if ans and not ans.startswith("[Groq"):
            return ans
    except Exception as e:
        log("Groq %s" % e)
    try:
        data = json.dumps({"model": "llama3.2:3b", "prompt": system + "\n" + user, "stream": False}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read()).get("response", "")
    except Exception as e:
        return "AKTION: SWIPE_UP\nWARUM: fallback %s" % e

def parse_action(ans):
    aktion, warum = "SWIPE_UP", "?"
    for line in (ans or "").splitlines():
        s = line.strip()
        if s.upper().startswith("AKTION:"):
            aktion = s.split(":", 1)[1].strip().split("|")[0].strip()
        elif s.upper().startswith("WARUM:"):
            warum = s.split(":", 1)[1].strip()
        elif s.upper() in ("SWIPE_UP", "SWIPE_DOWN", "BACK", "DONE") or s.upper().startswith("TAP:"):
            aktion = s.split("|")[0].strip()
    return aktion, warum

def do_action(aktion, els):
    up = aktion.upper()
    if up.startswith("TAP:"):
        try:
            i = int(re.sub(r"\D", "", up.split(":", 1)[1]))
        except ValueError:
            return False
        if i < 1 or i > len(els):
            return False
        e = els[i - 1]
        low = e["label"].lower()
        if any(x in low for x in ("anmelden", "sign in", "login", "star")):
            log("skip %s" % e["label"])
            return False
        su("input tap %d %d" % (e["x"], e["y"]))
        log("TAP #%d %s" % (i, e["label"]))
        return True
    if up == "SWIPE_UP":
        su("input swipe 540 1400 540 700 200"); return True
    if up == "SWIPE_DOWN":
        su("input swipe 540 700 540 1400 200"); return True
    if up == "BACK":
        su("input keyevent 4"); return True
    return up == "DONE"

def main():
    log("=== READ %s ===" % URL)
    unlock()
    open_url(URL)
    time.sleep(3.5)
    history = []
    for step in range(1, STEPS + 1):
        els = parse_elements(dump_xml())
        if not els:
            time.sleep(1.2)
            els = parse_elements(dump_xml())
        log("ELEMENTE: %s" % " | ".join("%d:%s" % (i + 1, e["label"][:24]) for i, e in enumerate(els[:8])))
        ans = think(els, step, history)
        log("DENKEN: %s" % ans.replace("\n", " | ")[:200])
        aktion, warum = parse_action(ans)
        log("SCHRITT %d: %s | %s" % (step, aktion, warum))
        if aktion.upper() == "DONE":
            break
        do_action(aktion, els)
        history.append("%d:%s" % (step, aktion))
        time.sleep(1.8)
    log("=== ENDE ===")

if __name__ == "__main__":
    main()
