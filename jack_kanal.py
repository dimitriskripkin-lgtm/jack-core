#!/usr/bin/env python3
"""JACK_TUNE_KANAL: Briefkasten + Reservierung zwischen den KIs (claude, grok, gemini, dima).
Asynchron: jeder holt Post bei seinem naechsten Zug (ap_lese). Rundengrenze und STOP-Schalter gegen Endlos-Ping-Pong."""
import os, re, json, time, fcntl
import jack_arbeitsplatz as _ap

AP = _ap.AP
J = _ap.J
KANAL = AP + "/gemeinsam/kanal.jsonl"
CLAIMS = AP + "/gemeinsam/claims.json"
TYPEN = ("frage", "aufgabe", "antwort", "info", "entscheidung", "fertig")
MAXKETTE = 10      # max. KI-Nachrichten in Folge ohne Wort von Dima
MAXTEXT = 2000
CLAIM_TTL = 3600
OKZIEL = re.compile(r"^[A-Za-z0-9_.\-/]{1,80}$")

def _wer(w):
    w = str(w or "").strip().lower()
    return w if w in _ap.WER else None

def _alle():
    out = []
    try:
        with open(KANAL, encoding="utf-8") as f:
            for l in f:
                try: out.append(json.loads(l))
                except Exception: pass
    except Exception:
        pass
    return out

def post(wer, an, typ, text, re_id=0):
    try:
        wer = _wer(wer)
        an = str(an or "").strip().lower()
        typ = str(typ or "").strip().lower()
        text = str(text or "").strip()
        if not wer: return _ap._err("wer ungueltig")
        if an != "alle" and an not in _ap.WER: return _ap._err("an: claude|grok|gemini|dima|alle")
        if typ not in TYPEN: return _ap._err("typ: " + "|".join(TYPEN))
        if not text: return _ap._err("text leer")
        if len(text) > MAXTEXT: return _ap._err("text zu lang (max %d Zeichen)" % MAXTEXT)
        if typ == "entscheidung" and wer not in ("claude", "dima"):
            return _ap._err("Entscheidungen nur Claude oder Dima. Schreibe typ=frage an claude.")
        if os.path.exists(J + "/missions/STOP"):
            return _ap._err("NOTAUS: missions/STOP existiert. Kein Kanalverkehr bis Dima es loescht.")
        os.makedirs(os.path.dirname(KANAL), exist_ok=True)
        with open(KANAL, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            msgs = []
            for l in f:
                try: msgs.append(json.loads(l))
                except Exception: pass
            kette = 0
            for m in reversed(msgs):
                if m.get("von") == "dima": break
                kette += 1
            if wer != "dima" and kette >= MAXKETTE:
                return _ap._err("RUNDENGRENZE: %d KI-Nachrichten ohne Dima. Stopp, warte auf Dima (er schreibt typ=info an alle)." % kette)
            nid = (msgs[-1].get("id", len(msgs)) + 1) if msgs else 1
            rec = {"id": nid, "ts": _ap._now(), "von": wer, "an": an, "typ": typ, "re": int(re_id or 0), "text": text}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
        _ap._audit(wer, "gemeinsam/kanal.jsonl", "post", len(text))
        return json.dumps({"ok": True, "id": nid, "kette": (0 if wer == "dima" else kette + 1), "limit": MAXKETTE}, ensure_ascii=False)
    except Exception as e:
        return _ap._err("Fehler: " + str(e)[:150])

def _cursor_pfad(wer):
    return AP + "/BUEROS/%s/kanal_cursor.json" % wer

def _cursor(wer):
    try: return int(json.load(open(_cursor_pfad(wer)))["seit"])
    except Exception: return 0

def ungelesen(wer):
    wer = _wer(wer)
    if not wer: return 0
    c = _cursor(wer)
    return sum(1 for m in _alle() if m.get("id", 0) > c and m.get("von") != wer and m.get("an") in (wer, "alle"))

def lese(wer, seit_id=-1, markieren=True):
    """Neue Post fuer wer. seit_id<0: ab eigenem Cursor. Setzt Cursor (markieren)."""
    try:
        wer = _wer(wer)
        if not wer: return _ap._err("wer ungueltig")
        c = _cursor(wer) if int(seit_id) < 0 else int(seit_id)
        msgs = _alle()
        neu = [m for m in msgs if m.get("id", 0) > c and m.get("von") != wer and m.get("an") in (wer, "alle")]
        letzte = msgs[-1].get("id", 0) if msgs else 0
        if markieren and int(seit_id) < 0 and os.path.isdir(AP + "/BUEROS/" + wer):
            with open(_cursor_pfad(wer), "w") as f:
                json.dump({"seit": letzte, "ts": _ap._now()}, f)
        kette = 0
        for m in reversed(msgs):
            if m.get("von") == "dima": break
            kette += 1
        return json.dumps({"ok": True, "neu": neu[-20:], "anzahl_neu": len(neu), "letzte_id": letzte,
                           "kette": kette, "limit": MAXKETTE, "claims": claims_liste()}, ensure_ascii=False)
    except Exception as e:
        return _ap._err("Fehler: " + str(e)[:150])

def _claims_laden():
    try: d = json.load(open(CLAIMS))
    except Exception: d = {}
    now = time.time()
    return {k: v for k, v in d.items() if now - v.get("t", 0) < CLAIM_TTL}

def claims_liste():
    return {k: "%s (seit %s)" % (v["wer"], v["ts"]) for k, v in _claims_laden().items()}

def claim(wer, ziel, aktion="claim"):
    """Reservierung eines Moduls/einer Aufgabe. claim|frei|verlaengern. TTL 60 Min."""
    try:
        wer = _wer(wer); ziel = str(ziel or "").strip()
        if not wer: return _ap._err("wer ungueltig")
        if not OKZIEL.match(ziel): return _ap._err("ziel ungueltig (z.B. jack_telegram.py)")
        if aktion not in ("claim", "frei", "verlaengern"): return _ap._err("aktion: claim|frei|verlaengern")
        os.makedirs(os.path.dirname(CLAIMS), exist_ok=True)
        with open(CLAIMS + ".lock", "a+") as lk:
            fcntl.flock(lk, fcntl.LOCK_EX)
            d = _claims_laden()
            cur = d.get(ziel)
            if aktion == "frei":
                if cur and cur["wer"] != wer and wer != "dima":
                    return _ap._err("gehoert %s" % cur["wer"])
                d.pop(ziel, None); res = "frei"
            else:
                if cur and cur["wer"] != wer:
                    return _ap._err("BELEGT von %s seit %s. Nicht anfassen, im Kanal fragen." % (cur["wer"], cur["ts"]))
                d[ziel] = {"wer": wer, "ts": _ap._now(), "t": time.time()}; res = "reserviert (60 Min)"
            with open(CLAIMS, "w") as f: json.dump(d, f, ensure_ascii=False)
        _ap._audit(wer, ziel, "claim:" + aktion, 0)
        return json.dumps({"ok": True, "ziel": ziel, "status": res}, ensure_ascii=False)
    except Exception as e:
        return _ap._err("Fehler: " + str(e)[:150])
