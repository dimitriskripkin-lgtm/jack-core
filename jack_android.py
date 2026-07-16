#!/usr/bin/env python3
"""
jack_android.py - JACK 2 Android Control Module
Laeuft auf: Xiaomi 11T Pro (Node Alpha)
Pipeline: Intent -> Focus-Check -> XML -> SoM -> Gemini -> Ausfuehren
"""

import subprocess, os, io, hashlib, json, time, datetime
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    from PIL import Image, ImageDraw
    PILLOW_OK = True
except ImportError:
    PILLOW_OK = False

# Konfiguration
DISPLAY_W = 1080
DISPLAY_H = 2400
SCREENSHOT_DIR = os.path.expanduser("~/jack/screenshots")
SCREENSHOT_QUALITY = 65
SCREENSHOT_MAX_WIDTH = 720
_LAST_HASH = None


# ─── HILFSFUNKTIONEN ─────────────────────────────────────────────────────────

def _sh(cmd, root=False, timeout=10):
    if root:
        cmd = f'su -c "{cmd}"'
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", "TIMEOUT", 1
    except Exception as e:
        return "", str(e), 1

def _sec(key):
    try:
        with open(os.path.expanduser("~/.jack_secrets")) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    if k.strip() == key:
                        return v.strip().strip('"').strip("'") 
    except Exception:
        pass
    return ""

def toast(msg):
    """Visuelles Feedback auf Xiaomi-Display."""
    _sh(f"termux-toast -g middle -s '{str(msg)[:80]}'")



def _adb(cmd):
    import subprocess
    r = subprocess.run(f'adb -s 127.0.0.1:5555 shell {cmd}',
                      shell=True, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip(), r.returncode

def adb_setup():
    import subprocess, time
    _sh('setprop service.adb.tcp.port 5555', root=True)
    _sh('stop adbd && start adbd', root=True)
    time.sleep(2)
    subprocess.run('adb connect 127.0.0.1:5555', shell=True, capture_output=True)

# ─── ANDROID SYSTEM ───────────────────────────────────────────────────────────

def get_display_size():
    out, _, _ = _sh("wm size", root=True)
    try:
        size = out.split(":")[-1].strip()
        w, h = size.split("x")
        return int(w), int(h)
    except Exception:
        return DISPLAY_W, DISPLAY_H

def get_current_focus():
    out, _, _ = _sh("dumpsys window windows | grep -E 'mCurrentFocus|mFocusedApp'", root=True)
    return out.strip()

def clear_popups(max_tries=5):
    """System-Popups und Dialoge wegdruecken."""
    for _ in range(max_tries):
        focus = get_current_focus()
        if any(x in focus for x in ["PopupWindow", "Dialog", "Alert", "Permission"]):
            toast("JACK: Popup erkannt -> Zurueck")
            _sh("input keyevent 4", root=True)
            time.sleep(0.5)
        else:
            return True
    return False

def launch_app(package, activity=None):
    """App per Intent starten (Teleportation - kein UI-Klicken)."""
    if activity:
        cmd = f"am start -n {package}/{activity}"
    else:
        cmd = f"monkey -p {package} -c android.intent.category.LAUNCHER 1"
    _, _, code = _sh(cmd, root=True)
    time.sleep(1.5)
    toast(f"JACK: Starte {package.split('.')[-1]}")
    return code == 0

def tap(x, y):
    toast(f"JACK: Tippe {x},{y}")
    _adb(f"input tap {x} {y}")
    time.sleep(0.3)

def swipe(x1, y1, x2, y2, ms=300):
    _adb(f"input swipe {x1} {y1} {x2} {y2} {ms}")
    time.sleep(0.5)

def type_text(text):
    safe = text.replace("'", "").replace('"', "").replace(" ", "%s")
    _adb(f"input text '{safe}'")

def keyevent(code):
    _adb(f"input keyevent {code}")


# ─── UI BAUM ──────────────────────────────────────────────────────────────────

def get_ui_tree():
    """uiautomator XML dump -> geparste Element-Liste."""
    out = ""
    code = 1  # MIUI: kein stdout, immer via Datei
    if code != 0 or "<hierarchy" not in out:
        _sh("pkill -9 uiautomator", root=True)
        import time
        time.sleep(1.5)
        _sh("uiautomator dump /sdcard/jack_ui.xml", root=True)
        out, _, _ = _sh("cat /sdcard/jack_ui.xml", root=True)
    if not out or "<hierarchy" not in out:
        return []
    try:
        root_el = ET.fromstring(out)
        elements = []
        idx = 0
        for node in root_el.iter("node"):
            text = node.get("text", "")
            desc = node.get("content-desc", "")
            cls = node.get("class", "")
            clickable = node.get("clickable", "false") == "true"
            bounds_str = node.get("bounds", "")
            try:
                parts = bounds_str.replace("][", ",").replace("[","").replace("]","")
                x1, y1, x2, y2 = map(int, parts.split(","))
                cx, cy = (x1+x2)//2, (y1+y2)//2
            except Exception:
                continue
            if (text or desc) and (x2-x1) > 5 and (y2-y1) > 5:
                elements.append({
                    "id": idx, "text": text, "desc": desc, "class": cls,
                    "clickable": clickable, "bounds": (x1,y1,x2,y2), "center": (cx,cy)
                })
                idx += 1
        return elements
    except ET.ParseError:
        return []

def find_element(elements, text=None, desc=None, cls=None):
    for el in elements:
        if text and text.lower() in el["text"].lower(): return el
        if desc and desc.lower() in el["desc"].lower(): return el
        if cls and cls in el["class"]: return el
    return None

def xml_state_diff(tree1, tree2):
    """True wenn UI sich signifikant geaendert hat."""
    if not tree1 or not tree2:
        return True
    return set(e["text"] for e in tree1) != set(e["text"] for e in tree2)

def wait_for_ui_change(prev_tree, timeout=8, interval=0.5):
    time.sleep(5)
    return get_ui_tree()


# ─── SCREENSHOT + SOM ─────────────────────────────────────────────────────────

def screenshot_to_ram():
    """Screenshot direkt in RAM - kein Flash-Schreiben."""
    if not PILLOW_OK:
        return None
    try:
        result = subprocess.run(
            ["su", "-c", "screencap -p"],
            capture_output=True, timeout=8
        )
        if result.returncode != 0 or not result.stdout:
            return None
        return Image.open(io.BytesIO(result.stdout))
    except Exception:
        return None

def compress_image(img):
    """720px Breite, JPEG 65% -> ~80-120KB."""
    w, h = img.size
    if w > SCREENSHOT_MAX_WIDTH:
        ratio = SCREENSHOT_MAX_WIDTH / w
        img = img.resize((SCREENSHOT_MAX_WIDTH, int(h*ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=SCREENSHOT_QUALITY)
    return buf.getvalue()

def add_som_markers(img, elements):
    """Set-of-Mark: Nummerierte rote Boxen ueber klickbare Elemente."""
    if not PILLOW_OK:
        return img
    annotated = img.copy()
    draw = ImageDraw.Draw(annotated, "RGBA")
    w_img, h_img = img.size
    scale_x = w_img / DISPLAY_W
    scale_y = h_img / DISPLAY_H
    for el in elements:
        pass  # clickable nicht filtern - MIUI setzt clickable oft falsch
        x1, y1, x2, y2 = el["bounds"]
        bx1,by1 = int(x1*scale_x), int(y1*scale_y)
        bx2,by2 = int(x2*scale_x), int(y2*scale_y)
        draw.rectangle([bx1,by1,bx2,by2], outline=(255,0,0,200), width=2)
        draw.rectangle([bx1,by1,bx1+20,by1+18], fill=(255,0,0,200))
        draw.text((bx1+2, by1+1), str(el["id"]), fill=(255,255,255))
    return annotated

def image_hash(img_bytes):
    return hashlib.md5(img_bytes).hexdigest()

def save_screenshot(img_bytes, label=""):
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    name = f"{ts}_{label}.jpg" if label else f"{ts}.jpg"
    path = os.path.join(SCREENSHOT_DIR, name)
    with open(path, "wb") as f:
        f.write(img_bytes)
    return path

def cleanup_screenshots(days=14):
    if not os.path.exists(SCREENSHOT_DIR):
        return 0
    cutoff = time.time() - (days * 86400)
    count = 0
    for f in os.listdir(SCREENSHOT_DIR):
        path = os.path.join(SCREENSHOT_DIR, f)
        if os.path.getmtime(path) < cutoff:
            os.remove(path)
            count += 1
    return count


# ─── GEMINI VISION ────────────────────────────────────────────────────────────

def analyze_screen(goal, elements=None, img=None):
    """
    SoM-annotierter Screenshot -> Gemini Flash-Lite -> Action-Dict.
    Gibt zurueck: {"action": "tap", "id": 5} o.ae.
    """
    import base64, urllib.request
    global _LAST_HASH

    if img is None:
        img = screenshot_to_ram()
    if img is None:
        return {"action": "error", "reason": "Screenshot fehlgeschlagen"}

    if elements:
        img = add_som_markers(img, elements)

    img_bytes = compress_image(img)

    h = image_hash(img_bytes)
    if h == _LAST_HASH:
        return {"action": "skip", "reason": "Screen unveraendert"}
    _LAST_HASH = h

    save_screenshot(img_bytes)

    api_key = _sec("GEMINI_API_KEY")
    if not api_key:
        return {"action": "error", "reason": "Kein GEMINI_API_KEY in ~/.jack_secrets"}

    el_context = ""
    if elements:
        clickable = [e for e in elements if e["clickable"]]
        lines = [f"ID {e['id']}: {(e['text'] or e['desc'])[:40]}" for e in clickable[:25]]
        el_context = "\nKlickbare Elemente:\n" + "\n".join(lines)

    prompt = (
        f"Du steuerst ein Android-Geraet. Aufgabe: {goal}\n"
        f"Klickbare Elemente sind mit roten Boxen und IDs markiert.{el_context}\n"
        "Antworte NUR mit einem JSON-Objekt (kein Markdown, keine Erklaerung):\n"
        '{"action":"tap","id":5} oder\n'
        '{"action":"swipe","dir":"up"} oder\n'
        '{"action":"text","value":"eingabe"} oder\n'
        '{"action":"keyevent","code":4} oder\n'
        '{"action":"done","result":"beschreibung"} oder\n'
        '{"action":"error","reason":"beschreibung"}'
    )

    payload = json.dumps({
        "contents": [{"parts": [
            {"text": prompt},
            {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(img_bytes).decode()}}
        ]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 128}
    }).encode()

    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"models/gemini-2.5-flash-lite:generateContent?key={api_key}")
    try:
        for versuch in range(3):
            try:
                import time
                req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read())
                text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                text = text.replace('```json','').replace('```','').strip()
                return json.loads(text)
            except Exception as e:
                if versuch < 2:
                    time.sleep(2 ** versuch)
                else:
                    return {'action':'error','reason':str(e)[:200]}
    except Exception as e:
        return {"action": "error", "reason": str(e)[:200]}


# ─── AUSFUEHREN ───────────────────────────────────────────────────────────────

def execute_action(action_dict, elements):
    """Gemini-Antwort in echte Aktion umsetzen. Gibt (done, msg) zurueck."""
    action = action_dict.get("action", "error")

    if action == "tap":
        el_id = action_dict.get("id")
        el = next((e for e in elements if e["id"] == el_id), None)
        if el:
            toast(f"JACK: Tippe ID {el_id} - {el['text'][:20]}")
            tap(*el["center"])
        else:
            return False, f"Element ID {el_id} nicht gefunden"

    elif action == "swipe":
        d = action_dict.get("dir", "up")
        cx = DISPLAY_W // 2
        dirs = {"up":(cx,1600,cx,600),"down":(cx,600,cx,1600),
                "left":(900,1200,180,1200),"right":(180,1200,900,1200)}
        if d in dirs:
            toast(f"JACK: Wische {d}")
            swipe(*dirs[d])

    elif action == "text":
        toast("JACK: Tippe Text")
        type_text(action_dict.get("value", ""))

    elif action == "keyevent":
        keyevent(action_dict.get("code", 4))

    elif action == "done":
        msg = action_dict.get("result", "Aufgabe erledigt")
        toast(f"JACK: Fertig - {msg[:40]}")
        return True, msg

    elif action == "skip":
        return None, "Screen unveraendert"

    elif action == "error":
        return False, action_dict.get("reason", "Unbekannter Fehler")

    return None, None  # Weiter



def find_element_smart(elements, goal):
    """Lokale Suche im XML bevor Gemini gerufen wird.
    Gibt Element zurueck wenn Treffer, sonst None."""
    import re
    keywords = [w.lower() for w in re.split(r"[ ,.-]+", goal) if len(w) > 2]
    best, best_score = None, 0
    for el in elements:
        pass  # clickable nicht filtern - MIUI setzt clickable oft falsch
        haystack = (el["text"] + " " + el["desc"]).lower()
        score = sum(1 for kw in keywords if kw in haystack)
        if score > best_score:
            best, best_score = el, score
    if best_score >= 1:
        return best
    return None

# ─── HAUPTSCHLEIFE ────────────────────────────────────────────────────────────

def run(goal, app_package=None, app_activity=None, max_rounds=10):
    """
    JACK fuehrt ein Ziel autonom aus.
    Beispiel: run("Oeffne WhatsApp und lies letzte Nachricht",
                  app_package="com.whatsapp")
    """
    adb_setup()
    toast(f"JACK: {goal[:50]}")

    if app_package:
        launch_app(app_package, app_activity)

    clear_popups()

    prev_tree = None
    for rnd in range(max_rounds):
        toast(f"JACK: Runde {rnd+1}/{max_rounds}")

        focus = get_current_focus()
        if any(x in focus for x in ["Dialog","Popup","Permission"]):
            clear_popups()

        elements = get_ui_tree()

        if prev_tree and not xml_state_diff(prev_tree, elements):
            time.sleep(0.8)
            elements = get_ui_tree()

        # Erst lokal suchen - kein API-Call wenn Treffer
        local_hit = find_element_smart(elements, goal)
        if local_hit:
            toast(f"JACK: Lokal gefunden - {local_hit['text'][:25]}")
            tap(*local_hit["center"])
            prev_tree = elements
            wait_for_ui_change(elements, timeout=5)
            elements = get_ui_tree()
            # Pruefen ob Ziel erreicht
            result = analyze_screen(f"Wurde das Ziel erreicht? Ziel war: {goal}", elements)
            done, msg = execute_action(result, elements)
            if done is True:
                cleanup_screenshots()
                return True, msg
            continue

        result = analyze_screen(goal, elements)
        done, msg = execute_action(result, elements)

        if done is True:
            cleanup_screenshots()
            return True, msg
        if done is False:
            return False, msg

        prev_tree = elements
        wait_for_ui_change(elements, timeout=6)

    return False, f"Max Runden ({max_rounds}) erreicht"


# ─── SCHNELLTEST ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        goal = " ".join(sys.argv[1:])
        ok, msg = run(goal)
        print("OK:" if ok else "FAIL:", msg)
    else:
        print("=== jack_android.py Schnelltest ===")
        print("Display:", get_display_size())
        print("Focus:", get_current_focus())
        els = get_ui_tree()
        print(f"UI-Elemente: {len(els)}")
        if els:
            print("Erstes Element:", els[0])
        cleanup_screenshots()
        print("Cleanup: OK")
