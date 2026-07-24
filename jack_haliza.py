#!/usr/bin/env python3
"""JACK Haliza - Halluzinations-Guard vor jedem Code-Patch.
Duenn gebaut: nutzt jack_approval (Sandbox), py_compile (Syntax),
jack_gemini_bridge (Semantik). Eigen: nur Rate-Limit + Orchestrierung.
Fail-closed: Bei Zweifel wird blockiert, nie durchgewunken."""
import os, json, time, subprocess

H = os.path.expanduser("~/jack")
RATE_FILE = os.path.join(H, ".haliza_rate")
RATE_MAX = 10
RATE_FENSTER = 3600
TMP = os.path.join(H, ".haliza_check.py")

def _log(tag, msg):
    try:
        import jack_log
        jack_log.log_decision(tag, str(msg)[:120])
    except Exception:
        pass

def rate_ok():
    now = time.time()
    try:
        stamps = json.load(open(RATE_FILE))
    except Exception:
        stamps = []
    stamps = [t for t in stamps if now - t < RATE_FENSTER]
    if len(stamps) >= RATE_MAX:
        return False, "Rate-Limit " + str(RATE_MAX) + "/h erreicht"
    stamps.append(now)
    try:
        json.dump(stamps, open(RATE_FILE, "w"))
    except Exception:
        pass
    return True, "OK"

def sandbox_ok(datei):
    try:
        import jack_approval
        return jack_approval.is_safe_path(datei)
    except Exception as e:
        return False, "Approval-Modul nicht ladbar: " + str(e)[:60]

def syntax_ok(code):
    try:
        open(TMP, "w").write(code)
        r = subprocess.run(["python3", "-m", "py_compile", TMP],
                           capture_output=True, text=True, timeout=20)
        try:
            os.unlink(TMP)
        except Exception:
            pass
        if r.returncode == 0:
            return True, "Syntax OK"
        return False, r.stderr.strip()[:200]
    except Exception as e:
        return False, "py_compile Fehler: " + str(e)[:80]

def semantik_ok(alt, neu, beschreibung):
    ok, grund = rate_ok()
    if not ok:
        return False, "hoch", grund
    prompt = (
        "Du bist Code-Reviewer fuer ein Python-Projekt auf Android/Termux."
        + chr(10) + "Antworte NUR mit JSON, kein Text davor oder danach:"
        + chr(10) + '{"ok": true, "risiko": "niedrig", "grund": "kurz"}'
        + chr(10) + "ok=false wenn der neue Code Bugs hat."
        + chr(10) + "Pruefe: UnboundLocalError, falsche Variablen-Scopes,"
        + chr(10) + "fehlende Imports, kaputte Anker, Sicherheitsluecken."
        + chr(10) + chr(10) + "AENDERUNG: " + str(beschreibung)[:300]
        + chr(10) + chr(10) + "ALT:" + chr(10) + str(alt)[:1200]
        + chr(10) + chr(10) + "NEU:" + chr(10) + str(neu)[:1200]
    )
    try:
        import jack_gemini_bridge
        antwort = jack_gemini_bridge.ask_gemini(prompt, None)
    except Exception as e:
        return False, "unbekannt", "Gemini nicht erreichbar: " + str(e)[:80]
    txt = str(antwort).strip()
    if "```" in txt:
        teile = txt.split("```")
        if len(teile) > 1:
            txt = teile[1].replace("json", "", 1).strip()
    try:
        d = json.loads(txt)
    except Exception:
        return False, "unbekannt", "Gemini-Antwort kein JSON: " + txt[:100]
    return bool(d.get("ok")), str(d.get("risiko", "unbekannt")), str(d.get("grund", ""))

def pruefe(datei, alt, neu, beschreibung, mit_gemini=True):
    """Haupteinstieg. Gibt IMMER dict zurueck:
    {ok, stufe, risiko, grund}. ok=True heisst: bereit fuer Dimas Freigabe."""
    _log("HALIZA-START", str(datei) + ": " + str(beschreibung)[:60])
    ok, grund = sandbox_ok(datei)
    if not ok:
        _log("HALIZA-SANDBOX-STOP", grund)
        return {"ok": False, "stufe": "sandbox", "risiko": "hoch", "grund": str(grund)}
    ok, grund = syntax_ok(neu)
    if not ok:
        _log("HALIZA-SYNTAX-STOP", grund)
        return {"ok": False, "stufe": "syntax", "risiko": "hoch", "grund": grund}
    if not mit_gemini:
        return {"ok": True, "stufe": "syntax", "risiko": "ungeprueft",
                "grund": "Syntax+Sandbox OK, Semantik uebersprungen"}
    ok, risiko, grund = semantik_ok(alt, neu, beschreibung)
    if not ok:
        _log("HALIZA-SEMANTIK-STOP", grund)
        return {"ok": False, "stufe": "semantik", "risiko": risiko, "grund": grund}
    _log("HALIZA-BEREIT", "Risiko " + risiko)
    return {"ok": True, "stufe": "bereit", "risiko": risiko, "grund": grund}

def selbsttest():
    print("=== HALIZA SELBSTTEST (ohne API-Kosten) ===")
    gut = "def add(a, b):" + chr(10) + "    return a + b"
    kaputt = "def add(a, b:" + chr(10) + "    return a + b"
    scope = "def f(d):" + chr(10) + "    x = cmd" + chr(10) + "    cmd = d" + chr(10) + "    return x"
    r1 = pruefe(os.path.join(H, "test.py"), gut, gut, "Trivial", mit_gemini=False)
    print("1 guter Code   :", r1["ok"], r1["stufe"], r1["grund"][:50])
    r2 = pruefe(os.path.join(H, "test.py"), gut, kaputt, "Kaputt", mit_gemini=False)
    print("2 Syntaxfehler :", r2["ok"], r2["stufe"], r2["grund"][:50])
    r3 = pruefe("/system/boot.py", gut, gut, "Ausbruch", mit_gemini=False)
    print("3 Sandbox-Bruch:", r3["ok"], r3["stufe"], r3["grund"][:50])
    r4 = pruefe(os.path.join(H, "test.py"), gut, scope, "Scope-Bug", mit_gemini=False)
    print("4 Scope-Bug    :", r4["ok"], r4["stufe"], "(braucht Gemini zum Fangen)")
    ok, g = rate_ok()
    print("5 Rate-Limit   :", ok, g)
    print("=== FERTIG ===")

if __name__ == "__main__":
    selbsttest()
