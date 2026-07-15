#!/usr/bin/env python3
"""JACK Autonomer Agent: arbeitet SELBSTSTAENDIG an einem Ziel - NUR in der Werkstatt.
Schreibt Code, testet, verbessert sich, bis es laeuft. HARTE WAENDE bleiben absolut:
kein Loeschen, kein Netz, keine Secrets, kein Ausbruch, Timeout, Budget. Diese Waende
sind KEINE entziehbaren Rechte - sie MACHEN die Sandbox aus."""
import jack_coder, jack_budget, jack_log

def _failed(out):
    low=(out or "").lower()
    return ("traceback" in low or "error" in low or "exception" in low or "blockiert" in low or (out or "").strip()=="")

def _fehler_signatur(out):
    for line in (out or "").splitlines():
        line = line.strip()
        if line:
            return line[:120]
    return ""

def autonomous_task(goal, max_iter=4):
    jack_log.log_decision("AGENT-START", goal[:80])
    aufgabe=goal; letzte=None
    letzte_sig=None; sig_count=0
    import time as _t
    for i in range(1, max_iter+1):
        if i>1: _t.sleep(6)
        okb, _=jack_budget.check_and_count("text")
        if not okb:
            jack_log.log_decision("AGENT-STOP","Budget")
            return False, f"Budget-Limit erreicht nach {i-1} Runden."
        fn, code, msg=jack_coder.write_code(aufgabe)
        if not fn:
            return False, f"Code-Erzeugung fehlgeschlagen: {msg}"
        letzte=fn
        ok, out=jack_coder.run_code(fn)
        gut = ok and not _failed(out)
        jack_log.log_decision("AGENT-RUNDE", f"{goal[:35]} #{i}", "ok" if gut else "nachbessern")
        if gut:
            jack_log.log_decision("AGENT-ERFOLG", f"{goal[:35]} -> {fn}")
            return True, f"Geschafft in Runde {i}. Datei: {fn}\n\nErgebnis:\n{out[:800]}"
        sig = _fehler_signatur(out)
        if sig and sig == letzte_sig:
            sig_count += 1
        else:
            sig_count = 1; letzte_sig = sig
        if sig_count >= 3:
            jack_log.log_decision("AGENT-CIRCUIT-BREAKER", f"{goal[:35]} gleicher Fehler 3x -> Abbruch")
            return False, f"Circuit Breaker: gleicher Fehler 3x in Folge, Runde {i} abgebrochen.\nFehler: {sig}\nLetzter Stand: {letzte}"
        aufgabe=(goal+f"\n\nDein letzter Code ({fn}) ergab dieses Problem:\n{out[:500]}\n"
                 "Korrigiere es. Wieder vollstaendiges lauffaehiges Python, nur Code.")
    return False, f"Nach {max_iter} Runden nicht geschafft. Letzter Stand: {letzte}"
