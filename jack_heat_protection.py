"""Heat-Protection + Worker-Target (Qwen 22.08. P4)
3 Stufen: Warnung (55°C), Blockade (65°C), Notfall (75°C).
+ worker_target(): entscheidet automatisch Honor vs Xiaomi."""
import os, subprocess, sys, json

HONOR_TEMP_WARN = 55
HONOR_TEMP_BLOCK = 65
HONOR_TEMP_EMERGENCY = 75

def get_temp(device="honor"):
    """Liest CPU-Temperatur."""
    try:
        if device == "honor":
            return int(open('/sys/class/thermal/thermal_zone0/temp').read().strip()) / 1000
        else:
            r = subprocess.run(["ssh","xiaomi-jack","cat /sys/class/thermal/thermal_zone0/temp"],
                              capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                return int(r.stdout.strip()) / 1000
    except Exception:
        return 0
    return 0

def _kill_exact(name, sig=15):
    import os
    r=subprocess.run(["pgrep","-x",str(name)],capture_output=True,text=True,timeout=5)
    for pid in (r.stdout or "").split():
        try: os.kill(int(pid), int(sig))
        except Exception: pass

def xiaomi_erreichbar():
    """JACK_TUNE_SPLITSTATE — nur Erreichbarkeit, ohne Ollama.
    Vorher pruefte xiaomi_online() beides zusammen und meldete offline,
    obwohl das Geraet lief — nur weil Ollama absichtlich aus war (Muster P1)."""
    try:
        r = subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=6",
                            "xiaomi-jack","echo ok"],
                           capture_output=True, text=True, timeout=10)
        return r.returncode == 0 and "ok" in (r.stdout or "")
    except Exception:
        return False


def ist_xiaomi(t):
    """JACK_TUNE_ISTXIAOMI — xiaomi und xiaomi-jack."""
    return str(t or "").strip().lower() in ("xiaomi", "xiaomi-jack")

def xiaomi_online():
    """Altname. Erreichbarkeit ohne Ollama. JACK_TUNE_E3STATE"""
    return ssh_da()

def fallback_to_local_ollama():
    """Tot. Startet kein Ollama. JACK_TUNE_NOFALL2"""
    print("P9: Ollama-Start gesperrt")
    return False

def worker_target():
    """Wer soll arbeiten. JACK_TUNE_E3STATE\n    xiaomi oder hitze+SSH -> xiaomi-jack\n    honor oder hitze ohne SSH -> honor, kein Ollama-Start"""
    honor_temp = get_temp("honor")
    try:
        import jack_workers
        best = jack_workers.get_best_worker(honor_temp)
        if best:
            print("WORKER-TARGET: %s (Honor %.1fC)"%(best['name'], honor_temp))
            return best['ssh_alias']
    except Exception as e:
        print("P11: Worker-Registry Fehler (%s), Fallback auf Zustand"%e)
    z = zustand()
    if z == "xiaomi" or (z == "hitze" and ssh_da()):
        xt = get_temp("xiaomi")
        print("WORKER-TARGET: xiaomi-jack (zustand=%s Honor %.1fC Xiaomi %.1fC)"%(z, honor_temp, xt))
        return "xiaomi-jack"
    print("WORKER-TARGET: honor (zustand=%s Honor %.1fC)"%(z, honor_temp))
    return "honor"

def check_heat(level="normal"):
    """Prueft Temperatur und gibt True zurueck wenn Aktion erlaubt."""
    temp = get_temp("honor")
    
    if level == "shadow":
        if temp > HONOR_TEMP_WARN:
            print(f"HEAT-PROTECT: Shadow-Fixer uebersprungen (CPU {temp:.1f}°C > {HONOR_TEMP_WARN}°C)")
            return False
    elif level == "ollama":
        if temp > HONOR_TEMP_BLOCK:
            print(f"HEAT-PROTECT: Ollama-Call blockiert (CPU {temp:.1f}°C > {HONOR_TEMP_BLOCK}°C)")
            return False
    elif level == "emergency":
        if temp > HONOR_TEMP_EMERGENCY:
            print(f"HEAT-EMERGENCY: CPU {temp:.1f}°C > {HONOR_TEMP_EMERGENCY}°C - Kille ollama + llama-server")
            _kill_exact("llama-server",9)
            _kill_exact("ollama",9)
            return False
    elif level == "overmind":
        # API-Teacher nur wenn Honor unter BLOCK-Schwelle
        if temp > HONOR_TEMP_BLOCK:
            print(f"HEAT-PROTECT: Overmind-API skip (CPU {temp:.1f}°C > {HONOR_TEMP_BLOCK}°C)")
            return False
    return True

def emergency_shutdown():
    """Notfall-Shutdown: Killt alle Ollama-Prozesse."""
    _kill_exact("llama-server",9)
    _kill_exact("ollama",9)
    print("HEAT-EMERGENCY: Alle Ollama-Prozesse gekillt")

def get_status():
    """Kompakter Status fuer /status oder /selftest."""
    h_temp = get_temp("honor")
    x_online = ssh_da()  # JACK_TUNE_REACH2
    x_temp = get_temp("xiaomi") if x_online else 0
    target = arbeiter()
    return {
        "honor_temp_c": round(h_temp, 1),
        "zustand": zustand(),
        "xiaomi_online": x_online,
        "xiaomi_temp_c": round(x_temp, 1),
        "next_worker": target,
        "thresholds": {"warn": HONOR_TEMP_WARN, "block": HONOR_TEMP_BLOCK, "emergency": HONOR_TEMP_EMERGENCY}
    }


def emergency_stop():
    """NIGHT-FIX (Qwen 23.08.): Stoppt alle autonomen Loops bei >80°C.
    Wird von jack_cortex Main-Loop aufgerufen."""
    import subprocess
    temp = get_temp("honor")
    if temp >= HONOR_TEMP_BLOCK:
        print(f"EMERGENCY: Honor {temp}°C >= {HONOR_TEMP_BLOCK}°C - stoppe alle Loops")
        # Shadow-Fixer killen
        _kill_exact("false")  # JACK_TUNE_NOPKILL2 autofixer-f gestrichen, kein Namens-Kill
        # Autolearn pausieren
        subprocess.run(["sv", "stop", "jack_autolearn"], capture_output=True)
        # Lokales Ollama killen (falls doch gestartet)
        _kill_exact("ollama",9)
        _kill_exact("llama-server",9)
        return True
    return False


def ssh_da():
    """Xiaomi per SSH erreichbar. Kein Ollama, kein HTTP."""
    return bool(xiaomi_erreichbar())

def dienst_da(name="ollama"):
    """Prozess auf Xiaomi per pgrep -x. Kein Port 11434."""
    try:
        r=subprocess.run(["ssh","-o","BatchMode=yes","-o","ConnectTimeout=6","xiaomi-jack","pgrep","-x",str(name)],capture_output=True,text=True,timeout=8)
        return bool((r.stdout or "").strip())
    except Exception:
        return False

def arbeiter():
    """Wer arbeiten soll. Vergleich nur mit ist_xiaomi()."""
    return worker_target()

def zustand():
    """Drei Zustaende. JACK_TUNE_E3STATE\n    xiaomi — SSH da, Honor unter BLOCK\n    honor  — SSH weg, Honor unter BLOCK\n    hitze  — Honor >= BLOCK (65C)"""
    try:
        ht = float(get_temp("honor") or 0)
    except Exception:
        ht = 0.0
    if ht >= HONOR_TEMP_BLOCK:
        return "hitze"
    if ssh_da():
        return "xiaomi"
    return "honor"

def lage(was):
    """OK / TEMPORAER_WEG / ABSICHTLICH_AUS / PAUSIERT / UNBEKANNT. JACK_TUNE_LAGE5"""
    import os as _os
    w=(was or "").lower().strip()
    if w.startswith("jack_"):
        w=w[5:]
    H="/data/data/com.termux/files/home/jack"
    S="/data/data/com.termux/files/usr/var/service"
    OK,TW,AA,PA,UN="OK","TEMPORAER_WEG","ABSICHTLICH_AUS","PAUSIERT","UNBEKANNT"
    def _down(svc):
        return _os.path.isfile(S+"/"+svc+"/down")
    def _stat(svc):
        f=S+"/"+svc+"/supervise/stat"
        try:
            return open(f).read().strip() if _os.path.isfile(f) else ""
        except Exception:
            return ""
    if w in ("ollama","llama"):
        if _os.path.isfile(H+"/.ollama_lock") or _os.path.isfile(H+"/.ollama_hb_down"):
            return AA
        return TW
    if w in ("ssh","xiaomi"):
        if ssh_da():
            return OK
        if _os.path.isfile(H+"/.xi_hb_down"):
            return AA
        return TW
    if w in ("missions",):
        if _down("jack_missions"):
            return AA
        if _os.path.isfile(H+"/missions/STOP"):
            return PA
        st=_stat("jack_missions")
        return OK if st.startswith("run") else TW
    if w in ("autolearn","publisher"):
        svc="jack_"+w
        if _down(svc):
            return AA
        st=_stat(svc)
        return OK if st.startswith("run") else TW
    if w in ("telegram","cortex","waechter"):
        svc="jack_"+w
        if _down(svc):
            return AA
        st=_stat(svc)
        return OK if st.startswith("run") else TW
    return UN
