"""JACK_TUNE_XIBREAKER2: gemeinsamer Schutzschalter fuer alle Xiaomi-SSH-Wege (jack_xiaomi.run_shell, jack_exec.run).
Zustand in ~/jack/.xiaomi_breaker.json (prozessuebergreifend). 2 Fehlschlaege in Folge -> 30 s Sperre."""
import json, os, time
P = os.path.expanduser("~/jack/.xiaomi_breaker.json")

def _ld():
    try:
        return json.load(open(P))
    except Exception:
        return {"fails": 0, "until": 0.0}

def wait():
    return max(0.0, float(_ld().get("until", 0.0)) - time.time())

def note(ok):
    d = _ld()
    if ok:
        d = {"fails": 0, "until": 0.0}
    else:
        d["fails"] = int(d.get("fails", 0)) + 1
        if d["fails"] >= 2:
            d["until"] = time.time() + 30
    try:
        json.dump(d, open(P, "w"))
    except Exception:
        pass
