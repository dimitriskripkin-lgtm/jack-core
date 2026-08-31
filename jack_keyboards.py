#!/usr/bin/env python3
"""jack_keyboards.py — alle Keyboard/Menu-Builder. Kein Telegram-State."""

def build_write_keyboard(filename):
    return {"inline_keyboard":[[
        {"text":"🟢 Bestätigen","callback_data":f"confirm_write:{filename}"},
        {"text":"🔴 Abbrechen","callback_data":f"cancel_write:{filename}"}
    ]]}

def menu_hauptseite(MENU):
    kb = [[(_v["label"], "menu:"+_k)] for _k, _v in MENU.items()]
    try:
        if "menu:befehle" not in str(kb):
            kb.append([("🔧 Alle Befehle","menu:befehle")])
    except Exception:
        pass
    return kb

def menu_kategorie(key, MENU):
    if key not in MENU:
        return "Unbekannte Kategorie"
    kat = MENU[key]
    zeilen = [kat["label"],""]
    for befehl, beschreibung, beispiel in kat["befehle"]:
        zeilen += [f"• {befehl}", f"  {beschreibung}",
                   f"  Beispiel: {beispiel}", ""]
    zeilen.append("← /menu fuer Hauptmenue")
    return chr(10).join(zeilen)
