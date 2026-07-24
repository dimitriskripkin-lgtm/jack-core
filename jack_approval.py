#!/usr/bin/env python3
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.expanduser("~/jack"))

SAFE_DIRS = [os.path.expanduser("~/jack"), os.path.expanduser("~/jack_werkstatt"), "/data/local/tmp"]
FORBIDDEN_DIRS = ["/system/", "/data/system/", "/data/app/", "/data/data/"]
AUTONOM_PREFIX = "jack autonom:"


def _norm_pfad(p):
    return os.path.normpath(str(Path(p).resolve()))


def _liegt_unter(pfad, basis):
    b = _norm_pfad(basis)
    return pfad == b or pfad.startswith(b + os.sep)


def is_safe_path(filepath):
    p = _norm_pfad(filepath)
    for safe in SAFE_DIRS:
        if _liegt_unter(p, safe):
            return True, None
    for forbidden in FORBIDDEN_DIRS:
        if _liegt_unter(p, forbidden):
            return False, f"Forbidden: {forbidden}"
    return False, "Outside sandbox"


def has_autonom_prefix(raw_command):
    return raw_command.strip().lower().startswith(AUTONOM_PREFIX)


def check_approval(filepath, operation="edit", raw_command="", use_voice=False):
    safe, reason = is_safe_path(filepath)
    if not safe:
        return False, f"BLOCKED (Sandbox): {reason}"

    if operation == "create" and not os.path.exists(filepath):
        return True, "Neue Datei im Sandbox-Bereich"

    if has_autonom_prefix(raw_command):
        return True, f"Autonom-Praefix erkannt: '{AUTONOM_PREFIX}'"

    prompt = f"Aenderung an {os.path.basename(filepath)} freigeben?"

    if use_voice:
        from jack_voice import confirm
        result = confirm(prompt)
        if result is True:
            return True, "Voice-Bestaetigung: ja"
        elif result is False:
            return False, "Voice-Bestaetigung: nein"
        else:
            return False, "Voice-Bestaetigung: unklar, sicherheitshalber abgelehnt"
    else:
        response = input(f"{prompt} (ja/nein): ").strip().lower()
        return response in ("ja", "j", "yes", "y"), "Text-Bestaetigung"


if __name__ == "__main__":
    print("[APPROVAL] Testmodus\n")
    ok, reason = check_approval(os.path.expanduser("~/jack/test_approval_neu.py"), operation="create")
    print(f"Test 1 (neue Datei): {ok} ({reason})")
    ok, reason = check_approval(os.path.expanduser("~/jack/jack_config.py"), operation="edit", raw_command="JACK autonom: fixe den bug in config.py")
    print(f"Test 2 (autonom-praefix): {ok} ({reason})")
    ok, reason = check_approval("/system/build.prop", operation="edit")
    print(f"Test 3 (unsicherer Pfad): {ok} ({reason})")


def confirm_action(description, raw_command="", use_voice=False):
    """
    Generische Freigabe fuer Aktionen OHNE Dateipfad (z.B. Aktionslisten
    aus jack_operator.py). Nutzt dieselbe Autonom-Praefix-Logik wie
    check_approval(), aber ohne Sandbox-Pfad-Check.
    Gibt True/False zurueck.
    """
    if has_autonom_prefix(raw_command):
        print(f"[APPROVAL] Autonom-Praefix erkannt, automatisch freigegeben: {description}")
        return True

    prompt = f"{description} - freigeben?"

    if use_voice:
        from jack_voice import confirm
        result = confirm(prompt)
        return result is True
    else:
        response = input(f"{prompt} (ja/nein): ").strip().lower()
        return response in ("ja", "j", "yes", "y")
