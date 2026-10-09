# JACK_TUNE_SKILLIDEE: Skill-Ideen aus erledigter Arbeit (nur lesen, nur Vorschlag, kein Code-Erzeugen, kein LLM)
import os, re, json, glob, time, collections
H = os.path.expanduser("~/jack")
_TRIVIAL = {"grep_count", "file_exists", "mtime_fresh", "hb_ok", "line_check", "line_count", "no_secret", "fact", "diag"}

def _laden(tage):
    cut = time.time() - tage * 86400
    rows = []
    for p in glob.glob(os.path.join(H, "missions", "logs", "*.json")):
        try:
            if os.path.getmtime(p) < cut:
                continue
            d = json.load(open(p, encoding="utf-8", errors="replace"))
            r = d.get("result") if isinstance(d.get("result"), dict) else d
            a = d.get("act") or r.get("act")
            ts = d.get("ts") or r.get("ts") or ""
            if a and ts:
                rows.append((ts, a, r.get("ok", d.get("ok")) is not False))
        except Exception:
            continue
    rows.sort()
    return rows

def _t(ts):
    try:
        return time.mktime(time.strptime(ts[:19], "%Y-%m-%d %H:%M:%S"))
    except Exception:
        return 0

def ideen(tage=30, top=5):
    rows = _laden(tage)
    folgen, cur, last = [], [], 0
    for ts, a, ok in rows:
        t = _t(ts)
        if cur and t - last > 600:
            folgen.append(cur); cur = []
        cur.append((a, ok)); last = t
    if cur:
        folgen.append(cur)
    cnt = collections.Counter()
    for f in folgen:
        for n in (3, 4, 5):
            for i in range(len(f) - n + 1):
                seg = f[i:i + n]
                acts = tuple(a for a, _ in seg)
                if all(ok for _, ok in seg) and len(set(acts)) >= 3 and not set(acts) <= _TRIVIAL \
                        and sum(1 for a in acts if a in _TRIVIAL) <= 1:
                    cnt[acts] += 1
    # Teilfolgen unterdruecken: nur die laengste mit gleichem oder aehnlichem Zaehler behalten
    out = []
    for acts, c in cnt.most_common(60):
        if c < 4:
            break
        if any(set(acts) <= set(o[0]) and len(acts) < len(o[0]) and o[1] >= c * 0.8 for o in out):
            continue
        out.append((acts, c))
        if len(out) >= top:
            break
    return len(rows), out

def antwort(arg=""):
    try:
        n, out = ideen()
    except Exception as e:
        return "Skill-Ideen-Fehler: " + str(e)[:100]
    if not out:
        return "Keine wiederkehrenden Abfolgen gefunden (%d Missionen, 30 Tage)." % n
    z = ["Skill-Ideen aus erledigter Arbeit (30 Tage, %d Missionen, nur Vorschlag):" % n]
    for i, (acts, c) in enumerate(out, 1):
        z.append("%d) %s  (%dx erfolgreich)\n   Name-Vorschlag: %s" % (i, " > ".join(acts), c, "_".join(a.replace("_ok", "") for a in acts)[:40]))
    z.append("Naechster Schritt: sag mir welche Idee, ich baue sie als Skill (mit Haliza-Pruefung und deiner Freigabe).")
    return "\n".join(z)[:3500]
