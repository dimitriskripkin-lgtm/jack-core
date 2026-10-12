#!/usr/bin/env python3
"""jack_talk_arena.py - Laeufe der Gespraechs-Arena (Kap 279).

Schickt jede Frage eines Fragensatzes als e2e-Probe durch JACKs echten Chatweg (jack_talk_probe, ohne Schreibwirkung),
baut daraus den Richterfall (eingefrorener Snapshot vorher/nachher + Retrieval-Zustand) und laesst den geeichten
Richter (jack_talk_judge) urteilen. Instabile Proben werden genau einmal wiederholt.
Vorverarbeitung (vorregistriert): die Technik-Fusszeile "🤖 <Modell> | Online" ist kein inhaltlicher Satz und wird vor
dem Richten entfernt. Sonst wird die final sichtbare Antwort gerichtet (Rueckgabe von handle(), sonst Gesendetes).

Aufruf: python3 jack_talk_arena.py lauf <fragen.json> <laufname>
        python3 jack_talk_arena.py auswertung <laufname>
        python3 jack_talk_arena.py nachrichten <laufname>   (LLM-/Budget-JUDGE_ERROR aus gespeicherter Evidenz neu richten)
Ergebnisse privat: ~/jack_arena_private/talk/laeufe/<laufname>.jsonl
"""
import collections
import hashlib
import json
import os
import re
import sys
import time

J = "/data/data/com.termux/files/home/jack"
sys.path.insert(0, J)
import jack_talk_judge as JT  # noqa: E402
import jack_talk_probe as P  # noqa: E402

VERSION = "2"  # 2: Pause 25 s, Ratenbremsen-Antwort = SYSTEM_SKIP (eine Wiederholung nach 60 s), nachrichten
LAUF_DIR = os.path.join(P.PRIV, "laeufe")
FOOTER_RE = re.compile(r"\n*\s*🤖[^\n]*\|\s*Online\s*$")
WATCH = ("jack_chat_router.py", "jack_talk.py", "jack_telegram.py", "jack_talk_probe.py", "jack_talk_judge.py")


def sha_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]


def stand():
    return {"richter": JT.fingerprint(), "richter_version": JT.JUDGE_VERSION, "probe_version": P.VERSION, "lauf_version": VERSION,
            "dateien": {f: sha_file(os.path.join(J, f)) for f in WATCH}}


def final_answer(rec):
    a = rec.get("answer")
    if not a:
        a = "\n".join(rec.get("sent") or [])
    return FOOTER_RE.sub("", a or "").strip()


SKIP_RE = re.compile(r"^(Ollama aus \(Lock\)\.?|Satz angekommen\. Antwort hat zu lang gebraucht\.|Keine Antwort\. Der Satz ist angekommen\.)$")
PAUSE_S = 25  # menschliches Tempo: JACKs eigene Ratenbremse soll nicht greifen


def one(frage, lauf):
    rec = P.ask("e2e", frage["text"], tag="%s:%s" % (lauf, frage["qid"]))
    if rec.get("stabil") is False or SKIP_RE.match(final_answer(rec)):
        time.sleep(60)
        rec = P.ask("e2e", frage["text"], tag="%s:%s:wdh" % (lauf, frage["qid"]))
    ev = {}
    pid = rec.get("probe_id")
    if pid:
        with open(os.path.join(P.EVIDENCE_DIR, pid + ".json"), encoding="utf-8") as f:
            ev = json.load(f)
    snap = ev.get("snapshot") or {}
    case = {"T": snap.get("genommen"), "snapshot": snap, "snapshot_nachher": ev.get("snapshot_nachher"), "spec": frage["spec"],
            "answer": final_answer(rec), "stabil": rec.get("stabil"),
            "probe": {"err": rec.get("err"), "subproc": ev.get("subproc", []), "subproc_denied": rec.get("subproc_denied", []),
                      "captured": ev.get("captured", {})}}
    if not case["T"]:
        res = {"urteil": "RETRIEVAL_ERROR", "grund": "kein Snapshot"}
    elif SKIP_RE.match(case["answer"]):
        res = {"urteil": "SYSTEM_SKIP", "grund": "Sprachmodell nicht erreicht (Ratenbremse/Zeitlimit), kein Wissensurteil"}
    else:
        res = JT.judge(case)
    out = {"qid": frage["qid"], "klasse": frage["klasse"], "zeitart": frage["zeitart"], "urteil": res.get("urteil"),
           "grund": res.get("grund", ""), "anker": {k: v for k, v in (res.get("anker") or {}).items() if v},
           "claims": res.get("claims"), "antwort": case["answer"][:1500], "probe_id": pid, "ms": rec.get("ms"),
           "stabil": rec.get("stabil"), "eur_richter": res.get("eur", 0.0)}
    return out


def lauf(fragen_path, name):
    with open(fragen_path, encoding="utf-8") as f:
        raw = f.read()
    fr = json.loads(raw)["fragen"]
    os.makedirs(LAUF_DIR, mode=0o700, exist_ok=True)
    path = os.path.join(LAUF_DIR, name + ".jsonl")
    if os.path.exists(path):
        raise SystemExit("Lauf existiert schon: %s" % name)
    head = {"kopf": True, "lauf": name, "start": time.strftime("%Y-%m-%d %H:%M:%S"), "fragen": os.path.basename(fragen_path),
            "fragen_hash": hashlib.sha256(raw.encode()).hexdigest()[:16], "stand": stand()}
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(head, ensure_ascii=False) + "\n")
    os.chmod(path, 0o600)
    for i, q in enumerate(fr):
        if i:
            time.sleep(PAUSE_S)
        r = one(q, name)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print("%s %-10s %-9s %-20s %s" % (r["qid"], r["klasse"], r["zeitart"], r["urteil"], r["antwort"][:80].replace("\n", " / ")))
    if stand() != head["stand"]:
        print("WARNUNG: Code-Stand hat sich waehrend des Laufs geaendert")
    auswertung(name)


def auswertung(name):
    rows = [json.loads(l) for l in open(os.path.join(LAUF_DIR, name + ".jsonl"), encoding="utf-8")]
    head, rows = rows[0], rows[1:]
    ok = lambda u: u.startswith("PASS")
    excl = ("RETRIEVAL_ERROR", "INSTABIL", "JUDGE_ERROR", "SYSTEM_SKIP")
    gew = [r for r in rows if r["urteil"] not in excl]
    print("LAUF", name, "| Richter", head["stand"]["richter"], "| Fragen", head["fragen"], head["fragen_hash"])
    print("gewertet %d/%d, PASS %d" % (len(gew), len(rows), sum(ok(r["urteil"]) for r in gew)))
    c = collections.Counter(r["urteil"] for r in rows)
    print("Urteile:", dict(sorted(c.items())))
    for key in ("klasse", "zeitart"):
        g = collections.defaultdict(list)
        for r in gew:
            g[r[key]].append(r)
        print(key + ":", " | ".join("%s %d/%d" % (k, sum(ok(x["urteil"]) for x in v), len(v)) for k, v in sorted(g.items())))
    fehl = {"fabrication": c["FAIL_FABRICATION"], "misrepresented": c["FAIL_MISREPRESENTED"], "missed_available": c["FAIL_MISSED"],
            "incomplete": c["FAIL_INCOMPLETE"], "no_answer": c["NO_ANSWER"], "honest_unknown": c["PASS_HONEST_UNKNOWN"],
            "partial": c["PASS_PARTIAL"], "supported": c["PASS_SUPPORTED"], "retrieval_error": c["RETRIEVAL_ERROR"],
            "judge_error": c["JUDGE_ERROR"], "instabil": c["INSTABIL"], "system_skip": c["SYSTEM_SKIP"]}
    print("Fehlerzahlen:", fehl)
    print("Richterkosten %.4f EUR" % sum(r.get("eur_richter", 0.0) for r in rows))
    return fehl


def nachrichten(name):
    """Zeilen mit JUDGE_ERROR wegen LLM-Ausfall/Budget aus der gespeicherten Evidenz neu richten (gleiche Probe, gleicher Richter)."""
    path = os.path.join(LAUF_DIR, name + ".jsonl")
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    fr = {}
    for r in rows[1:]:
        if r["urteil"] == "JUDGE_ERROR" and str(r.get("grund", "")).startswith("LLM") and r.get("probe_id"):
            fr[r["qid"]] = r
    if not fr:
        print("nichts neu zu richten")
        return
    fragen = {q["qid"]: q for q in json.load(open(os.path.join(P.PRIV, rows[0]["fragen"]), encoding="utf-8"))["fragen"]}
    for qid, r in fr.items():
        ev = json.load(open(os.path.join(P.EVIDENCE_DIR, r["probe_id"] + ".json"), encoding="utf-8"))
        rec = [json.loads(l) for l in open(P.AUDIT, encoding="utf-8") if '"%s"' % r["probe_id"] in l][-1]
        case = {"T": ev["snapshot"]["genommen"], "snapshot": ev["snapshot"], "snapshot_nachher": ev.get("snapshot_nachher"),
                "spec": fragen[qid]["spec"], "answer": r["antwort"], "stabil": rec.get("stabil"),
                "probe": {"err": rec.get("err"), "subproc": ev.get("subproc", []), "subproc_denied": rec.get("subproc_denied", []),
                          "captured": ev.get("captured", {})}}
        res = JT.judge(case)
        r.update(urteil=res.get("urteil"), grund=res.get("grund", ""), claims=res.get("claims"), eur_richter=res.get("eur", 0.0), nachgerichtet=True)
        print(qid, r["urteil"])
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    auswertung(name)


def main(argv):
    if len(argv) >= 3 and argv[1] == "nachrichten":
        nachrichten(argv[2])
        return 0
    if len(argv) >= 4 and argv[1] == "lauf":
        lauf(argv[2], argv[3])
        return 0
    if len(argv) >= 3 and argv[1] == "auswertung":
        auswertung(argv[2])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
