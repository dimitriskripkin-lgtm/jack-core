#!/usr/bin/env python3
import os, re, time, json, subprocess, urllib.request

H = "/data/data/com.termux/files/home/jack"
LOG = H + "/xiaomi_think.log"
HOME = "/data/data/com.termux/files/home"
SSH = "/data/data/com.termux/files/usr/bin/ssh"
STEPS = 12

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
    full = '%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack su -c %s' % (
        SSH, repr(cmd))
    # repr adds quotes; safer: pass via ssh remote
    rc, out = sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "su -c \'%s\'"' % (
        SSH, cmd.replace("'", "'\"'\"'")))
    return rc, out

def unlock():
    su("input keyevent 224")
    time.sleep(0.3)
    su("input keyevent 82")
    time.sleep(0.2)
    su("input swipe 540 1550 540 850 200")
    time.sleep(0.6)
    log("UNLOCK done")

def dump_ui():
    su("rm -f /sdcard/screen.xml; uiautomator dump /sdcard/screen.xml")
    time.sleep(0.4)
    rc, xml = sh('%s -o BatchMode=yes -o ConnectTimeout=8 xiaomi-jack "cat /sdcard/screen.xml"' % SSH)
    if rc != 0 or not xml:
        return "", []
    texts = re.findall(r'text="([^"]{2,80})"', xml)
    # unique, keep order
    seen = set()
    vis = []
    for t in texts:
        if t in seen:
            continue
        if t.strip().isdigit() and len(t) < 3:
            continue
        seen.add(t)
        vis.append(t)
    return xml, vis[:40]

def find_tap(xml, label):
    # node containing text, then bounds
    idx = xml.lower().find('text="%s"' % label.lower())
    if idx < 0:
        # partial
        m = re.search(r'text="([^"]*%s[^"]*)"' % re.escape(label), xml, re.I)
        if not m:
            return None
        idx = m.start()
        label = m.group(1)
    # search bounds near this text (same node often has bounds before or after)
    window = xml[max(0, idx - 200): idx + 200]
    bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', window)
    if not bm:
        # try full node forward
        window = xml[idx: idx + 400]
        bm = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', window)
    if not bm:
        return None
    x1, y1, x2, y2 = map(int, bm.groups())
    return (x1 + x2) // 2, (y1 + y2) // 2

def think(vis, step, history):
    system = (
        "Du bist JACK. Du steuerst Dimas Xiaomi. Er schaut zu. "
        "Ziel: neugierig und sinnvoll UI erkunden (Einstellungen, ggf. Chrome). "
        "Nicht loeschen, nicht reset, nicht bezahlen, keine Passwoerter. "
        "Antworte EXAKT in 2 Zeilen:\n"
        "AKTION: HOME|BACK|SWIPE_UP|SWIPE_DOWN|OPEN_SETTINGS|OPEN_CHROME|TAP:<exakter Text aus SICHTBAR>|DONE\n"
        "WARUM: <ein kurzer Satz>\n"
        "TAP nur mit Text der in SICHTBAR vorkommt."
    )
    user = "Schritt %d/%d\nSICHTBAR:\n- %s\n\nBisher:\n%s\n\nWas ist der naechste sinnvolle Schritt?" % (
        step, STEPS, "\n- ".join(vis[:25]) if vis else "(leer)",
        "\n".join(history[-5:]) or "(nichts)")
    # Groq zuerst
    try:
        import sys
        sys.path.insert(0, H)
        import jack_groq_bridge as groq
        ans = groq.ask_groq(system, user, timeout=25)
        if ans and not ans.startswith("[Groq"):
            return ans
        log("Groq fail: %s" % ans[:80])
    except Exception as e:
        log("Groq import/call: %s" % e)
    # Ollama Fallback
    try:
        prompt = system + "\n\n" + user
        data = json.dumps({"model": "llama3.2:3b", "prompt": prompt, "stream": False}).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:11434/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read()).get("response", "")
    except Exception as e:
        return "AKTION: DONE\nWARUM: kein Modell erreichbar (%s)" % e

def parse_action(ans):
    aktion, warum = "DONE", "parse fail"
    for line in (ans or "").splitlines():
        line = line.strip()
        if line.upper().startswith("AKTION:"):
            aktion = line.split(":", 1)[1].strip()
            aktion = aktion.split("|")[0].strip()
            if " " in aktion and not aktion.upper().startswith("TAP:"):
                aktion = aktion.split()[0].strip()
        if line.upper().startswith("WARUM:"):
            warum = line.split(":", 1)[1].strip()
    return aktion, warum

def do_action(aktion, xml):
    a = aktion.strip()
    up = a.upper()
    if up == "HOME":
        su("input keyevent 3")
        return True
    if up == "BACK":
        su("input keyevent 4")
        return True
    if up == "SWIPE_UP":
        su("input swipe 540 1400 540 600 250")
        return True
    if up == "SWIPE_DOWN":
        su("input swipe 540 600 540 1400 250")
        return True
    if up == "OPEN_SETTINGS":
        su("am start -a android.settings.SETTINGS")
        return True
    if up == "OPEN_CHROME":
        su("am start -a android.intent.action.VIEW -d 'https://de.wikipedia.org/wiki/Last_(Physik)' -n com.android.chrome/com.google.android.apps.chrome.Main")
        return True
    if up.startswith("TAP:") or a.startswith("TAP:"):
        label = a.split(":", 1)[1].strip().split("|")[0].strip()
        pos = find_tap(xml, label)
        if not pos:
            log("TAP miss: %s" % label)
            return False
        su("input tap %d %d" % pos)
        log("TAP %s @ %s" % (label, pos))
        return True
    if up == "DONE":
        return True
    log("unbekannte AKTION: %s" % a)
    return False

def main():
    os.chdir(H)
    log("=== XIAOMI THINK START steps=%d ===" % STEPS)
    unlock()
    history = []
    xml, vis = dump_ui()
    log("SICHTBAR: %s" % ", ".join(vis[:12]))
    for step in range(1, STEPS + 1):
        ans = think(vis, step, history)
        log("DENKEN: %s" % ans.replace("\n", " | ")[:220])
        aktion, warum = parse_action(ans)
        log("SCHRITT %d: %s | %s" % (step, aktion, warum))
        if aktion.upper() == "DONE":
            log("DONE vom Modell")
            break
        ok = do_action(aktion, xml)
        history.append("%d:%s -> %s" % (step, aktion, "ok" if ok else "fail"))
        time.sleep(1.2)
        xml, vis = dump_ui()
        log("SICHTBAR: %s" % ", ".join(vis[:12]))
    log("=== XIAOMI THINK ENDE ===")

if __name__ == "__main__":
    main()
