# JACK_TUNE_MUSTER: Erfahrungsmuster aus Missions-Logs (nur lesen, nur Vorschlag, kein LLM)
import os, re, json, glob, time, collections
H = os.path.expanduser("~/jack")
# Pruefungen: ok=false ist dort ein Ergebnis, kein Fehler
_CHECKS = {"grep_count", "file_exists", "mtime_fresh", "hb_ok", "line_check", "line_count", "no_secret",
           "xiaomi_ssh_check", "xiaomi_lage", "compile_ok", "sv_ok", "ro_scan", "ro_pyflakes", "diag", "fact"}
_HINTS = (("old nicht gefunden", "Anker vorher lesen (sed -n / grep), nicht aus dem Kopf patchen"),
          ("old fehlt", "Anker vorher lesen, Datei kann sich geaendert haben"),
          ("nicht erlaubt", "nur Dienste aus der Whitelist (Liste steht in der Fehlermeldung)"),
          ("Dienstname ungueltig", "ro_log_tail nur mit Whitelist-Namen, sonst exec_proposed tail"),
          ("Pfad-Tabu", "Zielpfad liegt ausserhalb JACK_HOME oder in Sperrbereich"),
          ("msg fehlt", "git_publish-Nachricht kurz, ohne ; und Sonderzeichen"),
          ("Schritt verboten", "plan_try erlaubt kein exec"),
          ("OBSERVER", "exec: Erkennungsartefakt, Ergebnis aus missions/logs lesen"),
          ("TEMPORAER_WEG", "Xiaomi kurz weg (Schutzfenster), spaeter erneut"))
_SEC = re.compile(r"(gh[opsu]_[A-Za-z0-9]{20}|AIza[A-Za-z0-9_-]{30}|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,}|[A-Za-z0-9+/=_-]{40,})")

def analyse(tage=14, top=6):
    cut = time.time() - tage * 86400
    tot = collections.Counter(); bad = collections.Counter(); why = collections.defaultdict(collections.Counter)
    n = 0
    for p in glob.glob(os.path.join(H, "missions", "logs", "*.json")):
        try:
            if os.path.getmtime(p) < cut:
                continue
            d = json.load(open(p, encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        r = d.get("result") if isinstance(d.get("result"), dict) else d
        a = d.get("act") or r.get("act") or "?"
        n += 1; tot[a] += 1
        if a in _CHECKS or r.get("ok", d.get("ok")) is not False:
            continue
        note = str(r.get("note") or r.get("error") or "")
        note = _SEC.sub("[X]", re.sub(r"/data/data/com\.termux/files/home/", "~/", note))
        key = re.sub(r"\d+", "#", " ".join(note.split()))[:70]
        bad[a] += 1; why[a][key] += 1
    rows = []
    for a, c in bad.most_common():
        k, kc = why[a].most_common(1)[0]
        hint = next((h for s, h in _HINTS if s.lower() in k.lower()), "")
        rows.append((a, c, tot[a], k, kc, hint))
    return n, rows[:top]

def antwort(arg=""):
    try:
        tage = int(re.findall(r"\d+", arg or "")[0]) if re.findall(r"\d+", arg or "") else 14
        tage = max(1, min(tage, 60))
        n, rows = analyse(tage)
    except Exception as e:
        return "Muster-Fehler: " + str(e)[:100]
    if not rows:
        return "Keine wiederkehrenden Fehler in %d Tagen (%d Missionen)." % (tage, n)
    out = ["Erfahrungsmuster, %d Tage, %d Missionen (nur Vorschlag):" % (tage, n)]
    for i, (a, c, t, k, kc, h) in enumerate(rows, 1):
        out.append("%d) %s: %d/%d fehlgeschlagen (%d%%)\n   haeufigster Grund (%dx): %s%s" % (
            i, a, c, t, 100 * c // max(t, 1), kc, k, ("\n   Tipp: " + h) if h else ""))
    return "\n".join(out)[:3500]
