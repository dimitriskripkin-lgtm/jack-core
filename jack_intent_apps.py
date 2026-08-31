"""App-Starts ohne LLM - verifizierte Map aus pm list packages (Qwen 21.08.)
Alle Pakete live vom Xiaomi 11T Pro abgefragt."""
import re, json

MAP = dict(p.split(":") for p in """
einstellungen:com.android.settings|settings:com.android.settings|
chrome:com.android.chrome|browser:com.android.chrome|
firefox:org.mozilla.firefox|
kamera:com.android.camera|camera:com.android.camera|
foto:com.miui.gallery|fotos:com.miui.gallery|galerie:com.miui.gallery|gallery:com.miui.gallery|photos:com.miui.gallery|
rechner:com.miui.calculator|calculator:com.miui.calculator|
uhr:com.android.deskclock|clock:com.android.deskclock|
kontakte:com.google.android.contacts|contacts:com.google.android.contacts|
telefon:com.google.android.dialer|phone:com.google.android.dialer|anrufen:com.google.android.dialer|
dateien:com.google.android.apps.nbu.files|files:com.google.android.apps.nbu.files|
musik:com.miui.player|music:com.miui.player|
youtube:com.google.android.youtube|
gmail:com.google.android.gm|mail:com.google.android.gm|email:com.google.android.gm|
maps:com.google.android.apps.maps|karten:com.google.android.apps.maps|google maps:com.google.android.apps.maps|googlemaps:com.google.android.apps.maps|
whatsapp:com.whatsapp|
telegram:org.telegram.messenger|telegramm:org.telegram.messenger|
spotify:com.spotify.music|
netflix:com.netflix.mediaclient|
instagram:com.instagram.android|
tiktok:com.zhiliaoapp.musically|
vlc:org.videolan.vlc|
soundcloud:com.soundcloud.android|
xing:com.xing.android|
assistant:com.google.android.apps.googleassistant|google:com.google.android.apps.googleassistant
""".strip().replace("\n","").split("|") if ":" in p)


def _live_pkgs():
    try:
        d=json.load(open("/data/data/com.termux/files/home/jack/jack_apps_live.json",encoding="utf-8"))
        return set(d.get("pkgs") or [])
    except Exception:
        return set()

def try_app_launch(text, PENDING_EXEC, send_keyboard):
    m = re.search(r"(?:öffne|starte|eröffne|mache? auf)\s+(?:die\s+|den\s+|das\s+)?([a-zA-Z0-9äöüß\s]+?)(?:\s+auf\s+de[mn]|\s+und|\.|$)", text, re.I)
    if not m: return False
    name = m.group(1).strip().lower()
    name = name.replace("google ", "").strip() if name.startswith("google ") else name
    pkg = MAP.get(name) or MAP.get(m.group(1).strip().lower()) or MAP.get(name.replace(" ", ""))
    if not pkg: return False

    try:  # JACK_TUNE_UNLOCK_GATE
        import jack_xiaomi_unlock as _xu
        _xu.ensure_unlocked()
    except Exception:
        pass
    try:
        import jack_verify_gate as _vg
        ok, detail = _vg.app_open_verified(pkg, times=3)
        msg = ("APP OK: " if ok else "APP FAIL: ") + pkg + " | " + detail
        send_keyboard(msg, [])
        return True
    except Exception as e:
        q = chr(39)
        cmd = "ssh xiaomi-jack " + chr(34) + "su -c " + q + "monkey -p " + pkg + " -c android.intent.category.LAUNCHER 1" + q + chr(34)
        PENDING_EXEC.clear()
        PENDING_EXEC["cmd"] = cmd
        send_keyboard("VORSCHLAG (fallback):" + chr(10) + cmd + chr(10) + str(e)[:80], [[("🟢 Ausführen", "run_exec"), ("🔴 Abbrechen", "cancel_exec")]])
        return True
