"""JACK_TUNE_LOGROT: einfache Log-Rotation. Aufruf stuendlich aus jack_telemetry.loop.
Logs > 5 MB: letzte 1 MB nach <name>.old.log (ueberschrieben), Original in-place auf 0 gekuerzt
(offene Append-Handles der Dienste bleiben gueltig). Nichts wird geloescht ausser der aelteren Haelfte."""
import os, glob, time
H = os.path.expanduser("~/jack")
GRENZE = 5 * 1024 * 1024  # JACK_TUNE_LOGROT
BEHALTEN = 1024 * 1024
STAMP = H + "/.logrot_stamp"

def rotiere(force=False):
    try:
        if not force and os.path.exists(STAMP) and time.time() - os.path.getmtime(STAMP) < 3600:
            return []
        open(STAMP, "w").write(str(time.time()))
    except Exception:
        pass
    getan = []
    for p in [H + "/waechter.log"] + glob.glob(H + "/logs/*.log"):
        try:
            if p.endswith(".old.log") or os.path.getsize(p) <= GRENZE:
                continue
            with open(p, "rb") as f:
                f.seek(-BEHALTEN, 2)
                rest = f.read()
            with open(p[:-4] + ".old.log", "wb") as o:
                o.write(rest)
            with open(p, "r+b") as f:
                f.truncate(0)
            getan.append(os.path.basename(p))
        except Exception:
            continue
    if getan:
        try:
            import jack_log
            jack_log.log_decision("LOGROT", ",".join(getan)[:80])
        except Exception:
            pass
    return getan
