#!/data/data/com.termux/files/usr/bin/python3
"""Chrome App Card: feste Suche ueber vorhandenen UI-Pfad, Erfolg nur per Vertrag."""
import re
import time

PKG = "com.android.chrome"
MAX_QUERY = 180

def _norm(s):
    return re.sub(r"\s+", " ", str(s or "").lower()).strip()

def query_from_goal(ziel):
    z = " ".join(str(ziel or "").split()).strip()
    if not z:
        return ""
    m = re.search(r'["\']([^"\']{2,180})["\']', z)
    if m:
        return m.group(1).strip()
    m = re.search(r"\b(?:suche|such)\b.*?\bnach\s+(.+)$", z, re.I)
    if not m:
        return ""
    q = re.split(r"\s+\bund\b\s+(?:zeige|zeig|oeffne|lass|bleib)\b",
                 m.group(1), maxsplit=1, flags=re.I)[0]
    return q.strip(" .,:;")[:MAX_QUERY]

def _strict_contract(query, vertrag):
    if not isinstance(vertrag, dict) or vertrag.get("app") != PKG:
        return None, "Chrome-Erfolgsvertrag fehlt"
    qn = _norm(query)
    eins = [str(x).strip() for x in (vertrag.get("text_eins") or []) if str(x).strip()]
    result_eins = [x for x in eins if _norm(x) not in qn]
    if not result_eins:
        return None, "kein ergebnis-spezifischer text_eins-Beleg ausserhalb des Query-Texts"
    return {
        "app": PKG,
        "text_alle": list(vertrag.get("text_alle") or []),
        "text_eins": result_eins,
        "text_nicht": list(vertrag.get("text_nicht") or []),
    }, "ok"

def _fg():
    import jack_ui_session as ui
    return (ui.get_foreground().get("pkg") or "")

def _xml():
    import jack_ghost as jg
    return jg.hol_xiaomi_ui() or ""

def _xml_diag(xml):
    import xml.etree.ElementTree as ET
    s = str(xml or "")
    hat_hierarchy = "<hierarchy" in s
    idle = "idle state" in s.lower()
    parse_ok = False
    parse_err = ""
    try:
        ET.fromstring(s)
        parse_ok = True
    except Exception as e:
        parse_err = type(e).__name__
    return {
        "len": len(s),
        "hierarchy": hat_hierarchy,
        "parse_ok": parse_ok,
        "parse_err": parse_err,
        "idle_state": idle,
    }

def run_search(query, vertrag, send_fn=None):
    q = " ".join(str(query or "").split()).strip()
    if not q or len(q) > MAX_QUERY:
        return {"handled": True, "ok": False, "stufe": "FAIL",
                "grund": ["Query leer/zu lang"], "schritte": 0, "vision": 0}
    contract, why = _strict_contract(q, vertrag)
    if contract is None:
        return {"handled": True, "ok": False, "stufe": "UNBEWIESEN",
                "grund": [why], "schritte": 0, "vision": 0}

    import urllib.parse
    import jack_xiaomi as jx
    enc = urllib.parse.quote_plus(q, safe="")
    url = "https://www.google.com/search?q=" + enc
    cmd = "am start -a android.intent.action.VIEW -d \"" + url + "\" -n com.android.chrome/com.google.android.apps.chrome.Main"
    r = jx.run_shell(cmd, as_root=True, timeout=15)
    if not r.get("success"):
        return {"handled": True, "ok": False, "stufe": "FAIL",
                "grund": ["Chrome-Suche fehlgeschlagen: " + str(r.get("stderr") or "")[:100]],
                "schritte": 1, "vision": 0}
    if send_fn:
        send_fn("APP-CARD Chrome: direkte Such-URL geoeffnet")
    time.sleep(3.0)

    import jack_finish_verify as fv
    diag_fg = _fg()
    diag_xml = _xml()
    diag_meta = _xml_diag(diag_xml)
    diag_all = fv.ui_texte(diag_xml)[:200]
    diag_texte = diag_all[:40]
    try:
        import os
        pfad = os.path.expanduser("~/jack/ARBEITSPLATZ/BUEROS/chatgpt/chrome_diag_last.txt")
        tmp = pfad + ".tmp"
        os.makedirs(os.path.dirname(pfad), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("query=" + q + "\n")
            f.write("fg=" + (diag_fg or "?") + "\n")
            f.write("xml_len=" + str(diag_meta["len"]) + "\n")
            f.write("hierarchy=" + str(diag_meta["hierarchy"]) + "\n")
            f.write("parse_ok=" + str(diag_meta["parse_ok"]) + "\n")
            f.write("parse_err=" + (diag_meta["parse_err"] or "-") + "\n")
            f.write("idle_state=" + str(diag_meta["idle_state"]) + "\n")
            f.write("texte_count=" + str(len(diag_all)) + "\n")
            for i, t in enumerate(diag_all, 1):
                f.write("%03d: %s\n" % (i, " ".join(str(t).split())))
        os.replace(tmp, pfad)
    except Exception:
        pass
    if send_fn:
        send_fn("APP-CARD DIAG fg=%s xml_len=%s hierarchy=%s parse_ok=%s parse_err=%s idle_state=%s texte40=%s" % (
            diag_fg or "?", diag_meta["len"], diag_meta["hierarchy"], diag_meta["parse_ok"],
            diag_meta["parse_err"] or "-", diag_meta["idle_state"], " | ".join(diag_texte)[:1800]))
    stufe, gruende = fv.pruefe(
        "Chrome-Suchergebnisse fuer: " + q,
        contract, _fg, _xml, vision_fn=None, wiederholen=2, pause=0.7)
    if send_fn:
        send_fn("APP-CARD Chrome: %s - %s" % (stufe, "; ".join(gruende)[:160]))
    return {"handled": True, "ok": stufe == "VERIFIZIERT", "stufe": stufe,
            "grund": gruende, "schritte": 2, "vision": 0, "contract": contract}
