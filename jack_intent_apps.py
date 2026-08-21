import re
MAP = dict(p.split(":") for p in "einstellungen:com.android.settings|settings:com.android.settings|chrome:com.android.chrome|browser:com.android.chrome|kamera:com.miui.camera|camera:com.miui.camera|foto:com.miui.gallery|fotos:com.miui.gallery|galerie:com.miui.gallery|gallery:com.miui.gallery|rechner:com.miui.calculator|calculator:com.miui.calculator|uhr:com.miui.deskclock|clock:com.miui.deskclock|kontakte:com.android.contacts|contacts:com.android.contacts|telefon:com.android.dialer|phone:com.android.dialer|dateien:com.android.fileexplorer|files:com.android.fileexplorer|musik:com.miui.player|music:com.miui.player|youtube:com.google.android.youtube|gmail:com.google.android.gm|mail:com.google.android.gm|email:com.google.android.gm|maps:com.google.android.apps.maps|karten:com.google.android.apps.maps|whatsapp:com.whatsapp|telegram:org.telegram.messenger|spotify:com.spotify.music|netflix:com.netflix.mediaclient|twitter:com.twitter.android|x:com.twitter.android|instagram:com.instagram.android|tiktok:com.zhiliaoapp.musically".split("|"))
def try_app_launch(text, PENDING_EXEC, send_keyboard):
    m = re.search(r"(?:öffne|starte|eröffne|mache? auf)\s+(?:die\s+|den\s+|das\s+)?([a-zA-Z0-9äöüß\s]+?)(?:\s+auf\s+dem|\s+und|\.|$)", text, re.I)
    if not m: return False
    pkg = MAP.get(m.group(1).strip().lower())
    if not pkg: return False
    q = chr(39)
    cmd = "ssh xiaomi-jack " + chr(34) + "su -c " + q + "monkey -p " + pkg + " -c android.intent.category.LAUNCHER 1" + q + chr(34)
    PENDING_EXEC.clear()
    PENDING_EXEC["cmd"] = cmd
    send_keyboard("VORSCHLAG:" + chr(10) + cmd, [[("🟢 Ausführen", "run_exec"), ("🔴 Abbrechen", "cancel_exec")]])
    return True
