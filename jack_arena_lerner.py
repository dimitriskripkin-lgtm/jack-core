#!/usr/bin/env python3
"""jack_arena_lerner.py - JACK als Lerner (Arena Phase 4, Kap 277).

JACKs Modell liest Fehlschlaege eines UEBUNGS-Satzes und schlaegt genau EINE allgemeine Arbeitsregel vor.
Der Lerner sieht nur sichtbare Aufgabentexte, Richterurteil, Stop-Grund und die letzte sichtbare Testausgabe.
Nie Holdout, nie Oracle, nie versteckte Tests. Die Regel wird nur als Vorschlag abgelegt; uebernommen wird sie erst,
wenn sie eine vorregistrierte Arena-Messung besteht und Dima zustimmt. Kein Code wird veraendert.

Aufruf: python3 jack_arena_lerner.py vorschlag <split> <modell_der_laeufe>
  z.B.  python3 jack_arena_lerner.py vorschlag genC2 gemini-2.5-flash-lite
"""
import json
import os
import re
import sys
import time
from pathlib import Path

os.environ["ARENA_MODEL"] = "gemini-2.5-flash"  # Lerner denkt mit Flash; muss vor dem Runner-Import stehen
sys.path.insert(0, str(Path(__file__).resolve().parent))
import jack_arena as A  # noqa: E402
import jack_arena_runner as R  # noqa: E402

VERSION = "1"
MAX_FAILS = 25
RULE_MAX = 450
RULES_DIR = A.ARENA / "rules"
LOG = A.ARENA / "lerner.jsonl"

SYSTEM = """Du bist der Lerner von JACK. JACK ist ein KI-Pruefling in einer Arena fuer Code-Reparatur: Er liest ein kaputtes
Python-Modul, aendert es und laesst sichtbare pytest-Tests laufen. Danach urteilt ein Richter mit den sichtbaren UND
weiteren versteckten Tests gegen die komplette Aufgabenbeschreibung.
Unten stehen Aufgaben, die JACK nicht geschafft hat, mit Richterurteil und letzter sichtbarer Testausgabe.
Finde das wichtigste wiederkehrende Fehlermuster und schlage GENAU EINE allgemeine Arbeitsregel fuer JACK vor:
Deutsch, Imperativ, hoechstens 400 Zeichen, hilfreich auch fuer kuenftige, andere Aufgaben dieser Art.
Verboten in der Regel: Aufgaben-, Funktions- oder Dateinamen, konkrete Werte oder Beispiele aus diesen Aufgaben.
Antworte nur mit JSON: {"regel": "...", "begruendung": "hoechstens 300 Zeichen", "muster": ["...", "..."]}"""


def failures(split, model):
    if split == "holdout":
        raise SystemExit("Holdout ist fuer den Lerner verboten")
    latest = {}
    for line in R.RUNLOG.read_text().splitlines():
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if r.get("split") == split and r.get("model_id") == model and r.get("agent") == "gemini" and r.get("rules_hash") == R.h16(""):
            latest[r["task_id"]] = r
    out, names = [], set()
    for tid, r in sorted(latest.items()):
        if r["verdict"] == "PASS":
            continue
        task, _oracle = A.load(tid)  # nur sichtbare Felder werden benutzt
        if task.get("split") == "holdout":
            continue
        names |= set(re.findall(r"`([^`]+)`", task["instruction"]))
        last = ""
        tp = A.D_RUNS / r["run_id"] / "transcript.jsonl"
        if tp.exists():
            for l in tp.read_text().splitlines():
                try:
                    d = json.loads(l)
                    if '"pytest_run"' in d.get("req", "") and "resp" in d:
                        last = json.loads(d["resp"]).get("data", {}).get("summary", "")[-500:]
                except (ValueError, AttributeError):
                    pass
        out.append({"aufgabe": task["instruction"][:600], "richter": r.get("judge_reason", ""), "stop": r.get("stop_reason"),
                    "sichtbar_gruen_versteckt_rot": bool(r.get("public_overfit")), "als_erfolg_gemeldet": bool(r.get("agent_claimed_success")),
                    "letzte_sichtbare_testausgabe": last})
    return out[:MAX_FAILS], len(out), names, len(latest)


def check_rule(rule, names):
    if not isinstance(rule, str) or not 20 <= len(rule) <= RULE_MAX:
        return "Regel fehlt oder Laenge nicht 20-%d" % RULE_MAX
    if re.search(r"\b[A-Z]{1,2}K[0-9A-B]\d{2}\b|\b[A-Z]\d{2}\b", rule):
        return "Regel nennt Aufgaben-IDs"
    for n in names:
        if len(n) >= 4 and n.split("(")[0].lower() in rule.lower():
            return "Regel nennt einen Namen aus den Aufgaben: %s" % n[:40]
    if "```" in rule or "\n\n" in rule:
        return "Regel enthaelt Codeblock oder mehrere Absaetze"
    return ""


def vorschlag(split, model):
    fails, nfail, names, ntask = failures(split, model)
    if not fails:
        raise SystemExit("keine Fehlschlaege gefunden")
    import jack_budget
    ok, msg = jack_budget.check_and_count("text")
    if not ok:
        raise SystemExit("jack_budget: %s" % msg)
    deur, _ = R.day_usage()
    if deur >= R.day_eur_cap():
        raise SystemExit("Arena-Tageskosten erreicht")
    payload = {"system_instruction": {"parts": [{"text": SYSTEM}]},
               "contents": [{"role": "user", "parts": [{"text": "FEHLSCHLAEGE (%d von %d Aufgaben, gezeigt %d):\n%s" % (
                   nfail, ntask, len(fails), json.dumps(fails, ensure_ascii=False))}]}],
               "generationConfig": {"temperature": 0.0, "maxOutputTokens": 800, "responseMimeType": "application/json",
                                    "thinkingConfig": {"thinkingBudget": 0}}}
    resp = R.GeminiAgent()._http(payload)
    um = resp.get("usageMetadata") or {}
    tin, tout = um.get("promptTokenCount", 0), um.get("candidatesTokenCount", 0)
    eur = R.cost_eur(tin, tout)
    ts = time.strftime("%Y%m%d_%H%M%S")
    A.append(R.COSTS, {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "day": R.today(), "run_id": "LERNER_" + ts,
                       "model": R.MODEL_ID, "in": tin, "out": tout, "eur": round(eur, 6), "price": R.PRICE["version"]})
    try:
        jack_budget.add_tokens(tin + tout)
    except Exception:
        pass
    text = "".join(p.get("text", "") for p in resp["candidates"][0]["content"]["parts"])
    try:
        d = json.loads(text)
    except ValueError:
        d = {"regel": None, "roh": text[:500]}
    why = check_rule(d.get("regel"), names)
    rec = {"ts": ts, "lerner_version": VERSION, "split": split, "modell_laeufe": model, "lerner_modell": R.MODEL_ID,
           "fehlschlaege": nfail, "aufgaben": ntask, "gezeigt": len(fails), "regel": d.get("regel"),
           "begruendung": d.get("begruendung"), "muster": d.get("muster"), "tokens": [tin, tout], "eur": round(eur, 6),
           "gueltig": not why, "grund": why}
    if not why:
        RULES_DIR.mkdir(exist_ok=True)
        p = RULES_DIR / ("jack_regel_%s.txt" % ts)
        p.write_text(d["regel"].strip() + "\n", encoding="utf-8")
        os.chmod(p, 0o600)
        rec["datei"] = str(p.name)
        rec["rules_hash"] = R.h16(d["regel"].strip())
    A.append(LOG, rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return rec


def main(argv):
    if len(argv) >= 4 and argv[1] == "vorschlag":
        vorschlag(argv[2], argv[3])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
