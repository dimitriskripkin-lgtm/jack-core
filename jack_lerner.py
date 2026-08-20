#!/usr/bin/env python3
"""Stufe 2: lernt Xiaomi-Einstellungen durch reversible Experimente.
Regel: nur anfassen was (a) dokumentiert, (b) lesbar, (c) nachweislich
wiederherstellbar ist. Journal auf Platte, Restore wird verifiziert,
Kanarienvogel nach jedem Zyklus."""
import os, sys, json, re, time, sqlite3, subprocess
sys.path.insert(0, os.path.expanduser("~/jack"))
H = os.path.expanduser("~/jack")
W = os.path.join(H, "xiaomi_wissen.json")
JOURNAL = os.path.join(H, ".lerner_journal.json")
DB = os.path.join(H, "jack_lernen.db")
KEY = os.path.expanduser("~/.ssh/id_jack")

TABU = [
    # Entwickler und Debugging - Wortstamm, faengt auch development_*
    "adb", "debug", "develop", "oem_unlock", "bugreport", "testharness",
    # Hardware und Verbindung
    "usb", "sim", "radio", "airplane", "cellular", "roaming", "tether",
    "bluetooth_on", "wifi_on", "nfc", "modem", "carrier", "apn",
    # Sicherheit und Sperre
    "lock", "encrypt", "credential", "keyguard", "biometric", "fingerprint",
    "face_unlock", "password", "pin_", "pattern", "trust_agent",
    # Geraeteverwaltung
    "device_owner", "device_admin", "provision", "factory", "reset", "wipe",
    "safe_boot", "boot_count", "setup_wizard", "frp", "restore",
    # Barrierefreiheit - Abschalten kann Nutzer aussperren
    "accessibility", "talkback", "captioning", "magnif",
    # Installation und Verifikation
    "install_non_market", "verifier", "package_verifier", "unknown_sources",
    # Netz und Konten
    "vpn", "proxy", "dns", "private_dns", "captive", "account",
    # Notfall
    "emergency", "sos", "cell_broadcast", "alert",
    "audio_safe_volume",  # EU-Kopfhoererschutz - P0 Fix
]

def _ip():
    import jack_config
    return jack_config.get_param("NETWORK", "xiaomi_ip")

def sh(cmd, t=15):
    try:
        r = subprocess.run(["ssh","-i",KEY,"-o","BatchMode=yes",
            "-o","StrictHostKeyChecking=accept-new","-o","UserKnownHostsFile=/dev/null",
            "-o","LogLevel=ERROR","-o","ConnectTimeout=4","-p","8022",
            "root@"+_ip(), cmd], capture_output=True, text=True, timeout=t)
        return (r.stdout or "").strip(), r.returncode
    except Exception as e:
        return "SSHFEHLER:" + str(e)[:60], 99

def _db():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS beobachtungen (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, namespace TEXT,
        schluessel TEXT, alt_wert TEXT, test_wert TEXT, beschreibung TEXT,
        ui_aenderung TEXT, restore_ok INTEGER, ergebnis TEXT)""")
    c.commit()
    return c

def _wissen():
    try: return json.load(open(W))
    except Exception: return {}

def _journal_lesen():
    try: return json.load(open(JOURNAL))
    except Exception: return []

def _journal_schreiben(eintraege):
    tmp = JOURNAL + ".tmp"
    json.dump(eintraege, open(tmp, "w"))
    os.replace(tmp, JOURNAL)

def journal_abarbeiten():
    """Stellt nach Absturz alle offenen Aenderungen wieder her."""
    offen = _journal_lesen()
    if not offen: return "Journal leer, nichts zurueckzusetzen"
    ok = fehl = 0
    for e in offen:
        out, rc = sh("su -c 'settings put " + e["ns"] + " " + e["key"] +
                     " " + e["alt"] + "'")
        pruef, _ = sh("su -c 'settings get " + e["ns"] + " " + e["key"] + "'")
        if pruef.strip() == e["alt"].strip(): ok += 1
        else: fehl += 1
    _journal_schreiben([])
    return "Journal abgearbeitet: " + str(ok) + " ok, " + str(fehl) + " FEHLGESCHLAGEN"

def kanarienvogel():
    """Lebt das Geraet noch normal?"""
    out, rc = sh("su -c 'echo lebt'", t=8)
    if rc != 0 or "lebt" not in out: return False, "SSH tot"
    fokus, _ = sh("su -c 'dumpsys window | grep mCurrentFocus'", t=10)
    if not fokus: return False, "Kein UI-Fokus"
    return True, "ok"

def kandidaten(limit=40):
    """Nur was dokumentiert, lesbar, numerisch und nicht tabu ist."""
    d = _wissen()
    besch = d.get("settings_bedeutung", {})
    keys = d.get("settings_keys", {})
    raus = []
    for ns in ("system", "secure", "global"):
        for k in keys.get(ns, []):
            if k not in besch: continue
            low = k.lower()
            if any(t in low for t in TABU): continue
            raus.append((ns, k, besch[k]))
    raus.sort(key=lambda x: (_stufe(x[1]), x[1]))
    return raus[:limit]

def _stufe(key):
    """0 = harmlos und sofort messbar, 3 = lieber spaeter."""
    k = key.lower()
    if any(w in k for w in ("font", "brightness", "dim_screen", "animation",
                            "haptic", "vibrate", "sound_effects", "screen_off",
                            "master_mono", "dtmf", "volume", "ringer")):
        return 0
    if any(w in k for w in ("display", "color", "rotation", "alarm", "notification",
                            "media", "tone", "hearing", "touch")):
        return 1
    if any(w in k for w in ("app", "service", "policy", "network", "data",
                            "sync", "account", "call", "sms", "cdma", "wifi")):
        return 3
    return 2

def _testwert(alt):
    """Sicherer Nachbarwert. Nur fuer numerische Werte."""
    try: n = int(alt)
    except Exception: return None
    if n in (0, 1): return str(1 - n)
    if 2 <= n <= 100: return str(max(1, n - 1))
    if n > 100: return str(int(n * 0.9))
    return None

def _uidump():
    sh("su -c 'uiautomator dump /sdcard/l.xml'", t=18)
    xml, _ = sh("su -c 'cat /sdcard/l.xml'", t=18)
    return set(re.findall(r'text="([^"]{2,50})"', xml))

def experiment(ns, key, beschreibung, mit_ui=False):
    """Ein vollstaendiger Zyklus. Gibt (erfolg, text) zurueck."""
    alt, rc = sh("su -c 'settings get " + ns + " " + key + "'")
    if rc != 0 or not alt or alt == "null":
        return False, "kein lesbarer Wert"
    neu = _testwert(alt)
    if neu is None:
        return False, "nicht numerisch, uebersprungen"

    _journal_schreiben(_journal_lesen() + [{"ns": ns, "key": key, "alt": alt}])
    vor = _uidump() if mit_ui else set()

    sh("su -c 'settings put " + ns + " " + key + " " + neu + "'")
    time.sleep(1.5)
    gesetzt, _ = sh("su -c 'settings get " + ns + " " + key + "'")
    try:
        from wirkungs_check import check_ui as _wc
        if _wc() is False:
            sh("su -c 'settings put " + ns + " " + key + " " + alt + "'")
            return False, "SOS-SCHUTZ: Notfall-Activity nach Setzen " + key
    except Exception:
        pass
    nach = _uidump() if mit_ui else set()
    diff = (nach - vor) | (vor - nach) if mit_ui else set()

    sh("su -c 'settings put " + ns + " " + key + " " + alt + "'")
    time.sleep(1.0)
    zurueck, _ = sh("su -c 'settings get " + ns + " " + key + "'")
    try:
        from wirkungs_check import check_ui as _wc2
        if _wc2() is False:
            return False, "SOS-SCHUTZ: Notfall-Activity nach Restore " + key
    except Exception:
        pass
    restore_ok = zurueck.strip() == alt.strip()

    rest = [e for e in _journal_lesen()
            if not (e["ns"] == ns and e["key"] == key)]
    _journal_schreiben(rest if not restore_ok else
                       [e for e in rest])
    if not restore_ok:
        _journal_schreiben(rest + [{"ns": ns, "key": key, "alt": alt}])

    c = _db()
    c.execute("""INSERT INTO beobachtungen
        (ts,namespace,schluessel,alt_wert,test_wert,beschreibung,ui_aenderung,restore_ok,ergebnis)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (time.strftime("%Y-%m-%d %H:%M:%S"), ns, key, alt, neu,
         beschreibung[:300], " | ".join(sorted(diff))[:400],
         1 if restore_ok else 0,
         "gesetzt=" + gesetzt + " zurueck=" + zurueck))
    c.commit(); c.close()

    if not restore_ok:
        return False, "RESTORE FEHLGESCHLAGEN bei " + key + " (alt=" + alt + ", ist=" + zurueck + ")"
    text = key + ": " + alt + " -> " + neu + " -> zurueck ok"
    if mit_ui: text += " | UI-Diff " + str(len(diff))
    return True, text

def runde(anzahl=5, mit_ui=False):
    """Eine Lernrunde. Bricht bei Kanarienvogel-Alarm sofort ab."""
    r = journal_abarbeiten()
    lebt, grund = kanarienvogel()
    if not lebt: return "ABBRUCH vor Start: " + grund

    c = _db()
    schon = {x[0] for x in c.execute(
        "SELECT schluessel FROM beobachtungen WHERE restore_ok=1")}
    c.close()

    getan, ok, uebersprungen = [], 0, 0
    for ns, key, besch in kandidaten(120):
        if len(getan) >= anzahl: break
        if key in schon: continue
        erfolg, text = experiment(ns, key, besch, mit_ui)
        if "nicht numerisch" in text or "kein lesbarer" in text:
            uebersprungen += 1; continue
        getan.append(text)
        if erfolg: ok += 1
        else:
            return ("NOTSTOPP nach " + str(len(getan)) + " Experimenten: " + text +
                    "\n" + "\n".join(getan))
        lebt, grund = kanarienvogel()
        if not lebt:
            journal_abarbeiten()
            return "NOTSTOPP Kanarienvogel: " + grund + "\n" + "\n".join(getan)
        time.sleep(60)
    return ("RUNDE OK | " + str(ok) + " gelernt, " + str(uebersprungen) +
            " uebersprungen\n" + "\n".join(getan[:6]))

def bericht():
    c = _db()
    n = c.execute("SELECT COUNT(*) FROM beobachtungen").fetchone()[0]
    gut = c.execute("SELECT COUNT(*) FROM beobachtungen WHERE restore_ok=1").fetchone()[0]
    letzte = c.execute("""SELECT schluessel, alt_wert, test_wert FROM beobachtungen
        WHERE restore_ok=1 ORDER BY id DESC LIMIT 5""").fetchall()
    c.close()
    kand = len(kandidaten(9999))
    z = ["Lernstand:", "  Experimente: " + str(n) + " | sauber zurueckgesetzt: " + str(gut),
         "  Kandidaten gesamt: " + str(kand),
         "  Journal offen: " + str(len(_journal_lesen()))]
    for k, a, t in letzte: z.append("  " + k + " (" + a + " -> " + t + ")")
    return "\n".join(z)

if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "bericht"
    if a == "runde": print(runde(5, False))
    elif a == "runde_ui": print(runde(3, True))
    elif a == "journal": print(journal_abarbeiten())
    elif a == "kandidaten":
        for ns, k, b in kandidaten(15): print("  [" + ns + "] " + k + ": " + b[:70])
    elif a == "kanarie": print(kanarienvogel())
    else: print(bericht())


# SOS-INCIDENT 18.08.2026: nur explizit freigegebene Parameter
# Kein Audio, Vibration, Klingelton, Lautstaerke
POSITIV = {
    "system.font_scale",
    "system.screen_off_timeout",
    "system.accelerometer_rotation",
    "global.enable_back_animation",
    "system.pointer_speed",
}

def kandidaten(limit=40):
    d = _wissen()
    besch = d.get("settings_bedeutung", {})
    raus = []
    for ns_key in sorted(POSITIV):
        ns, key = ns_key.split(".", 1)
        raus.append((ns, key, besch.get(key, ns_key)))
    return raus[:limit]
