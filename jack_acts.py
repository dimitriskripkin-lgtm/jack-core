#!/usr/bin/env python3
"""JACK_TUNE_ACTS Schritt 3. Eine Liste. Noch niemand liest sie."""
ACTS = {
"fact": {"freigabe": False, "xiaomi": False, "text": "Fakt lesen"},
"diag": {"freigabe": False, "xiaomi": False, "text": "Diagnose lesen"},
"classify_is": {"freigabe": False, "xiaomi": False, "text": "Satz einordnen"},
"compile_ok": {"freigabe": False, "xiaomi": False, "text": "Python pruefen"},
"explain_ok": {"freigabe": False, "xiaomi": False, "text": "Erklaerung pruefen"},
"sv_ok": {"freigabe": False, "xiaomi": False, "text": "Dienststatus lesen"},
"hb_ok": {"freigabe": False, "xiaomi": False, "text": "Herzschlag lesen"},
"mtime_fresh": {"freigabe": False, "xiaomi": False, "text": "Datei-Alter lesen"},
"json_valid": {"freigabe": False, "xiaomi": False, "text": "JSON pruefen"},
"no_secret": {"freigabe": False, "xiaomi": False, "text": "Secret-Muster suchen"},
"no_chrome_src": {"freigabe": False, "xiaomi": False, "text": "Chrome-Quelle pruefen"},
"ui_none": {"freigabe": False, "xiaomi": False, "text": "UI leer pruefen"},
"grep_count": {"freigabe": False, "xiaomi": False, "text": "Treffer zaehlen"},
"line_check": {"freigabe": False, "xiaomi": False, "text": "Zeile pruefen"},
"line_count": {"freigabe": False, "xiaomi": False, "text": "Zeilen zaehlen"},
"file_exists": {"freigabe": False, "xiaomi": False, "text": "Datei da?"},
"list_proposals": {"freigabe": False, "xiaomi": False, "text": "Vorschlaege zeigen"},
"preview_proposal": {"freigabe": False, "xiaomi": False, "text": "Vorschlag zeigen"},
"shadow_report": {"freigabe": False, "xiaomi": False, "text": "Schattenbericht"},
"talk_contract": {"freigabe": False, "xiaomi": False, "text": "Talk-Vertrag pruefen"},
"dashboard_render": {"freigabe": False, "xiaomi": False, "text": "Dashboard bauen"},
"was_ist_neu": {"freigabe": False, "xiaomi": False, "text": "Neu seit letztem Blick"},
"honor_heat_report": {"freigabe": False, "xiaomi": False, "text": "Honor-Waerme lesen"},
"xiaomi_ssh_check": {"freigabe": False, "xiaomi": True, "text": "Xiaomi nur anpingen"},
"xiaomi_battery": {"freigabe": False, "xiaomi": True, "text": "Xiaomi-Akku lesen"},
"xiaomi_ollama_status": {"freigabe": False, "xiaomi": True, "text": "Xiaomi-Ollama Status"},
"file_create": {"freigabe": True, "xiaomi": False, "text": "Datei anlegen"},
"file_delete": {"freigabe": True, "xiaomi": False, "text": "Datei loeschen"},
"py_replace": {"freigabe": True, "xiaomi": False, "text": "Text ersetzen"},
"sed_replace": {"freigabe": True, "xiaomi": False, "text": "Zeile ersetzen"},
"create_demo_file": {"freigabe": True, "xiaomi": False, "text": "Demo-Datei"},
"graph_add_fact": {"freigabe": True, "xiaomi": False, "text": "Graph-Fakt schreiben"},
"graph_remove_fact": {"freigabe": True, "xiaomi": False, "text": "Graph-Fakt loeschen"},
"sv_restart": {"freigabe": True, "xiaomi": False, "text": "Dienst neu starten"},
"reload_module": {"freigabe": True, "xiaomi": False, "text": "Modul neu laden"},
"batch": {"freigabe": True, "xiaomi": False, "text": "Mehrere Acts"},
"propose_fix": {"freigabe": True, "xiaomi": False, "text": "Fix vorschlagen"},
"approve_proposal": {"freigabe": True, "xiaomi": False, "text": "Vorschlag ausfuehren"},
"exec_proposed": {"freigabe": True, "xiaomi": False, "text": "Vorgeschlagenen Befehl"},
"write_proposed": {"freigabe": True, "xiaomi": False, "text": "Vorgeschlagenes Schreiben"},
"honor_ollama_disable": {"freigabe": True, "xiaomi": False, "text": "Honor-Ollama aus"},
"open_url_xiaomi": {"freigabe": True, "xiaomi": True, "text": "URL auf Xiaomi"},
"close_app_xiaomi": {"freigabe": True, "xiaomi": True, "text": "App auf Xiaomi zu"},
"chrome_search_xiaomi": {"freigabe": True, "xiaomi": True, "text": "Chrome auf Xiaomi"},
"maps_nav_xiaomi": {"freigabe": True, "xiaomi": True, "text": "Navigation Xiaomi"},
"maps_open_xiaomi": {"freigabe": True, "xiaomi": True, "text": "Karten Xiaomi"},
"spotify_play_xiaomi": {"freigabe": True, "xiaomi": True, "text": "Spotify Xiaomi"},
"youtube_search_xiaomi": {"freigabe": True, "xiaomi": True, "text": "YouTube-Suche Xiaomi"},
"youtube_play_xiaomi": {"freigabe": True, "xiaomi": True, "text": "YouTube Xiaomi"},
"xiaomi_ollama_restart": {"freigabe": True, "xiaomi": True, "text": "Xiaomi-Ollama an"},
"xiaomi_ollama_stop": {"freigabe": True, "xiaomi": True, "text": "Xiaomi-Ollama aus"},
"plan_try": {"freigabe": True, "xiaomi": True, "text": "UI-Plan auf Xiaomi testen (ohne exec)"},
"skill_confirm": {"freigabe": True, "xiaomi": False, "text": "Skill nach Dimas Bestaetigung speichern"},
"honor_net_scan": {"freigabe": True, "xiaomi": False, "text": "Honor Netzwerk-Diagnose (ip neigh/addr/route), read-only"},
"xiaomi_screenshot": {"freigabe": True, "xiaomi": True, "text": "Screenshot des Xiaomi als Base64-Datei fuer read_file (Vision)"},
}

def names():
    return sorted(ACTS)

def braucht_freigabe(name):
    return bool(ACTS.get(name, {}).get("freigabe"))

def braucht_xiaomi(name):
    return bool(ACTS.get(name, {}).get("xiaomi"))
