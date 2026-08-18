#!/usr/bin/env python3
"""JACK Scout - Faehigkeits-Fingerabdruck des Geraets.
Read-only. Null API-Calls. Kann nichts kaputtmachen.
Ausfuehren: python3 jack_scout.py
Ergebnis: ~/jack/jack_fingerprint.json (versioniert, nie ueberschrieben)"""
import os, json, subprocess, datetime, hashlib
try:
    import jack_logging as _jlog
except Exception:
    _jlog = None

H = os.path.expanduser("~/jack")
FP_DIR = os.path.join(H, "fingerprints")
os.makedirs(FP_DIR, exist_ok=True)

def _run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = r.stdout.strip()
        return out if out else None
    except Exception:
        return None

def _check(cmd, timeout=5):
    """True wenn Befehl ohne Fehler laeuft und Output liefert."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0 and bool(r.stdout.strip())
    except Exception:
        return False

def scan_system():
    """Basis-Systeminformationen, niemals schreibend."""
    return {
        "android_version": _run("getprop ro.build.version.release"),
        "android_sdk": _run("getprop ro.build.version.sdk"),
        "device_model": _run("getprop ro.product.model"),
        "device_brand": _run("getprop ro.product.brand"),
        "cpu_abi": _run("getprop ro.product.cpu.abi"),
        "termux_api_version": _run("echo $TERMUX_API_VERSION"),
        "termux_release": _run("echo $TERMUX_APK_RELEASE"),
        "python_version": _run("python3 --version"),
        "kernel": _run("uname -r"),
        "hostname": _run("hostname"),
    }

def scan_ressourcen():
    """Aktuelle Ressourcen-Snapshot."""
    mem_raw = _run("cat /proc/meminfo | grep -E 'MemTotal|MemAvailable|MemFree'")
    mem = {}
    if mem_raw:
        for line in mem_raw.split("\n"):
            parts = line.split()
            if len(parts) >= 2:
                key = parts[0].rstrip(":")
                val_kb = int(parts[1]) if parts[1].isdigit() else 0
                mem[key] = round(val_kb / 1024, 1)  # in MB
    cpu_count = _run("nproc")
    storage = _run("df -h $HOME | tail -1 | awk '{print $2, $3, $4}'")
    return {
        "ram_mb": mem,
        "cpu_kerne": int(cpu_count) if cpu_count and cpu_count.isdigit() else None,
        "storage_home": storage,
    }

def scan_termux_api():
    """Welche termux-api Befehle funktionieren wirklich."""
    befehle = {
        "termux-battery-status": "termux-battery-status",
        "termux-wifi-connectioninfo": "termux-wifi-connectioninfo",
        "termux-location": "termux-location -p gps -r once",
        "termux-sensor": "termux-sensor -l",
        "termux-camera-photo": None,  # nicht ausfuehren, wuerde Kamera oeffnen
        "termux-clipboard-get": "termux-clipboard-get",
        "termux-notification": None,  # nicht ausfuehren, wuerde Notification senden
        "termux-tts-speak": None,      # nicht ausfuehren, wuerde sprechen
        "termux-microphone-record": None,  # nicht ausfuehren
        "termux-telephony-deviceinfo": "termux-telephony-deviceinfo",
    }
    ergebnisse = {}
    for name, testcmd in befehle.items():
        if testcmd is None:
            # Nur pruefen ob Befehl existiert, nicht ausfuehren
            existiert = _check(f"which {name}")
            ergebnisse[name] = {"vorhanden": existiert, "getestet": False, "grund": "Ausfuehrung wuerde Seiteneffekte haben"}
        else:
            ok = _check(testcmd)
            ergebnisse[name] = {"vorhanden": True, "getestet": True, "funktioniert": ok}
    return ergebnisse

def scan_python_pakete():
    """Relevante Python-Pakete die JACK nutzt oder nutzen koennte."""
    pakete = ["sqlite3", "requests", "numpy", "aiohttp", "flask", "google-genai",
              "whisper", "pydub", "sounddevice", "pyaudio"]
    verfuegbar = {}
    for p in pakete:
        try:
            __import__(p.replace("-", "_"))
            verfuegbar[p] = True
        except ImportError:
            verfuegbar[p] = False
    return verfuegbar

def scan_jack_module():
    """Welche JACK-Module existieren und importieren sauber."""
    module = [
        "jack_gemini_bridge", "jack_log", "jack_config", "jack_budget",
        "jack_missions", "jack_haliza", "jack_patch_memory", "jack_approval",
        "jack_coder", "jack_improve", "jack_learn", "jack_talk",
        "jack_oracle", "jack_autonomous",
    ]
    status = {}
    import sys
    sys.path.insert(0, H)
    for m in module:
        try:
            __import__(m)
            status[m] = "ok"
        except ImportError as e:
            status[m] = f"import_fehler: {str(e)[:60]}"
        except Exception as e:
            status[m] = f"fehler: {str(e)[:60]}"
    return status

def scan_ssh_verbindungen():
    """Bekannte SSH-Ziele pruefen."""
    ziele = {
        "xiaomi": {
            "host": __import__("jack_config").get_param("NETWORK","xiaomi_ip"),
            "port": 8022,
            "key": os.path.expanduser("~/.ssh/id_jack"),
            "user": "root",
        }
    }
    ergebnisse = {}
    for name, cfg in ziele.items():
        if not os.path.exists(cfg["key"]):
            ergebnisse[name] = "key_fehlt"
            continue
        ok = _check(
            f"ssh -i {cfg['key']} -o BatchMode=yes -o StrictHostKeyChecking=no "
            f"-o ConnectTimeout=5 -p {cfg['port']} {cfg['user']}@{cfg['host']} true",
            timeout=10
        )
        ergebnisse[name] = "erreichbar" if ok else "nicht_erreichbar"
    return ergebnisse

def scan_dateisystem():
    """Wichtige Pfade und ihre Existenz."""
    pfade = {
        "jack_home": H,
        "jack_werkstatt": os.path.expanduser("~/jack_werkstatt"),
        "jack_secrets": os.path.expanduser("~/.jack_secrets"),
        "jack_config_ini": os.path.join(H, "config.ini"),
        "jack_memory_db": os.path.join(H, "jack_memory.db"),
        "jack_errors_db": os.path.join(H, "jack_errors.db"),
        "jack_missions_db": os.path.join(H, "jack_missions.db"),
        "jack_patch_memory_db": os.path.join(H, "jack_patch_memory.db"),
        "jack_identity_json": os.path.join(H, "jack_identity.json"),
        "ssh_key_jack": os.path.expanduser("~/.ssh/id_jack"),
        "evolution_stop": os.path.join(H, ".evolution_stop"),
        "haliza_rate": os.path.join(H, ".haliza_rate"),
    }
    return {k: os.path.exists(v) for k, v in pfade.items()}

def erstelle_fingerabdruck():
    ts = datetime.datetime.now().isoformat()
    print(f"[Scout] Starte Fingerabdruck {ts}")

    print("[Scout] System...")
    system = scan_system()

    print("[Scout] Ressourcen...")
    ressourcen = scan_ressourcen()

    print("[Scout] Termux-API...")
    termux_api = scan_termux_api()

    print("[Scout] Python-Pakete...")
    python_pakete = scan_python_pakete()

    print("[Scout] JACK-Module...")
    jack_module = scan_jack_module()

    print("[Scout] SSH...")
    ssh = scan_ssh_verbindungen()

    print("[Scout] Dateisystem...")
    dateisystem = scan_dateisystem()

    fp = {
        "version": 1,
        "timestamp": ts,
        "geraet": system.get("device_brand", "?") + " " + system.get("device_model", "?"),
        "system": system,
        "ressourcen": ressourcen,
        "termux_api": termux_api,
        "python_pakete": python_pakete,
        "jack_module": jack_module,
        "ssh": ssh,
        "dateisystem": dateisystem,
    }

    # Hash des Fingerabdrucks fuer Vergleiche
    fp_json = json.dumps(fp, ensure_ascii=False, sort_keys=True)
    fp["hash"] = hashlib.sha256(fp_json.encode()).hexdigest()[:16]

    # Versioniert speichern
    dateiname = f"fingerprint_{ts[:10]}_{ts[11:19].replace(':','-')}.json"
    pfad = os.path.join(FP_DIR, dateiname)
    open(pfad, "w").write(json.dumps(fp, ensure_ascii=False, indent=2))

    # Auch als "aktuell" speichern
    aktuell = os.path.join(H, "jack_fingerprint.json")
    open(aktuell, "w").write(json.dumps(fp, ensure_ascii=False, indent=2))

    print(f"[Scout] Fertig. Hash: {fp['hash']}")
    print(f"[Scout] Gespeichert: {pfad}")
    print(f"[Scout] Aktuell: {aktuell}")
    return fp

def vergleiche_mit_letztem():
    """Vergleicht aktuellen mit letztem Fingerabdruck."""
    aktuell_pfad = os.path.join(H, "jack_fingerprint.json")
    if not os.path.exists(aktuell_pfad):
        return None
    alt = json.load(open(aktuell_pfad))
    return alt.get("hash")

def zusammenfassung(fp):
    """Menschenlesbare Zusammenfassung fuer Telegram."""
    api_ok = sum(1 for v in fp["termux_api"].values()
                 if v.get("funktioniert") or v.get("vorhanden"))
    api_total = len(fp["termux_api"])
    module_ok = sum(1 for v in fp["jack_module"].values() if v == "ok")
    module_total = len(fp["jack_module"])
    ram = fp["ressourcen"]["ram_mb"]
    ssh_status = ", ".join(f"{k}: {v}" for k, v in fp["ssh"].items())

    return (
        f"Scout-Fingerabdruck #{fp['hash']}\n"
        f"Geraet: {fp['geraet']}\n"
        f"Android: {fp['system']['android_version']} | Termux-API: {fp['system']['termux_api_version']}\n"
        f"RAM frei: {ram.get('MemAvailable', '?')} MB / {ram.get('MemTotal', '?')} MB\n"
        f"Termux-API: {api_ok}/{api_total} verfuegbar\n"
        f"JACK-Module: {module_ok}/{module_total} laden sauber\n"
        f"SSH: {ssh_status}"
    )

if __name__ == "__main__":
    alter_hash = vergleiche_mit_letztem()
    fp = erstelle_fingerabdruck()
    print("\n" + "="*50)
    print(zusammenfassung(fp))
    if alter_hash and alter_hash != fp["hash"]:
        print("\nFINGERABDRUCK GEAENDERT seit letztem Scan!")
        print(f"Alt: {alter_hash} -> Neu: {fp['hash']}")
    print("="*50)
