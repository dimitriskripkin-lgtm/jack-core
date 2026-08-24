#!/usr/bin/env python3
import os, re, time, json, subprocess, urllib.request

H = "/data/data/com.termux/files/home/jack"
LOG = H + "/xiaomi_web.log"
HOME = "/data/data/com.termux/files/home"
SSH = "/data/data/com.termux/files/usr/bin/ssh"
STEPS = 10

def log(msg):
    line = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")

def sh(cmd, timeout=25):
    env = os.environ.copy()
    env["HOME"] = HOME
    env["PATH"] = "/data/data/com.termux/files/usr/bin"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout, env=env)
    return r.returncode, ((r.stdout or "") + (r.stderr or "")).strip()

def su(cmd):
    rc, out = sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "su -c \'%s\'"' % (
        SSH, cmd.replace("'", "'\"'\"'")))
    return rc, out

def unlock():
    su("input keyevent 224")
    time.sleep(0.3)
    su("input keyevent 82")
    time.sleep(0.2)
    su("input swipe 540 1550 540 850 200")
    time.sleep(0.5)
    log("UNLOCK")

def dump_ui():
    su("rm -f /sdcard/screen.xml; uiautomator dump /sdcard/screen.xml")
    time.sleep(0.5)
    rc, xml = sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "cat /sdcard/screen.xml"' % SSH)
    if rc != 0 or not xml:
        return "", []
    texts = re.findall(r'text="([^"]{2,100})"', xml)
    seen, vis = set(), []
    for t in texts:
        if t in seen:
            continue
        seen.add(t)
        vis.append(t)
    return xml, vis[:35]

def find_tap(xml, label):
    m = re.search(r'text="([^"]*%s[^"]*)"' % re.escape(label), xml, re.I)
    if not m:
        return None
    idx = m.start()
    window = xml[max(0, idx - 250): idx + 350]
    bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', window)
    if not bm:
        return None
    x1, y1, x2, y2 = map(int, bm.groups())
    return (x1 + x2) // 2, (y1 + y2) // 2

def think(vis, step, history):
    system = (
        "Du bist JACK auf Dimas Xiaomi. Dima schaut zu.\n"
        "Auftrag: Ins INTERNET gehen und dich zu etwas informieren, das DICH interessiert "
        "(z.B. Android load average, Termux, autonome Agenten, MIUI, Ollama auf Handy).\n"
        "Nicht loeschen, nicht kaufen, keine Logins, keine Passwoerter.\n"
        "Antwort EXAKT 2 Zeilen:\n"
        "AKTION: OPEN_SEARCH:<kurze suchworte>|SWIPE_UP|SWIPE_DOWN|BACK|TAP:<exakter Text aus SICHTBAR>|DONE\n"
        "WARUM: <kurz was du lernen willst>\n"
        "Kein |DONE anhaengen. TAP nur Text der in SICHTBAR steht.\n"
        "Wenn noch kein Browser: OPEN_SEARCH:...\n"
        "Wenn Artikel sichtbar: scrollen oder einen Link-Text tippen."
    )
    user = "Schritt %d/%d\nSICHTBAR:\n- %s\n\nBisher:\n%s" % (
        step, STEPS,
        "\n- ".join(vis[:20]) if vis else "(leer)",
        "\n".join(history[-6:]) or "(start)")
    try:
        import sys
        sys.path.insert(0, H)
        import jack_groq_bridge as groq
        ans = groq.ask_groq(system, user, timeout=30)
        if ans and not ans.startswith("[Groq"):
            return ans
        log("Groq: %s" % (ans or "")[:80])
    except Exception as e:
        log("Groq err %s" % e)
    try:
        data = json.dumps({"model": "llama3.2:3b", "prompt": system + "\n\n" + user, "stream": False}).encode()
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=data,
                                     headers={"Content-Type": "application/json"})
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

def open_search(query):
    q = query.strip().replace(" ", "+")
    url = "https://www.google.com/search?q=" + q
    su("am start -a android.intent.action.VIEW -d '%s' -n com.android.chrome/com.google.android.apps.chrome.Main" % url)
    log("SEARCH %s" % query)

def do_action(aktion, xml, vis):
    a = aktion.strip()
    up = a.upper()
    if up.startswith("OPEN_SEARCH:"):
        open_search(a.split(":", 1)[1].strip())
        return True
    if up == "SWIPE_UP":
        su("input swipe 540 1500 540 700 280")
        return True
    if up == "SWIPE_DOWN":
        su("input swipe 540 700 540 1500 280")
        return True
    if up == "BACK":
        su("input keyevent 4")
        return True
    if up.startswith("TAP:") or a.startswith("TAP:"):
        label = a.split(":", 1)[1].strip()
        # nur wenn aehnlich sichtbar
        if not any(label.lower() in v.lower() or v.lower() in label.lower() for v in vis):
            log("TAP verweigert (nicht sichtbar): %s" % label)
            return False
        pos = find_tap(xml, label)
        if not pos:
            log("TAP miss %s" % label)
            return False
        su("input tap %d %d" % pos)
        log("TAP %s @ %s" % (label, pos))
        return True
    if up == "DONE":
        return True
    log("unbekannt: %s" % a)
    return False

def main():
    log("=== WEB EXPLORE START ===")
    unlock()
    history = []
    xml, vis = dump_ui()
    log("SICHTBAR: %s" % ", ".join(vis[:10]))
    # erster Schritt: Modell waehlt Thema, wir oeffnen Suche wenn noetig
    for step in range(1, STEPS + 1):
        ans = think(vis, step, history)
        log("DENKEN: %s" % ans.replace("\n", " | ")[:240])
        aktion, warum = parse_action(ans)
        log("SCHRITT %d: %s | %s" % (step, aktion, warum))
        if aktion.upper() == "DONE":
            break
        # Schritt 1 erzwingen ins Netz wenn Modell noch wisch/tipp ohne Suche
        if step == 1 and not aktion.upper().startswith("OPEN_SEARCH"):
            # Thema aus WARUM ableiten oder default
            q = warum if len(warum) > 8 else "Android load average high Termux"
            log("FORCE search from intent: %s" % q[:80])
            open_search(q[:80])
            history.append("1:FORCE_SEARCH")
        else:
            ok = do_action(aktion, xml, vis)
            history.append("%d:%s:%s" % (step, aktion[:40], "ok" if ok else "fail"))
        time.sleep(2.0)
        xml, vis = dump_ui()
        log("SICHTBAR: %s" % ", ".join(vis[:12]))
    log("=== WEB EXPLORE ENDE ===")
    log("SUMMARY history: %s" % " ; ".join(history))

if __name__ == "__main__":
    main()
