#!/data/data/com.termux/files/usr/bin/python3
"""Kurz-Health: Dienste, SSH, Heartbeats, Tune  # JACK_TUNE_HEALTH → jack_health_now.json"""
import json, subprocess, time
from pathlib import Path
H = Path("/data/data/com.termux/files/home/jack")


def bat_fresh(max_age=900):
    """Honor-Akku aus health_now.json. None wenn tot oder aelter max_age. JACK_TUNE_BATFRESH"""
    import json, os, time
    hn = "/data/data/com.termux/files/home/jack/jack_health_now.json"
    try:
        if not os.path.isfile(hn):
            return None
        if time.time() - os.path.getmtime(hn) > max_age:
            return None
        b = (json.loads(open(hn, encoding="utf-8").read()).get("bat") or {})
        if b.get("err") is not None or b.get("pct") is None:
            return None
        return b
    except Exception:
        return None

def sh(cmd, t=8):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t)
        return ((p.stdout or "") + (p.stderr or "")).strip()
    except Exception as e:
        return str(e)

def main():
    health = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sv": sh("sv status /data/data/com.termux/files/usr/var/service/jack_* 2>/dev/null"),
        "ssh_xiaomi": "OK" if "OK" in sh("ssh -o ConnectTimeout=4 -o BatchMode=yes xiaomi-jack 'echo OK'") else "DOWN",
        "heartbeats": {},
    }
    health["hb_stale"] = []
    for f in H.glob(".heartbeat_*"):
        name = f.name.replace(".heartbeat_", "")
        age = round(time.time() - f.stat().st_mtime, 1)
        health["heartbeats"][name] = age
        down = Path("/data/data/com.termux/files/usr/var/service/" + name + "/down").is_file()
        if down or age > 3600:
            health["hb_stale"].append(name)
    try:
        tj = H / "jack_tune.json"
        health["tune"] = json.loads(tj.read_text()) if tj.is_file() else None
    except Exception:
        health["tune"] = None
    health["marks"] = {}
    for rel, mark in (("jack_hey.py","JACK_TUNE_NC"),("jack_voice.py","JACK_TUNE_NC"),("jack_publish.py","JACK_TUNE_HASH"),("jack_autolearn_loop.py","JACK_TUNE_PAUSE")):
        p = H / rel
        health["marks"][rel] = (mark in p.read_text(encoding="utf-8", errors="ignore")) if p.is_file() else False
    health["lock"] = (H / ".ollama_lock").is_file()
    health["persona_b"] = (H / "jack_persona.md").stat().st_size if (H / "jack_persona.md").is_file() else -1
    health["approvals_b"] = (H / "pending_approvals.json").stat().st_size if (H / "pending_approvals.json").is_file() else -1
    _osvc = "/data/data/com.termux/files/usr/var/service"
    health["ollama_svc"] = "disabled" if Path(_osvc + "/_ollama_disabled").is_dir() else ("live" if Path(_osvc + "/ollama").is_dir() else "missing")
    health["fix_bak"] = len(list(H.glob("*.fix.bak")))
    # JACK_TUNE_HEALTHHONEST
    try:
        _br = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=5)
        _bd = json.loads(_br.stdout or "{}")
        _ma = _bd.get("current")
        _note = None
        try:
            _mai = int(_ma)
            if abs(_mai) >= 10000:
                _note = "roh wirkt wie uA, nicht mA"
        except Exception:
            _mai = _ma
        health["bat"] = {
            "pct": _bd.get("percentage"),
            "c": _bd.get("temperature"),
            "ma_raw": _ma,
            "ma": _mai,
            "note": _note,
            "plugged": _bd.get("plugged"),
            "status": _bd.get("status"),
        }
    except Exception as _be:
        health["bat"] = {"err": str(_be)[:80]}
    try:
        _dr = H / "reports" / "drain.jsonl"
        _dr.parent.mkdir(parents=True, exist_ok=True)
        _b = health.get("bat") or {}
        _line = json.dumps({"ts": health["ts"], "pct": _b.get("pct"), "c": _b.get("c"), "ma_raw": _b.get("ma_raw"), "plugged": _b.get("plugged"), "status": _b.get("status"), "ssh": health.get("ssh_xiaomi")}, ensure_ascii=False)
        with _dr.open("a", encoding="utf-8") as _fh:
            _fh.write(_line + "\n")
    except Exception:
        pass  # JACK_TUNE_DRAINLOG
    out = H / "jack_health_now.json"
    health["written_at"] = int(__import__("time").time())
    out.write_text(json.dumps(health, indent=2, ensure_ascii=False))
    print(json.dumps({k: health[k] for k in ("ts", "ssh_xiaomi", "heartbeats", "tune", "marks")}, ensure_ascii=False))
    return 0 if health["ssh_xiaomi"] == "OK" else 1

if __name__ == "__main__":
    import sys as _s
    if "--daily" in _s.argv:
        print(tagesbericht())
        raise SystemExit(0)
    raise SystemExit(main())

# ---------------------------------------------------------------
# JACK_TUNE_DAILY — Tagesbericht: was hat sich VERAENDERT
# Kein Alarm, keine Ampel. Verlauf statt Zustand.
# Vergleich mit dem Vortag, damit Abweichungen auffallen.
# ---------------------------------------------------------------
def _d_snap():
    """Sammelt die Kennzahlen des Tages."""
    import os as _o, json as _j, sqlite3, subprocess, time
    J = "/data/data/com.termux/files/home/jack"
    s = {"ts": time.strftime("%Y-%m-%d %H:%M"), "tag": time.strftime("%Y-%m-%d")}

    try: s["persona_b"] = _o.path.getsize(_o.path.join(J, "jack_persona.md"))
    except Exception: s["persona_b"] = None

    for name, datei in (("gespraeche", "reports/decisions.jsonl"),
                        ("groq_calls", "reports/groq_usage.jsonl")):
        try:
            s[name] = sum(1 for _ in open(_o.path.join(J, datei), encoding="utf-8"))
        except Exception:
            s[name] = 0

    try:
        tot = 0
        for l in open(_o.path.join(J, "reports/groq_usage.jsonl"), encoding="utf-8"):
            d = _j.loads(l)
            if str(d.get("ts", "")).startswith(s["tag"]):
                tot += int(d.get("total") or 0)
        s["token_heute"] = tot
    except Exception:
        s["token_heute"] = 0

    try:
        con = sqlite3.connect(_o.path.join(J, "jack_errors.db"))
        s["fehler_offen"] = con.execute(
            "SELECT COUNT(*) FROM errors WHERE resolved=0").fetchone()[0]
        con.close()
    except Exception:
        s["fehler_offen"] = None

    for d in ("pending", "fail", "done"):
        try:
            p = _o.path.join(J, "missions", d)
            s["m_" + d] = len([x for x in _o.listdir(p) if x.endswith(".json")])
        except Exception:
            s["m_" + d] = 0

    try:
        s["temp_honor"] = round(int(open(
            "/sys/class/thermal/thermal_zone0/temp").read().strip()) / 1000, 1)
    except Exception:
        s["temp_honor"] = None

    try:
        r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6",
                            "xiaomi-jack",
                            "cat /sys/class/thermal/thermal_zone0/temp"],
                           capture_output=True, text=True, timeout=12)
        s["temp_xiaomi"] = round(int((r.stdout or "0").strip()) / 1000, 1)
    except Exception:
        s["temp_xiaomi"] = None

    s["lock"] = _o.path.isfile(_o.path.join(J, ".ollama_lock"))
    s["stop"] = _o.path.isfile(_o.path.join(J, "missions", "STOP"))

    try:
        r = subprocess.run(
            ["sv", "status",
             "/data/data/com.termux/files/usr/var/service/jack_telegram",
             "/data/data/com.termux/files/usr/var/service/jack_waechter",
             "/data/data/com.termux/files/usr/var/service/jack_cortex"],
            capture_output=True, text=True, timeout=12)
        s["dienste_run"] = (r.stdout or "").count("run:")
    except Exception:
        s["dienste_run"] = None

    return s


def _d_diff(a, b, name, einheit="", wichtig=False):
    """Eine Zeile Veraenderung. a=gestern b=heute."""
    if b is None:
        return f"  {name}: nicht messbar"
    if a is None or a == b:
        return f"  {name}: {b}{einheit}"
    d = b - a if isinstance(a, (int, float)) and isinstance(b, (int, float)) else None
    if d is None:
        return f"  {name}: {b}{einheit}  (war {a}{einheit})"
    pfeil = "+" if d > 0 else ""
    mark = "  <-- " if wichtig else "  "
    return f"  {name}: {b}{einheit}{mark}({pfeil}{d})"


def tagesbericht(speichern=True):
    """Erzeugt den Bericht. Vergleicht mit dem letzten gespeicherten Stand."""
    import os as _o, json as _j
    J = "/data/data/com.termux/files/home/jack"
    P = _o.path.join(J, "reports", "daily.jsonl")

    heute = _d_snap()
    gestern = None
    try:
        zeilen = [l for l in open(P, encoding="utf-8") if l.strip()]
        for l in reversed(zeilen):
            k = _j.loads(l)
            if k.get("tag") != heute["tag"]:
                gestern = k
                break
    except Exception:
        pass

    g = gestern or {}
    z = []
    z.append(f"JACK Tagesbericht {heute['ts']}")
    if gestern:
        z.append(f"Vergleich mit {gestern.get('tag')}")
    else:
        z.append("Erster Bericht - noch kein Vergleich moeglich")
    z.append("")

    z.append("System")
    z.append(_d_diff(g.get("persona_b"), heute["persona_b"], "Persona", " B", True))
    z.append(_d_diff(g.get("dienste_run"), heute["dienste_run"], "Dienste aktiv", "/4", True))  # JACK_TUNE_DAILY4
    z.append(f"  Ollama-Sperre: {'liegt' if heute['lock'] else 'FEHLT'}")
    z.append(f"  Warteschlangen-Stopp: {'liegt' if heute['stop'] else 'offen'}")
    z.append("")

    z.append("Temperatur")
    z.append(_d_diff(g.get("temp_honor"), heute["temp_honor"], "Honor", " C"))
    z.append(_d_diff(g.get("temp_xiaomi"), heute["temp_xiaomi"], "Xiaomi", " C"))
    z.append("")

    z.append("Nutzung")
    z.append(_d_diff(g.get("gespraeche"), heute["gespraeche"], "Entscheidungen", ""))
    z.append(_d_diff(g.get("groq_calls"), heute["groq_calls"], "Groq-Aufrufe", ""))
    tok = heute["token_heute"]
    proz = round(100 * tok / 200000) if tok else 0
    z.append(f"  Token heute: {tok} ({proz}% vom Tageslimit)")
    z.append("")

    z.append("Missionen und Fehler")
    z.append(_d_diff(g.get("m_pending"), heute["m_pending"], "wartend", "", True))
    z.append(_d_diff(g.get("m_fail"), heute["m_fail"], "fehlgeschlagen", "", True))
    z.append(_d_diff(g.get("m_done"), heute["m_done"], "erledigt", ""))
    z.append(_d_diff(g.get("fehler_offen"), heute["fehler_offen"], "offene Fehler", "", True))

    auff = []
    if heute["persona_b"] and g.get("persona_b") and heute["persona_b"] != g["persona_b"]:
        auff.append("Persona hat sich veraendert - pruefen wer geschrieben hat")
    if not heute["lock"]:
        auff.append("Ollama-Sperre fehlt")
    if heute["m_pending"] and heute["m_pending"] > 0:
        auff.append(f"{heute['m_pending']} Missionen warten trotz Stopp")
    if proz > 80:
        auff.append(f"Token-Tageslimit zu {proz}% verbraucht")
    if heute["temp_xiaomi"] and heute["temp_xiaomi"] > 45:
        auff.append(f"Xiaomi bei {heute['temp_xiaomi']} C")

    if auff:
        z.append("")
        z.append("Auffaellig")
        for a in auff:
            z.append("  - " + a)

    if speichern:
        try:
            _o.makedirs(_o.path.dirname(P), exist_ok=True)
            with open(P, "a", encoding="utf-8") as fh:
                fh.write(_j.dumps(heute, ensure_ascii=False) + "\n")
        except Exception:
            pass

    return "\n".join(z)


