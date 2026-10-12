#!/usr/bin/env python3
"""jack_talk_probe.py - Gespraechs-Arena: Proben ohne Schreibwirkung (probe_mode, Kap 279).

Eine Probe liest JACKs Produktionsquellen, veraendert aber nichts an seinem Zustand.
Jede Probe laeuft in einem eigenen Kindprozess mit Schreibsperre (vor dem Import von JACK-Modulen):
- Dateischreiben unter HOME wird in ein Overlay im Temp-Ordner umgeleitet und protokolliert.
  Ausnahme: Kostenbuchhaltung (jack_budget), damit Probenkosten echt gezaehlt werden.
- SQLite-Dateien unter HOME werden beim ersten Zugriff per Backup ins Overlay kopiert; Schreiben trifft nur die Kopie.
- Unterprozesse nur aus einer festen Lese-Liste, sonst verweigert und protokolliert.
- Netz zu Telegram verweigert; Telegram-Sendefunktionen werden abgefangen (e2e).
Modi: unit = jack_talk.talk_to_gemini(frage); e2e = jack_telegram.handle(frage) wie im echten Chat.
Ausgabe der Proben: ~/jack_arena_private/talk/probes.jsonl (privat, nie ins Repo).

Aufruf: python3 jack_talk_probe.py ask <unit|e2e> "<frage>"
        python3 jack_talk_probe.py selftest
"""
import json
import os
import subprocess
import sys
import time

VERSION = "3"  # 2: Lese-Protokoll, Snapshot vorher/nachher; 3: Missionen + Graph-Fakten im Snapshot, Nachher voll gespeichert
J = "/data/data/com.termux/files/home/jack"
HOME = os.path.realpath(os.path.expanduser("~"))
PRIV = os.path.join(HOME, "jack_arena_private", "talk")
AUDIT = os.path.join(PRIV, "probes.jsonl")
TMP = os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp")
ALLOW_WRITE = {os.path.join(J, ".api_budget"), os.path.join(J, ".api_budget_week"), os.path.join(J, "reports", "groq_usage.jsonl")}  # Kosten/Limits echt zaehlen
READ_CMDS = {"dumpsys", "getprop", "uptime", "df", "free", "date", "termux-battery-status", "nproc", "whoami", "id"}
GIT_READ = {"log", "show", "rev-parse", "ls-files", "diff", "describe", "shortlog"}
EVIDENCE_DIR = os.path.join(PRIV, "evidence")
CAPTURE_OK = ("/jack/BETRIEBSHANDBUCH/", "/jack/00_START_HIER.md", "/jack/jack_health_now.json", "/jack/MODULKARTE.md")
SECRETISH = ("config", ".env", "token", "secret", "/.ssh", ".key", "credential", "oauth", "passw", ".pem", "auth")


# ---------------------------------------------------------------- Kindprozess: Sperre
def _install_guard(overlay, log):
    import builtins
    import io
    import socket
    import sqlite3

    real_open, real_os_open, real_connect = builtins.open, os.open, sqlite3.connect
    real_replace, real_remove = os.replace, os.remove
    real_mkdir, real_makedirs, real_gai = os.mkdir, os.makedirs, socket.getaddrinfo
    redir, dbs = {}, {}

    def prot(p):
        try:
            rp = os.fspath(p)
            rp = os.path.realpath(rp.decode() if isinstance(rp, bytes) else rp)
        except (TypeError, ValueError, UnicodeDecodeError):
            return None
        return rp if (rp == HOME or rp.startswith(HOME + os.sep)) and rp not in ALLOW_WRITE else None

    def ov(rp):
        return os.path.join(overlay, rp.replace(os.sep, "__"))

    def take(rp, keep):
        if rp not in redir:
            o = ov(rp)
            if keep and os.path.isfile(rp):
                with real_open(rp, "rb") as fi, real_open(o, "wb") as fo:
                    fo.write(fi.read())
            redir[rp] = o
            log["writes"].append(rp[len(HOME):])
        return redir[rp]

    def g_open(file, mode="r", *a, **k):
        if isinstance(file, int):
            return real_open(file, mode, *a, **k)
        rp = prot(file)
        if rp and rp in redir:
            return real_open(redir[rp], mode, *a, **k)
        if rp and any(c in mode for c in "wax+"):
            return real_open(take(rp, "a" in mode or "+" in mode), mode, *a, **k)
        if rp:
            note_read(rp)
        return real_open(file, mode, *a, **k)

    def note_read(rp):
        rel = rp[len(HOME):]
        if rel in log["reads"] or not os.path.isfile(rp):
            return
        if any(x in rel.lower() for x in SECRETISH):
            log["reads"][rel] = "geheim"  # nie Inhalt, nie Hash
            return
        try:
            size = os.path.getsize(rp)
            if size > 2_000_000:
                log["reads"][rel] = "gross:%d" % size
                return
            with real_open(rp, "rb") as f:
                data = f.read()
            log["reads"][rel] = _hb(data)
            low = rel.lower()
            if rel.startswith(CAPTURE_OK) and size <= 20000 and not any(x in low for x in SECRETISH):
                log["captured"][rel] = data.decode("utf-8", "replace")
        except OSError:
            pass

    def g_os_open(path, flags, *a, **k):
        rp = prot(path)
        if rp and (rp in redir or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC)):
            return real_os_open(take(rp, not flags & os.O_TRUNC), flags, *a, **k)
        return real_os_open(path, flags, *a, **k)

    def g_move(src, dst, *a, **k):
        rs, rd = prot(src), prot(dst)
        if not rs and not rd:
            return real_replace(src, dst)
        if rd:
            s = redir.get(rs, src) if rs else src
            if rs and rs not in redir:
                log["denied"].append("rename " + rs[len(HOME):])
                return None
            real_replace(s, take(rd, False))
            redir.pop(rs, None)
            return None
        log["denied"].append("rename_out " + rs[len(HOME):])
        return None

    def g_remove(path, *a, **k):
        rp = prot(path)
        if not rp:
            return real_remove(path, *a, **k)
        if rp in redir:
            return real_remove(redir.pop(rp))
        log["denied"].append("remove " + rp[len(HOME):])
        return None

    def g_mkdir(path, *a, **k):
        if prot(path):
            return None
        return real_mkdir(path, *a, **k)

    def g_makedirs(path, *a, **k):
        if prot(path):
            return None
        return real_makedirs(path, *a, **k)

    def g_connect(database, *a, **k):
        db = os.fspath(database) if not isinstance(database, (str, bytes)) else database
        path, uri = db, k.get("uri") or (len(a) > 6 and a[6])
        if isinstance(db, str) and db.startswith("file:"):
            path = db[5:].split("?", 1)[0]
            if "mode=ro" in db:
                return real_connect(database, *a, **k)
        rp = prot(path) if isinstance(path, str) and path != ":memory:" else None
        if not rp:
            return real_connect(database, *a, **k)
        if rp not in dbs:
            dbs[rp] = ov(rp)
            if os.path.isfile(rp):
                src = real_connect("file:%s?mode=ro" % rp, uri=True)
                dst = real_connect(dbs[rp])
                src.backup(dst)
                src.close()
                dst.close()
            log["dbs"][rp[len(HOME):]] = _h(dbs[rp])
        if uri and isinstance(db, str) and db.startswith("file:"):
            return real_connect("file:" + dbs[rp] + ("?" + db.split("?", 1)[1] if "?" in db else ""), *a, **k)
        return real_connect(dbs[rp], *a, **k)

    def argv0(args, shell):
        if shell or isinstance(args, str):
            parts = str(args).split()
        else:
            parts = [os.fspath(x) for x in args]
        return parts

    def allowed(parts):
        if not parts:
            return False
        p0 = os.path.basename(parts[0])
        if p0 in READ_CMDS and not any(c in " ".join(parts) for c in (">", "|", ";", "&", "`", "$(")):
            return True
        if p0 == "git":
            sub = [x for x in parts[1:] if not x.startswith("-")]
            return bool(sub) and sub[0] in GIT_READ
        return False

    real_run, real_popen = subprocess.run, subprocess.Popen

    def g_run(args, *a, **k):
        parts = argv0(args, k.get("shell"))
        if allowed(parts):
            r = real_run(args, *a, **k)
            o = r.stdout if isinstance(r.stdout, str) else (r.stdout or b"").decode("utf-8", "replace")
            log["subproc"].append({"cmd": " ".join(parts)[:120], "rc": r.returncode, "out_sha": _hb(o.encode()), "out": o[:4000]})
            return r
        log["subproc_denied"].append(" ".join(parts)[:80])
        txt = k.get("text") or k.get("universal_newlines") or k.get("encoding")
        if k.get("check"):
            raise subprocess.CalledProcessError(126, args, "" if txt else b"", "PROBE_DENY")
        return subprocess.CompletedProcess(args, 126, "" if txt else b"", "PROBE_DENY" if txt else b"PROBE_DENY")

    class GPopen(real_popen):
        def __init__(self, args, *a, **k):
            parts = argv0(args, k.get("shell"))
            if not allowed(parts):
                log["subproc_denied"].append(" ".join(parts)[:80])
                raise OSError(13, "PROBE_DENY")
            super().__init__(args, *a, **k)

    def g_check_output(args, *a, **k):
        k.pop("stdout", None)
        r = g_run(args, *a, capture_output=True, **k)
        if r.returncode:
            raise subprocess.CalledProcessError(r.returncode, args, r.stdout, r.stderr)
        return r.stdout

    def g_system(cmd):
        log["subproc_denied"].append(str(cmd)[:80])
        return 126 << 8

    def g_gai(host, *a, **k):
        if "telegram" in str(host).lower():
            log["net_denied"].append(str(host))
            raise OSError(13, "PROBE_DENY_NET")
        return real_gai(host, *a, **k)

    builtins.open = io.open = g_open
    os.open, os.replace, os.rename = g_os_open, g_move, g_move
    os.remove = os.unlink = g_remove
    os.mkdir, os.makedirs = g_mkdir, g_makedirs
    sqlite3.connect = g_connect
    subprocess.run, subprocess.Popen, subprocess.check_output = g_run, GPopen, g_check_output
    subprocess.call = lambda *a, **k: g_run(*a, **k).returncode
    os.system = g_system
    socket.getaddrinfo = g_gai
    return dbs


def _hb(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()[:16]


def _h(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()[:16]


def child(mode):
    req = json.loads(sys.stdin.read())
    overlay = os.path.join(TMP, "probe_%d" % os.getpid())
    os.makedirs(overlay, exist_ok=True)
    log = {"writes": [], "dbs": {}, "denied": [], "subproc_denied": [], "net_denied": [], "sent": [],
           "reads": {}, "captured": {}, "subproc": []}
    dbs = _install_guard(overlay, log)
    sys.path.insert(0, J)
    os.environ["JACK_PROBE"] = "1"
    import io
    real_out, buf = sys.stdout, io.StringIO()
    sys.stdout = buf
    t0, ans, err = time.time(), None, ""
    try:
        if mode == "unit":
            import jack_talk
            ans = jack_talk.talk_to_gemini(req["q"])
        else:
            import jack_telegram as T
            for fn in ("send", "send_voice", "send_webapp"):
                setattr(T, fn, lambda *a, **k: log["sent"].append(str(a[0])[:1500]) if a else None)
            T.send_keyboard = lambda text, buttons: log["sent"].append(str(text)[:1500])
            T.send_with_keyboard = lambda text, kb: log["sent"].append(str(text)[:1500])
            ans = T.handle(req["q"])
    except BaseException as e:  # Probe darf nie den Elternprozess reissen
        err = type(e).__name__ + ": " + str(e)[:200]
    sys.stdout = real_out
    log["db_changed"] = sorted(k for k, v in log["dbs"].items() if _h(dbs[HOME + k]) != v)
    import shutil
    shutil.rmtree(overlay, ignore_errors=True)
    out = {"answer": ans if isinstance(ans, str) else (None if ans is None else str(ans)), "err": err,
           "ms": int((time.time() - t0) * 1000), "stdout_tail": buf.getvalue()[-300:]}
    out.update(log)
    out["dbs"] = sorted(log["dbs"])
    print("PROBE_RESULT " + json.dumps(out, ensure_ascii=False))


# ---------------------------------------------------------------- Elternprozess
def snapshot(hours=168):
    """Wahrheit zum Fragezeitpunkt: Git-Stand (Commits mit Zeit, Titel, Dateien) im Fenster. Evidence-IDs G:<hash>."""
    g = lambda *a: subprocess.run(["git", "-C", J, "--no-optional-locks"] + list(a), capture_output=True, text=True, timeout=30).stdout
    head = g("rev-parse", "HEAD").strip()
    items = []
    for block in g("log", "--since=%d hours ago" % hours, "--name-only", "--format=@@%h|%cI|%s").split("@@")[1:]:
        lines = [l for l in block.splitlines() if l.strip()]
        h, t, title = lines[0].split("|", 2)
        items.append({"id": "G:" + h, "zeit": t, "titel": title, "dateien": lines[1:30]})
    snap = {"genommen": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "epoch": time.time(), "head": head, "fenster_h": hours, "commits": items}
    snap["hash"] = _hb(json.dumps([head, items], sort_keys=True).encode())  # Stabilitaet nur ueber Git (selten, aber hart)
    cut = time.time() - hours * 3600
    mis = []
    for fn in os.listdir(os.path.join(J, "missions", "logs")):
        fp = os.path.join(J, "missions", "logs", fn)
        try:
            mt = os.path.getmtime(fp)
            if fn.endswith(".json") and mt >= cut:
                with open(fp, encoding="utf-8") as f:
                    mis.append([round(mt, 1), bool(json.load(f).get("ok"))])
        except (OSError, ValueError):
            pass
    snap["missionen"] = sorted(mis)
    try:
        import sqlite3
        c = sqlite3.connect("file:%s?mode=ro" % os.path.join(J, "jack_graph.db"), uri=True)
        snap["fakten"] = [[r[0], str(r[1])[:60], r[2]] for r in c.execute("SELECT id, wert, ts FROM nodes WHERE ts>=? ORDER BY ts DESC LIMIT 30", (cut,))]
        c.close()
    except Exception as e:  # Quelle kaputt = im Snapshot sichtbar, nicht still
        snap["fakten_fehler"] = type(e).__name__
    return snap


def ask(mode, q, tag="", timeout=90):
    if mode not in ("unit", "e2e"):
        raise SystemExit("Modus unit oder e2e")
    t0 = time.strftime("%Y-%m-%d %H:%M:%S")
    snap = snapshot()
    try:
        p = subprocess.run([sys.executable, os.path.abspath(__file__), "_child", mode], input=json.dumps({"q": q}),
                           capture_output=True, text=True, timeout=timeout, cwd=TMP)
        line = [l for l in p.stdout.splitlines() if l.startswith("PROBE_RESULT ")]
        res = json.loads(line[-1][13:]) if line else {"answer": None, "err": "kein Ergebnis rc=%s %s" % (p.returncode, p.stderr[-200:])}
    except subprocess.TimeoutExpired:
        res = {"answer": None, "err": "TIMEOUT"}
    after = snapshot()
    pid = "P" + time.strftime("%Y%m%d_%H%M%S_") + _hb((q + mode + str(time.time())).encode())[:6]
    ev = {"probe_id": pid, "snapshot": snap, "snapshot_nachher": after, "reads": res.pop("reads", {}),
          "captured": res.pop("captured", {}), "subproc": res.pop("subproc", [])}
    rec = {"ts": t0, "probe_id": pid, "probe_version": VERSION, "mode": mode, "tag": tag, "q": q,
           "snapshot_hash": snap["hash"], "stabil": snap["hash"] == after["hash"]}
    rec.update(res)
    os.makedirs(EVIDENCE_DIR, mode=0o700, exist_ok=True)
    ep = os.path.join(EVIDENCE_DIR, pid + ".json")
    with open(ep, "w", encoding="utf-8") as f:
        json.dump(ev, f, ensure_ascii=False)
    os.chmod(ep, 0o600)
    os.makedirs(PRIV, mode=0o700, exist_ok=True)
    with open(AUDIT, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    os.chmod(AUDIT, 0o600)
    return rec


def _leaks(canary, since):
    hits = []
    for root, dirs, files in os.walk(HOME):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "__pycache__")]
        if root.startswith(PRIV):
            continue
        for fn in files:
            p = os.path.join(root, fn)
            try:
                if os.path.getmtime(p) < since or os.path.getsize(p) > 200_000_000:
                    continue
                with open(p, "rb") as f:
                    if canary.encode() in f.read():
                        hits.append(p[len(HOME):])
            except OSError:
                pass
    return hits


def selftest():
    import secrets
    can = "probecanary" + secrets.token_hex(4)
    since = time.time() - 1
    probes = [("e2e", "merk dir: %s ist ein Testwort" % can), ("e2e", "Was weisst du ueber %s?" % can),
              ("e2e", "Das ist falsch, hoer auf mit %s" % can), ("unit", "Erzaehl mir was ueber %s" % can)]
    seen = 0
    for mode, q in probes:
        r = ask(mode, q, tag="selftest")
        n = len(r.get("writes", [])) + len(r.get("db_changed", []))
        seen += n
        print(mode, "abgefangen=%d" % n, "db_geaendert=%s" % r.get("db_changed"), "unterprozess_verweigert=%d" % len(r.get("subproc_denied", [])),
              "netz_verweigert=%d" % len(r.get("net_denied", [])), "fehler=%s" % (r.get("err") or "-"), "antwort=%s" % str(r.get("answer"))[:70].replace("\n", " "))
    time.sleep(1)
    leaks = _leaks(can, since)
    print("Kanarienwort:", can, "| Lecks:", leaks or "keine", "| abgefangene Schreibversuche gesamt:", seen)
    ok = not leaks and seen > 0
    print("SELFTEST", "OK" if ok else "FEHLER")
    return ok


def main(argv):
    if len(argv) >= 3 and argv[1] == "_child":
        child(argv[2])
        return 0
    if len(argv) >= 4 and argv[1] == "ask":
        r = ask(argv[2], argv[3])
        print(json.dumps({k: r.get(k) for k in ("answer", "err", "ms", "writes", "db_changed", "subproc_denied", "net_denied", "sent")}, ensure_ascii=False, indent=1))
        return 0
    if len(argv) >= 2 and argv[1] == "selftest":
        return 0 if selftest() else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
