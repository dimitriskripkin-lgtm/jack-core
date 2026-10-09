#!/usr/bin/env python3
"""JACK_TUNE_ARBEITSPLATZ: gemeinsamer Arbeitsplatz fuer alle KIs (claude, grok, gemini).
Ordner ARBEITSPLATZ/: gemeinsam/ (eine Wahrheit, alle lesen/schreiben) und BUEROS/<wer>/ (eigene Notizen).
Schreiben nur hier, nur kleine Textdateien, nie ausserhalb. Fail-sicher: Fehler werden als JSON gemeldet."""
import os, re, json, time, shutil

J = os.environ.get("JACK_HB_HOME", "/data/data/com.termux/files/home/jack")
AP = J + "/ARBEITSPLATZ"
WER = ("claude", "grok", "gemini", "chatgpt", "dima")  # JACK_TUNE_CHATGPT
OKNAME = re.compile(r"^[A-Za-z0-9_.-]{1,60}\.(md|jsonl|json|txt)$")
OKDIR = re.compile(r"^[A-Za-z0-9_-]{1,40}$")
MAXCALL = 8000
MAXFILE = 200000

def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def _rd(p, n=None, tail=False):
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            t = f.read()
    except Exception:
        return ""
    if n is None:
        return t
    return t[-n:] if tail else t[:n]

def _err(msg, **kw):
    d = {"ok": False, "error": msg}
    d.update(kw)
    return json.dumps(d, ensure_ascii=False)

def _safe(rel):
    rel = str(rel or "").strip().lstrip("/")
    parts = rel.split("/")
    if len(parts) < 2 or len(parts) > 3 or any(not p or p in (".", "..") for p in parts):
        return None
    if parts[0] not in ("gemeinsam", "BUEROS"):
        return None
    if parts[0] == "BUEROS" and len(parts) != 3:
        return None
    if not OKNAME.match(parts[-1]) or any(not OKDIR.match(p) for p in parts[:-1]):
        return None
    full = os.path.realpath(os.path.join(AP, rel))
    if not full.startswith(os.path.realpath(AP) + os.sep):
        return None
    return full

def _audit(wer, rel, modus, n):
    try:
        os.makedirs(AP, exist_ok=True)
        with open(AP + "/audit.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": _now(), "wer": wer, "pfad": rel, "modus": modus, "bytes": n}, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _darf(wer, rel, modus):
    parts = rel.strip("/").split("/")
    if parts[0] == "BUEROS":
        if parts[1] == wer or wer == "dima":
            return True
        return parts[2] == "eingang.md" and modus == "anhaengen"
    if modus == "ersetzen":
        n = parts[-1]
        return not (n.startswith("entscheidungen") or n.startswith("00_"))
    return True

def schreiben(wer, pfad, text, modus="anhaengen"):
    try:
        wer = str(wer or "").strip().lower()
        if wer not in WER:
            return _err("wer muss einer von %s sein" % (WER,))
        if modus not in ("anhaengen", "ersetzen"):
            return _err("modus: anhaengen oder ersetzen")
        text = str(text or "")
        if not text.strip():
            return _err("text leer")
        if len(text.encode("utf-8")) > MAXCALL:
            return _err("text zu gross (max %d Bytes pro Aufruf), teile in mehrere Aufrufe" % MAXCALL)
        full = _safe(pfad)
        if not full:
            return _err("pfad ungueltig. Erlaubt: gemeinsam/<datei> oder BUEROS/<wer>/<datei>, Endung md/jsonl/json/txt", beispiel="BUEROS/claude/offen.md")
        rel = os.path.relpath(full, os.path.realpath(AP))
        if not _darf(wer, rel, modus):
            return _err("nicht erlaubt: fremdes Buero nur per anhaengen an eingang.md; entscheidungen*.md und 00_*.md in gemeinsam/ nie ersetzen, nur anhaengen")
        os.makedirs(os.path.dirname(full), exist_ok=True)
        exists = os.path.isfile(full)
        if modus == "ersetzen" and exists:
            arch = AP + "/gemeinsam/archiv"
            os.makedirs(arch, exist_ok=True)
            shutil.copy2(full, arch + "/" + os.path.basename(full) + "." + time.strftime("%Y%m%d_%H%M%S") + ".bak.txt")
        if full.endswith(".json") and modus == "ersetzen":
            try:
                json.loads(text)
            except Exception as e:
                return _err("kein gueltiges JSON: " + str(e)[:80])
        if full.endswith(".jsonl"):
            out = json.dumps({"ts": _now(), "wer": wer, "text": text}, ensure_ascii=False) + "\n"
        elif modus == "anhaengen" and exists and full.endswith(".md"):
            out = "\n\n### %s %s\n%s\n" % (_now(), wer, text.rstrip())
        else:
            out = text if text.endswith("\n") else text + "\n"
        if modus == "anhaengen" and exists and os.path.getsize(full) + len(out.encode("utf-8")) > MAXFILE:
            return _err("Datei waere ueber %d Bytes. Lege eine neue Datei an oder archiviere." % MAXFILE)
        with open(full, "a" if modus == "anhaengen" else "w", encoding="utf-8") as f:
            f.write(out)
        _audit(wer, rel, modus, len(out.encode("utf-8")))
        return json.dumps({"ok": True, "pfad": rel, "modus": modus, "bytes": len(out.encode("utf-8")), "neu": not exists}, ensure_ascii=False)
    except Exception as e:
        return _err("Fehler: " + str(e)[:150])

def journal(wer, text):
    return schreiben(wer, "BUEROS/%s/journal.jsonl" % str(wer or "").strip().lower(), text, "anhaengen")

def _liste(sub):
    d = os.path.join(AP, sub)
    out = []
    try:
        for n in sorted(os.listdir(d)):
            p = os.path.join(d, n)
            if os.path.isfile(p):
                out.append("%s (%d B, %s)" % (n, os.path.getsize(p), time.strftime("%d.%m. %H:%M", time.localtime(os.path.getmtime(p)))))
    except Exception:
        pass
    return out

def buero(wer):
    try:
        wer = str(wer or "").strip().lower()
        if wer not in WER:
            return _err("wer muss einer von %s sein" % (WER,))
        mine = "BUEROS/" + wer
        d = {
            "wer": wer,
            "arbeitsplatz": AP,
            "regeln": _rd(AP + "/gemeinsam/00_LIES_MICH.md", 1800),
            "mein_buero_vorhanden": os.path.isdir(os.path.join(AP, mine)),
            "buero_regeln": _rd(AP + "/%s/00_BUERO.md" % mine, 1200),
            "offen": _rd(AP + "/%s/offen.md" % mine, 3000),
            "eingang": _rd(AP + "/%s/eingang.md" % mine, 1500, tail=True),
            "journal_letzte": [l[:300] for l in _rd(AP + "/%s/journal.jsonl" % mine, 4000, tail=True).strip().splitlines()[-8:]],
            "roadmap_kopf": _rd(AP + "/gemeinsam/roadmap.md", 1500),
            "dateien_gemeinsam": _liste("gemeinsam"),
            "dateien_mein_buero": _liste(mine),
            "andere_bueros": [n for n in sorted(os.listdir(AP + "/BUEROS")) if n != wer] if os.path.isdir(AP + "/BUEROS") else [],
        }
        if not d["mein_buero_vorhanden"]:
            d["hinweis"] = "Dein Buero fehlt noch. Lege es mit ap_notiz an: BUEROS/%s/00_BUERO.md, offen.md, notizen.md (Muster: Buero von claude lesen)." % wer
        return json.dumps(d, ensure_ascii=False)
    except Exception as e:
        return _err("Fehler: " + str(e)[:150])
