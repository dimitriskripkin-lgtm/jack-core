#!/data/data/com.termux/files/usr/bin/python3
"""Gemini-Modellwaechter (Claude, 17.10.2026).

Google hat gemini-2.5-flash und gemini-2.5-flash-lite zum 16.10.2026 abgekuendigt.
Am 17.10. antworten beide noch (gemessen). Solange das so bleibt, aendert sich nichts.
Erst wenn ein Aufruf mit 404 zurueckkommt, setzt melde_404() die Marke ~/jack/.gemini25_weg
und meldet das einmal per Telegram. Danach biegt aktuell() die 2.5-Namen auf den Nachfolger um.
Nachfolger gemini-3.5-flash: antwortet, akzeptiert thinkingBudget 0 (gemessen 17.10.).
gemini-3.5-flash-lite lehnt thinkingBudget 0 ab (400), deshalb nicht als Ersatz.
Rueckweg: Marke loeschen.
"""
import os, json, time

H = os.path.expanduser("~/jack")
MARKE = os.path.join(H, ".gemini25_weg")
ERSATZ = {
    "gemini-2.5-flash": "gemini-3.5-flash",
    "gemini-2.5-flash-lite": "gemini-3.5-flash",
}


def aktuell(name):
    """Modellname, der wirklich benutzt werden soll."""
    if name in ERSATZ and os.path.exists(MARKE):
        return ERSATZ[name]
    return name


def melde_404(name):
    """Nach HTTP 404 fuer ein 2.5-Modell aufrufen. True, wenn jetzt umgestellt wurde."""
    if name not in ERSATZ:
        return False
    if os.path.exists(MARKE):
        return True
    try:
        with open(MARKE, "w") as f:
            json.dump({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "modell": name, "ersatz": ERSATZ[name]}, f)
    except Exception:
        return False
    try:
        import jack_log
        jack_log.log_decision("MODELMAP", "%s liefert 404, ab jetzt %s" % (name, ERSATZ[name]))
    except Exception:
        pass
    try:
        import jack_guard
        jack_guard.notify("Gemini: %s ist abgeschaltet (404). JACK nutzt ab jetzt %s. Kosten pruefen." % (name, ERSATZ[name]))
    except Exception:
        pass
    return True


if __name__ == "__main__":
    print(json.dumps({"marke": os.path.exists(MARKE), "flash": aktuell("gemini-2.5-flash"), "lite": aktuell("gemini-2.5-flash-lite")}))
