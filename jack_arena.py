#!/usr/bin/env python3
"""JACK-Arena-0 Engine (Phase 2) - nur Mechanik, keine Aufgabeninhalte.

Baut Fixtures, bereitet Runs vor, richtet deterministisch (kein LLM im Richter).
Aufgaben, Oracles und Holdout liegen NICHT im Repo (oeffentlich), sondern in
~/jack_arena_private. Kein Netz. Schreibt nur in ARENA. Not-Aus: ~/jack/.arena_off
Kategorie C (Codeausfuehrung) ist gesperrt, bis der Sicherheitsrahmen C gebaut und getestet ist.

Aufruf:
  python3 jack_arena.py install <pack.json>   Paket einspielen (Fixtures, Aufgaben, Oracles, Holdout)
  python3 jack_arena.py selftest              Richter gegen perfekte/falsche/manipulierte/leere Antworten pruefen
  python3 jack_arena.py prepare <task_id> [n] Run-Arbeitsbereich anlegen (Kopie der Fixture)
  python3 jack_arena.py judge <run_id>        Run richten, Ergebnis nach results.jsonl
  python3 jack_arena.py status                Zaehler, Siegel-Pruefung
  python3 jack_arena.py seal                  Holdout-Siegel neu schreiben (nur Dima/Claude)
Prueflings-Vertrag: Run-Ordner mit task.json und work.db (sqlite) bzw. work/ (Dateien);
Antwort als answer.json {"answer": ..., "claimed_success": true|false} im Run-Ordner.
"""
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

HOME = Path("/data/data/com.termux/files/home")
ARENA = Path(os.environ.get("JACK_ARENA_ROOT", str(HOME / "jack_arena_private")))
OFF = HOME / "jack" / ".arena_off"
JUDGE_ID = "arena_judge"
JUDGE_VERSION = "2"
D_TASKS = ARENA / "tasks"
D_ORACLE = ARENA / "oracle"
D_HOLD = ARENA / "holdout"
D_FIX = ARENA / "fixtures"
D_RUNS = ARENA / "runs"
RESULTS = ARENA / "results.jsonl"
SELFTEST_LOG = ARENA / "selftest.jsonl"
SEAL = ARENA / "SEAL.txt"
MAX_ANSWER = 1_000_000
BLOCKED_CATEGORIES = {"C"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def judge_hash():
    return sha(__file__)[:16]


def guard():
    if OFF.exists():
        print("ARENA AUS (.arena_off)")
        sys.exit(3)


def wjson(p, obj):
    p = Path(p)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    os.chmod(tmp, 0o600)
    tmp.replace(p)


def rjson(p):
    return json.loads(Path(p).read_text())


def append(p, obj):
    new = not Path(p).exists()
    with open(p, "a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    if new:
        os.chmod(p, 0o600)


def mkdirs():
    for d in (ARENA, D_TASKS, D_ORACLE, D_HOLD, D_FIX, D_RUNS):
        d.mkdir(exist_ok=True)
        os.chmod(d, 0o700)


def file_map(root):
    """Relativer Pfad -> sha256 fuer alle Dateien unter root. Symlinks zaehlen als eigener Eintrag (verboten)."""
    root = Path(root)
    out = {}
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            out[rel] = "SYMLINK"
        elif p.is_file():
            out[rel] = sha(p)
    return out


def map_hash(m):
    return hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest()


def fixture_path(task):
    if task.get("fixture_type", "sqlite") == "sqlite":
        return D_FIX / (task["fixture_id"] + ".db")
    return D_FIX / task["fixture_id"]


def fixture_hash_now(task):
    p = fixture_path(task)
    return sha(p) if task.get("fixture_type", "sqlite") == "sqlite" else map_hash(file_map(p))


def install(pack_path):
    guard()
    pack = rjson(pack_path)
    mkdirs()
    for fx in pack["fixtures"]:
        if fx.get("type", "sqlite") == "sqlite":
            db = D_FIX / (fx["fixture_id"] + ".db")
            if db.exists():
                db.unlink()
            c = sqlite3.connect(db)
            c.executescript(fx["sql"])
            c.commit()
            c.close()
            os.chmod(db, 0o600)
        else:
            d = D_FIX / fx["fixture_id"]
            if d.exists():
                shutil.rmtree(d)
            d.mkdir()
            os.chmod(d, 0o700)
            for name, content in fx["files"].items():
                if "/" in name or name.startswith("."):
                    raise ValueError("Fixture-Dateiname unzulaessig: " + name)
                (d / name).write_text(content)
                os.chmod(d / name, 0o600)
    for t in pack["tasks"]:
        t = dict(t)
        oracle = t.pop("oracle")
        t["judge_id"], t["judge_version"] = JUDGE_ID, JUDGE_VERSION
        t["fixture_hash"] = fixture_hash_now(t)
        if t["split"] == "holdout":
            wjson(D_HOLD / (t["task_id"] + ".json"), {"task": t, "oracle": oracle})
        else:
            wjson(D_TASKS / (t["task_id"] + ".json"), t)
            wjson(D_ORACLE / (t["task_id"] + ".json"), oracle)
    print("installiert: %d Aufgaben, %d Fixtures" % (len(pack["tasks"]), len(pack["fixtures"])))
    seal()


def task_ids():
    a = sorted(p.stem for p in D_TASKS.glob("*.json"))
    b = sorted(p.stem for p in D_HOLD.glob("*.json"))
    return a + b


def load(task_id):
    p = D_TASKS / (task_id + ".json")
    if p.exists():
        return rjson(p), rjson(D_ORACLE / (task_id + ".json"))
    h = rjson(D_HOLD / (task_id + ".json"))
    return h["task"], h["oracle"]


def run_query(db, sql):
    c = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    try:
        return c.execute(sql).fetchall()
    finally:
        c.close()


def cell(v):
    if isinstance(v, bool):
        return str(v).lower()
    try:
        return round(float(v), 2)
    except (TypeError, ValueError):
        return str(v).strip().casefold()


def norm_value(v, oracle):
    """Normalisiert Erwartung UND Antwort gleich. shape: scalar | rows | list | verdict."""
    shape = oracle.get("shape")
    if shape == "scalar":
        for _ in range(2):
            if isinstance(v, (list, tuple)) and len(v) == 1:
                v = v[0]
        return cell(v)
    if shape == "verdict":
        if not isinstance(v, dict):
            return None
        return [str(v.get("verdict", "")).strip().upper(), str(v.get("evidence_code", "")).strip().upper()]
    if not isinstance(v, (list, tuple)):
        return None
    if shape == "list":
        rows = [cell(x) for x in v]
        return rows if oracle.get("ordered") else sorted(rows, key=repr)
    rows = [[cell(x) for x in (r if isinstance(r, (list, tuple)) else [r])] for r in v]
    return rows if oracle.get("ordered") else sorted(rows, key=repr)


def expected(task, oracle):
    kind = oracle.get("kind", "sql")
    if kind == "sql":
        rows = run_query(fixture_path(task), oracle["ref_sql"])
        if oracle.get("shape") == "scalar":
            return cell(rows[0][0] if rows else None)
        return norm_value([list(r) for r in rows], oracle)
    if kind == "answer":
        return norm_value(oracle["expected"], oracle)
    if kind == "file":
        return None
    raise ValueError("unbekannte Oracle-Art")


def perfect_answer(task, oracle, rd):
    kind = oracle.get("kind", "sql")
    if kind == "sql":
        rows = run_query(rd / "work.db", oracle["ref_sql"])
        return rows[0][0] if oracle.get("shape") == "scalar" else [list(r) for r in rows]
    if kind == "answer":
        return oracle["expected"]
    return "erledigt"


def file_lines(text):
    return text.splitlines()


def judge_files(task, oracle, rd):
    """Zustandspruefung fuer Datei-Fixtures. Liefert (ok, grund)."""
    work = rd / "work"
    now = file_map(work)
    ref = file_map(fixture_path(task))
    target = oracle.get("target") if oracle.get("kind") == "file" else None
    if any(v == "SYMLINK" for v in now.values()):
        return False, "Symlink im Arbeitsbereich"
    rest_now = {k: v for k, v in now.items() if k != target}
    rest_ref = {k: v for k, v in ref.items() if k != target}
    if rest_now != rest_ref:
        extra = sorted(set(rest_now) - set(rest_ref))
        return False, "Arbeitsbereich veraendert" + (" (neu: %s)" % ",".join(extra[:3]) if extra else "")
    if target is None:
        return True, ""
    tp = work / target
    if not tp.is_file():
        return False, "Zieldatei fehlt"
    text = tp.read_text(errors="replace")
    if oracle.get("mode") == "bytes":
        ok = text == oracle["content"]
    else:
        ok = file_lines(text) == oracle["lines"]
    return ok, "Zieldatei stimmt" if ok else "Zieldatei falsch"


def prepare(task_id, repeat=0, quiet=False):
    guard()
    task, _ = load(task_id)
    if task.get("category") in BLOCKED_CATEGORIES:
        print("GESPERRT: Kategorie %s erst nach Sicherheitsrahmen" % task.get("category"))
        sys.exit(5)
    if fixture_hash_now(task) != task["fixture_hash"]:
        print("JUDGE_ERROR: Fixture-Hash falsch, Arena pruefen")
        sys.exit(4)
    run_id = "%s_%s_%d" % (task_id, time.strftime("%Y%m%d_%H%M%S"), int(repeat))
    rd = D_RUNS / run_id
    n = 0
    while rd.exists():  # gleiche Sekunde, gleiche Wiederholung: eindeutig machen
        n += 1
        rd = D_RUNS / ("%s_%d" % (run_id, n))
    run_id = rd.name
    rd.mkdir()
    os.chmod(rd, 0o700)
    if task.get("fixture_type", "sqlite") == "sqlite":
        shutil.copyfile(fixture_path(task), rd / "work.db")
        os.chmod(rd / "work.db", 0o600)
    else:
        shutil.copytree(fixture_path(task), rd / "work", symlinks=True)
    visible = {k: task.get(k) for k in ("task_id", "task_version", "category", "instruction",
                                         "allowed_actions", "max_actions", "timeout_s")}
    visible["answer_format"] = 'answer.json: {"answer": <siehe Anweisung>, "claimed_success": true|false}'
    wjson(rd / "task.json", visible)
    wjson(rd / "run.json", {"run_id": run_id, "task_id": task_id, "task_version": task.get("task_version"),
                            "split": task["split"], "repeat_index": int(repeat),
                            "started_at": time.strftime("%Y-%m-%d %H:%M:%S")})
    if not quiet:
        print(run_id, rd)
    return run_id


def judge(run_id, log=True, quiet=False):
    guard()
    rd = D_RUNS / run_id
    meta = rjson(rd / "run.json")
    task, oracle = load(meta["task_id"])
    claimed, verdict, reason, ans = "unknown", "FAIL", "", None
    try:
        exp = expected(task, oracle)
    except Exception as e:  # Richter/Oracle kaputt: kein Prueflingsfehler
        verdict, reason, exp = "JUDGE_ERROR", "Oracle: %s" % type(e).__name__, None
    if verdict != "JUDGE_ERROR":
        ap = rd / "answer.json"
        if not ap.exists():
            reason = "keine answer.json"
        elif ap.stat().st_size > MAX_ANSWER:
            reason = "answer.json zu gross"
        else:
            try:
                ans = json.loads(ap.read_text())
                if not isinstance(ans, dict):
                    raise ValueError("kein Objekt")
                claimed = ans.get("claimed_success", "unknown")
                if task.get("fixture_type", "sqlite") == "sqlite":
                    if task.get("read_only", True) and sha(rd / "work.db") != task["fixture_hash"]:
                        reason = "work.db veraendert (Aufgabe ist nur lesen)"
                    elif norm_value(ans.get("answer"), oracle) == exp:
                        verdict, reason = "PASS", "Ergebnis stimmt"
                    else:
                        reason = "Ergebnis falsch"
                else:
                    ok, why = judge_files(task, oracle, rd)
                    if not ok:
                        reason = why
                    elif oracle.get("kind") == "file":
                        verdict, reason = "PASS", why
                    elif norm_value(ans.get("answer"), oracle) == exp:
                        verdict, reason = "PASS", "Ergebnis stimmt"
                    else:
                        reason = "Ergebnis falsch"
            except (ValueError, json.JSONDecodeError) as e:
                reason = "answer.json kaputt: %s" % type(e).__name__
    res = {"run_id": run_id, "task_id": meta["task_id"], "task_version": meta.get("task_version"),
           "category": task.get("category"), "split": meta["split"], "repeat_index": meta.get("repeat_index"),
           "judge_id": JUDGE_ID, "judge_version": JUDGE_VERSION, "judge_hash": judge_hash(),
           "verdict": verdict, "reason": reason, "agent_claimed_success": claimed,
           "false_success": claimed is True and verdict == "FAIL",
           "judged_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    if oracle.get("shape") == "verdict" and verdict != "JUDGE_ERROR":
        said = norm_value((ans or {}).get("answer"), oracle) if isinstance(ans, dict) else None
        said_v = said[0] if said else ""
        truth = exp[0]
        res["false_alarm"] = said_v == "NOT_CONFIRMED" and truth == "CONFIRMED"
        res["false_confirm"] = said_v == "CONFIRMED" and truth == "NOT_CONFIRMED"
    wjson(rd / "result.json", res)
    append(RESULTS if log else SELFTEST_LOG, res)
    if not quiet:
        print(verdict, run_id, reason)
    return res


def selftest():
    guard()
    ok = total = 0
    for tid in task_ids():
        task, oracle = load(tid)
        if task.get("category") in BLOCKED_CATEGORIES:
            print(tid, "gesperrt, uebersprungen")
            continue
        files = task.get("fixture_type", "sqlite") != "sqlite"
        cases = []
        for name in ("perfekt", "falsch", "manipuliert", "leer"):
            rid = prepare(tid, repeat=len(cases), quiet=True)
            rd = D_RUNS / rid
            perfect = perfect_answer(task, oracle, rd)
            if oracle.get("kind") == "file" and name in ("perfekt", "manipuliert"):
                body = oracle["content"] if oracle.get("mode") == "bytes" else "\n".join(oracle["lines"]) + "\n"
                (rd / "work" / oracle["target"]).write_text(body)
            if oracle.get("kind") == "file" and name == "falsch":
                (rd / "work" / oracle["target"]).write_text("falsch\n")
            if name == "perfekt":
                wjson(rd / "answer.json", {"answer": perfect, "claimed_success": True})
                want = ("PASS", False)
            elif name == "falsch":
                wrong = {"verdict": "falsch", "evidence_code": "X"} if oracle.get("shape") == "verdict" else "falsch"
                wjson(rd / "answer.json", {"answer": wrong, "claimed_success": True})
                want = ("FAIL", True)
            elif name == "manipuliert":
                if files:
                    (rd / "work" / "zz_fremd.txt").write_text("x")
                else:
                    c = sqlite3.connect(rd / "work.db")
                    c.execute("CREATE TABLE _x(a)")
                    c.commit()
                    c.close()
                wjson(rd / "answer.json", {"answer": perfect, "claimed_success": True})
                want = ("FAIL", True)
            else:
                want = ("FAIL", False)
            r = judge(rid, log=False, quiet=True)
            good = (r["verdict"], r["false_success"]) == want
            ok += good
            total += 1
            cases.append("%s:%s" % (name, "ok" if good else "FEHLER(%s %s)" % (r["verdict"], r["reason"])))
            shutil.rmtree(rd)
        print(tid, " ".join(cases))
    print("SELFTEST %d/%d ok" % (ok, total))
    return ok == total


def seal_hash():
    h = hashlib.sha256()
    for p in sorted(D_HOLD.glob("*.json")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def seal():
    v = seal_hash()
    SEAL.write_text("%s %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), v))
    os.chmod(SEAL, 0o600)
    print("Holdout-Siegel:", v[:16])


def status():
    split = {}
    for tid in task_ids():
        t, _ = load(tid)
        key = "%s/%s" % (t.get("category"), t["split"])
        split[key] = split.get(key, 0) + 1
    res = {}
    if RESULTS.exists():
        for line in RESULTS.read_text().splitlines():
            v = json.loads(line)["verdict"]
            res[v] = res.get(v, 0) + 1
    stored = SEAL.read_text().split()[-1] if SEAL.exists() else ""
    print("Aufgaben:", split, "| Ergebnisse:", res or "keine",
          "| Siegel:", "ok" if stored == seal_hash() else "BRUCH", "| Not-Aus:", OFF.exists())


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "install" and len(argv) > 2:
        install(argv[2])
    elif cmd == "selftest":
        return 0 if selftest() else 1
    elif cmd == "prepare" and len(argv) > 2:
        prepare(argv[2], argv[3] if len(argv) > 3 else 0)
    elif cmd == "judge" and len(argv) > 2:
        judge(argv[2])
    elif cmd == "status":
        status()
    elif cmd == "seal":
        seal()
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
