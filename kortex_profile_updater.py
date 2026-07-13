#!/usr/bin/env python3
"""
Analysiert neue learned_facts und schreibt relevante
automatisch in kortex_profile.json (entscheidungen, projekte, owner).
Regelbasiert - kein LLM noetig.
"""
import json, os, re
from datetime import datetime

PROFILE = os.path.expanduser("~/jack/kortex_profile.json")

ENTSCHEIDUNG_KEYS = ["entschieden", "beschlossen", "ab jetzt", "nie wieder",
                      "verboten", "ersetzt", "umgestellt", "migriert", "gefixt"]
PROJEKT_KEYS = ["projekt", "wohnung", "jack", "kortex", "app", "tool", "script"]
OWNER_KEYS = ["dima ist", "dima hat", "dima nutzt", "dima arbeitet", "dima wohnt"]

def _load():
    try:
        return json.load(open(PROFILE))
    except Exception:
        return {}

def _save(p):
    json.dump(p, open(PROFILE, "w"), indent=2, ensure_ascii=False)

def _heute():
    return datetime.now().strftime("%Y-%m-%d")

def update_from_facts(new_facts: list, existing_facts: list):
    """
    Vergleicht neue mit bekannten Fakten.
    Klassifiziert und schreibt in kortex_profile.json.
    Gibt Anzahl Updates zurueck.
    """
    if not new_facts:
        return 0

    alte = set(existing_facts)
    wirklich_neu = [f for f in new_facts if f not in alte]
    if not wirklich_neu:
        return 0

    p = _load()
    updates = 0

    for fakt in wirklich_neu:
        fakt_lower = fakt.lower()

        # Entscheidungen
        if any(k in fakt_lower for k in ENTSCHEIDUNG_KEYS):
            eintrag = {"datum": _heute(), "entscheidung": fakt}
            existing_e = [e.get("entscheidung","") for e in p.get("entscheidungen", [])]
            if fakt not in existing_e:
                p.setdefault("entscheidungen", []).append(eintrag)
                updates += 1
            continue

        # Projekte - naechster_schritt aktualisieren
        if any(k in fakt_lower for k in PROJEKT_KEYS):
            for proj in p.get("projekte", []):
                if proj["name"].lower() in fakt_lower:
                    proj["naechster_schritt"] = fakt
                    updates += 1
                    break
            continue

        # Owner-Fakten
        if any(k in fakt_lower for k in OWNER_KEYS):
            owner = p.setdefault("owner", {})
            notizen = owner.setdefault("notizen", [])
            if fakt not in notizen:
                notizen.append(fakt)
                # max 10 owner-notizen
                owner["notizen"] = notizen[-10:]
                updates += 1
            continue

    if updates > 0:
        p.setdefault("meta", {})["profile_updated"] = datetime.now().isoformat()
        _save(p)

    return updates


if __name__ == "__main__":
    # Testlauf
    test_neu = [
        "Dima hat beschlossen FTS5 statt ChromaDB zu nutzen",
        "JACK Projekt naechster Schritt: Voice-Bug fixen auf Xiaomi",
        "Dima wohnt in Bremen",
    ]
    test_alt = []
    n = update_from_facts(test_neu, test_alt)
    print(f"Updates: {n}")
    import subprocess
    subprocess.run(["python3", "-c",
        "import json; p=json.load(open('/data/data/com.termux/files/home/jack/kortex_profile.json')); print(json.dumps({'entscheidungen': p.get('entscheidungen',[])[-2:], 'owner_notizen': p.get('owner',{}).get('notizen',[])}, indent=2, ensure_ascii=False))"])
