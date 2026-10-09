#!/usr/bin/env python3
"""jack_telemetry: kompakte Messwerte von Honor und Xiaomi alle 5 Min. JACK_TUNE_TELEMETRIE
Nur Zahlen und Prozessnamen. Keine Bildschirminhalte, Nachrichten, Zwischenablage, Standort.
Datei: ~/jack/telemetry/telemetrie_JJJJ-MM.jsonl (nicht im Git). Stop: touch ~/jack/.telemetry_stop
Die Daten sind Information fuer Auswertungen. Sie werden nie automatisch zu Fakten im Graph."""
import os, json, time, datetime

J = os.path.expanduser("~/jack")
DIR = os.path.join(J, "telemetry")
STOP = os.path.join(J, ".telemetry_stop")
INTERVAL = 300


def _honor():
    d = {}
    try:
        import jack_thermal as _t
        z = _t.thermal_zonen()[:5]
        d["zonen"] = [[str(a)[:14], round(b, 1)] for a, b in z]
        r = _t.ram()
        d["ram_mb"] = {"frei": r.get("MemAvailable"), "gesamt": r.get("MemTotal")}
        d["last"] = _t.cpu_last()
        _h, procs = _t.top_prozesse(anzahl=5)
        d["proz"] = [p.split()[-1][:24] for p in procs if p.split()]
    except Exception as e:
        d["fehler"] = str(e)[:60]
    try:
        hp = os.path.join(J, "jack_health_now.json")
        b = (json.load(open(hp, encoding="utf-8")).get("bat") or {})
        d["akku"] = {"pct": b.get("pct", b.get("percentage")), "c": b.get("c", b.get("temperature")),
                     "status": b.get("status"), "alter_s": int(time.time() - os.path.getmtime(hp))}
    except Exception:
        pass
    return d


_XCMD = ('for z in /sys/class/thermal/thermal_zone*; do echo "Z $(cat $z/type) $(cat $z/temp)"; done 2>/dev/null; '
         'echo "B $(cat /sys/class/power_supply/battery/capacity) $(cat /sys/class/power_supply/battery/temp) '
         '$(cat /sys/class/power_supply/battery/status)"; '
         'echo "M $(grep MemAvailable /proc/meminfo)"; echo "L $(cat /proc/loadavg)"; '
         'ps -A -o %CPU,NAME 2>/dev/null | sort -rn | head -5 | sed "s/^/P /"')


def _parse_x(text):
    d = {}
    zonen = []
    proz = []
    for ln in (text or "").splitlines():
        t = ln.split()
        if not t:
            continue
        try:
            if t[0] == "Z" and len(t) >= 3:
                roh = int(t[-1])
                g = roh / 1000.0 if roh > 1000 else float(roh)
                typ = t[1]
                if 10 < g < 110 and "trip" not in typ.lower() and "lvl" not in typ.lower():
                    zonen.append([typ[:14], round(g, 1)])
            elif t[0] == "B" and len(t) >= 4:
                d["akku"] = {"pct": int(t[1]), "c": round(int(t[2]) / 10.0, 1), "status": t[3]}
            elif t[0] == "M" and len(t) >= 3:
                d["ram_frei_mb"] = int(t[2]) // 1024
            elif t[0] == "L":
                d["last"] = t[1:4]
            elif t[0] == "P" and len(t) >= 3:
                proz.append([t[2][:24], t[1]])
        except Exception:
            continue
    zonen.sort(key=lambda x: -x[1])
    d["zonen"] = zonen[:5]
    d["proz"] = proz
    return d


def _xiaomi(honor_max):
    if honor_max is not None and honor_max >= 58:
        return {"uebersprungen": "honor heiss"}
    try:
        import jack_xiaomi as _jx
        r = _jx.run_shell(_XCMD, as_root=True, timeout=15)
        if not r.get("success"):
            return {"weg": (r.get("stderr") or "")[:40]}
        return _parse_x(r.get("stdout"))
    except Exception as e:
        return {"fehler": str(e)[:60]}


def sample():
    h = _honor()
    try:
        hm = max(z[1] for z in h.get("zonen", [])) if h.get("zonen") else None
    except Exception:
        hm = None
    return {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "honor": h, "xiaomi": _xiaomi(hm)}


def _write(rec):
    os.makedirs(DIR, exist_ok=True)
    p = os.path.join(DIR, "telemetrie_%s.jsonl" % time.strftime("%Y-%m"))
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def loop():
    time.sleep(120)
    while True:
        if not os.path.exists(STOP):
            try:
                _write(sample())
                try:
                    import jack_xiaomi_ports as _xp  # JACK_TUNE_XPORTS
                    _xp.check()
                except Exception:
                    pass
            except Exception as e:
                try:
                    import jack_log
                    jack_log.log_decision("TELEMETRIE-ERR", str(e)[:80])
                except Exception:
                    pass
        time.sleep(INTERVAL)
