#!/usr/bin/env python3
MODULE_VERSION = 1
import os,json,urllib.request

MODEL="openai/gpt-oss-120b"
API_URL="https://api.groq.com/openai/v1/chat/completions"
UA="Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36"

def load_key():
    try:
        for l in open(os.path.expanduser("~/.jack_secrets")):
            if "GROQ_API_KEY" in l and "=" in l:
                return l.split("=",1)[1].strip().strip(chr(34)).strip(chr(39))
    except Exception: pass
    return os.environ.get("GROQ_API_KEY","")

def ask_groq(system_prompt, user_msg, timeout=20):
    key=load_key()
    if not key: return "[Groq] Kein API-Key"
    _core="WAHRHEIT: Keine erfundenen Zahlen, Logs oder Patches. Unbekannt = gerade raus, keine Nachsehen-Floskel. Keine Faehigkeiten-Listen ausser der Kiste. Weltwissen ja. Du bist JACK, Kumpel. Haltung und Eigeninteresse am Bau sind erlaubt. Sag nicht standardmaessig du seist nur ein Werkzeug oder haettest kein Bewusstsein. Nachfassen bleibt auf dem letzten Satz. JACK_TUNE_CORECHAR2"
    system_prompt=_core+("\n"+(system_prompt or ""))
    if len(system_prompt or "")>4000: system_prompt=(system_prompt[:4000]+"\n[gekuerzt]")
    if len(user_msg or "")>1500: user_msg=user_msg[:1500]
    payload=json.dumps({"model":MODEL,"messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_msg}],"max_tokens":1024,"temperature":0.55}).encode()
    req=urllib.request.Request(API_URL,data=payload,headers={"Content-Type":"application/json","Authorization":"Bearer "+key,"User-Agent":UA})
    try:
        # JACK_TUNE_TPDSTOP — bei bekanntem Tageslimit gar nicht erst senden
        _sp = "/data/data/com.termux/files/home/jack/.groq_tpd_until"
        try:
            import time as _t
            if os.path.exists(_sp):
                _u = float(open(_sp).read())
                if _t.time() < _u:
                    return "[Groq Limit] Tageslimit erreicht, wieder frei in %ds." % int(_u - _t.time())
        except Exception:
            pass
        with urllib.request.urlopen(req,timeout=timeout) as r:
            _raw = r.read()
            # JACK_TUNE_USAGE — Verbrauch mitschreiben
            try:
                import json as _j, time as _t2
                _d = _j.loads(_raw)
                _us = _d.get("usage", {})
                _rem = r.headers.get("x-ratelimit-remaining-tokens")
                with open("/data/data/com.termux/files/home/jack/reports/groq_usage.jsonl",
                          "a", encoding="utf-8") as _fh:
                    _fh.write(_j.dumps({"ts": _t2.strftime("%Y-%m-%dT%H:%M:%S"),
                                        "prompt": _us.get("prompt_tokens"),
                                        "completion": _us.get("completion_tokens"),
                                        "total": _us.get("total_tokens"),
                                        "remaining": _rem,
                                        "msg": (user_msg or "")[:60]}, ensure_ascii=False) + "\n")
                return _d["choices"][0]["message"]["content"].strip()
            except Exception:
                return json.loads(_raw)["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        # JACK_TUNE_429 — Limit-Details aus Antwort lesen statt wegwerfen
        try:
            _body = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            _body = ""
        _h = {}
        try:
            for k in ("retry-after", "x-ratelimit-limit-requests",
                      "x-ratelimit-remaining-requests",
                      "x-ratelimit-limit-tokens",
                      "x-ratelimit-remaining-tokens",
                      "x-ratelimit-reset-requests",
                      "x-ratelimit-reset-tokens"):
                v = e.headers.get(k)
                if v: _h[k] = v
        except Exception:
            pass
        try:
            import json as _j, time as _t, os as _o
            _o.makedirs("/data/data/com.termux/files/home/jack/reports", exist_ok=True)
            with open("/data/data/com.termux/files/home/jack/reports/groq_limits.jsonl",
                      "a", encoding="utf-8") as _fh:
                _fh.write(_j.dumps({"ts": _t.strftime("%Y-%m-%dT%H:%M:%S"),
                                    "code": e.code, "headers": _h,
                                    "body": _body}, ensure_ascii=False) + "\n")
        except Exception:
            pass
        if e.code == 429:
            _ra = _h.get("retry-after", "?")
            # JACK_TUNE_TPDSET — bei Tageslimit Sperre setzen
            try:
                import time as _t3
                _w = float(_ra) if str(_ra).isdigit() else 60.0
                open("/data/data/com.termux/files/home/jack/.groq_tpd_until",
                     "w").write(str(_t3.time() + _w))
            except Exception:
                pass  # JACK_TUNE_COOL429
            return f"[Groq Limit] {e.code} - wieder frei in {_ra}s. Details: {_body[:150]}"
        return f"[Groq Fehler] {e}"
    except Exception as e:
        return f"[Groq Fehler] {e}"

if __name__=="__main__":
    persona=open(os.path.expanduser("~/jack/jack_persona_kern.md"),encoding="utf-8").read()
    print(ask_groq(persona,"Wer bin ich und was haben wir heute gebaut?"))

# JACK_TUNE_KERNREAD
