import os
import subprocess
import configparser

JACK_DIR = os.path.expanduser("~/jack")
CONFIG = os.path.join(JACK_DIR, "config.ini")

def _lese_config():
    out = {"pfad": CONFIG, "geladen": False, "xiaomi_ip": None, "modell": None}
    if not os.path.exists(CONFIG):
        return out
    try:
        cp = configparser.ConfigParser()
        cp.read(CONFIG)
        out["geladen"] = True
        if cp.has_option("NETWORK", "xiaomi_ip"):
            out["xiaomi_ip"] = cp.get("NETWORK", "xiaomi_ip")
        if cp.has_option("gemini", "model"):
            out["modell"] = cp.get("gemini", "model")
    except Exception as e:
        out["fehler"] = str(e)
    return out

def _git_status():
    out = {"branch": None, "lokal": None, "remote": None, "synchron": None}
    try:
        out["branch"] = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=JACK_DIR, text=True).strip()
        out["lokal"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=JACK_DIR, text=True).strip()[:7]
        info = subprocess.check_output(
            ["git", "ls-remote", "origin", "master"], cwd=JACK_DIR,
            text=True, timeout=15).split()
        if info:
            out["remote"] = info[0][:7]
            out["synchron"] = (out["lokal"] == out["remote"])
    except Exception as e:
        out["fehler"] = str(e)
    return out

def preflight():
    return {"config": _lese_config(), "git": _git_status()}

def bericht():
    d = preflight()
    z = chr(10)
    c = d["config"]
    g = d["git"]
    lin = []
    lin.append("[SANITY] Config: " + ("geladen" if c.get("geladen") else "NICHT gefunden"))
    if c.get("xiaomi_ip"):
        lin.append("[SANITY] Xiaomi-IP aktiv: " + str(c["xiaomi_ip"]))
    if c.get("modell"):
        lin.append("[SANITY] Gemini-Modell: " + str(c["modell"]))
    if g.get("fehler"):
        lin.append("[SANITY] Git-Check-Fehler: " + str(g["fehler"])[:100])
    else:
        sync = g.get("synchron")
        if sync is True:
            lin.append("[SANITY] Git synchron mit origin/master (" + str(g.get("lokal")) + ")")
        elif sync is False:
            lin.append("[SANITY] ACHTUNG Git NICHT synchron: lokal " + str(g.get("lokal")) + " remote " + str(g.get("remote")))
        else:
            lin.append("[SANITY] Git-Status unklar (remote nicht erreichbar?)")
    return z.join(lin)

if __name__ == "__main__":
    print(bericht() + chr(10))


def check():
    """Alias fuer Waechter-Thread."""
    return preflight()
