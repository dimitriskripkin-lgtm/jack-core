#!/usr/bin/env python3
"""jack_schema.py — JSON-Schema-Validation für Mission-Files."""
MODULE_VERSION = 1

import os, sys, json
J = os.path.expanduser("~/jack")
sys.path.insert(0, J)
from jack_log import get_logger
log = get_logger("jack_schema")

MISSION_SCHEMA = {
    "required": ["id", "act"],
    "types": {
        "id":      str,
        "act":     str,
        "typ":     str,
        "cat":     str,
        "file":    str,
        "pattern": str,
        "staged":  bool,
        "_prio":   (int, float),
        "expect":  str,
        "expect_max": (int, float),
        "expect_min": (int, float),
    },
    "valid_acts": [
        "shadow_report","talk_contract","fact","diag","no_chrome_src",
        "ui_none","classify_is","compile_ok","explain_ok","sv_ok",
        "mtime_fresh","json_valid","no_secret","grep_count","line_check",
        "hb_ok","file_exists","line_count","sed_replace","py_replace",
        "autodoc",
    ],
    "valid_typs": ["check","fix","notiz","befehl","code"],
    "prio_range": (0, 8),
}

def validate(mission: dict) -> tuple:
    """Validiert eine Mission. Gibt (ok, fehler_liste) zurück."""
    errors = []

    # Required fields
    for field in MISSION_SCHEMA["required"]:
        if field not in mission:
            errors.append(f"Pflichtfeld fehlt: {field}")

    # Type checks
    for field, expected_type in MISSION_SCHEMA["types"].items():
        if field in mission and not isinstance(mission[field], expected_type):
            errors.append(f"{field} falscher Typ: {type(mission[field]).__name__}")

    # ID nicht leer
    if "id" in mission and not mission["id"].strip():
        errors.append("id ist leer")

    # act validieren (wenn in ALLOWED)
    if "act" in mission:
        act = mission["act"]
        if act not in MISSION_SCHEMA["valid_acts"]:
            errors.append(f"act unbekannt: {act}")

    # typ validieren
    if "typ" in mission:
        if mission["typ"] not in MISSION_SCHEMA["valid_typs"]:
            errors.append(f"typ ungültig: {mission['typ']}")

    # _prio range
    if "_prio" in mission:
        p = mission["_prio"]
        lo, hi = MISSION_SCHEMA["prio_range"]
        if not (lo <= p <= hi):
            errors.append(f"_prio {p} außerhalb 0-8")

    # staged braucht file
    if mission.get("staged") and "file" not in mission:
        errors.append("staged:true aber kein file-Feld")

    return len(errors) == 0, errors

def validate_file(fpath: str) -> tuple:
    """Lädt JSON-File und validiert es."""
    try:
        m = json.load(open(fpath))
        return validate(m)
    except json.JSONDecodeError as e:
        return False, [f"JSON-Parse-Fehler: {e}"]
    except Exception as e:
        return False, [f"Fehler: {e}"]

def validate_all_pending() -> dict:
    """Validiert alle pending Missions. Gibt Stats zurück."""
    PEND = os.path.join(J, "missions", "pending")
    if not os.path.exists(PEND):
        return {"ok": 0, "fail": 0, "errors": []}
    ok = fail = 0
    errors = []
    for fname in os.listdir(PEND):
        if not fname.endswith(".json"): continue
        valid, errs = validate_file(os.path.join(PEND, fname))
        if valid:
            ok += 1
        else:
            fail += 1
            errors.append({"file": fname, "errors": errs})
            log.warn(f"Schema-Fehler {fname}: {errs}")
    return {"ok": ok, "fail": fail, "errors": errors[:10]}

if __name__ == "__main__":
    result = validate_all_pending()
    print(f"Schema-Check: {result['ok']} OK, {result['fail']} Fehler")
    for e in result["errors"]:
        print(f"  {e['file']}: {e['errors']}")
