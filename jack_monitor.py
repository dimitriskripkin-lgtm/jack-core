#!/usr/bin/env python3
"""JACK Monitor: Event-driven Ueberwachung + /scan Befehl.
Kein Dauerloop. Prueft nur was sich aendert und meldet sofort."""
import os, json, sqlite3, subprocess, time, datetime

H = os.path.expanduser("~/jack")
STATE_FILE = os.path.join(H, ".monitor_state")

SCHWELLEN = {
    "akku_min": 20,
    "ram_min_mb": 800,
    "temp_max": 43,
}

def _run(cmd, timeout=8):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except Exception:
        return None

def _notify(msg):
    try:
        import sys; sys.path.insert(0, H)
        sec = open(os.path.expanduser("~/.jack_secrets")).read()
        tok = [l.split("=",1)[1].strip().strip('"') for l in sec.split(chr(10)) if "TELEGRAM_BOT_TOKEN" in l][0]
        cid = [l.split("=",1)[1].strip().strip('"') for l in sec.split(chr(10)) if "TELEGRAM_CHAT_ID" in l][0]
        import urllib.request, json as _j
        d = _j.dumps({"chat_id": cid, "text": "[Monitor] " + msg}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage",
            data=d, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        try:
            import jack_log; jack_log.log_decision("MONITOR-NOTIFY-ERR", str(e)[:80])
        except Exception:
            pass

def _log(tag, msg):
    try:
        import jack_log; jack_log.log_decision(tag, msg[:120])
    except Exception:
        pass

def lade_state():
    try:
        return json.load(open(STATE_FILE))
    except Exception:
        return {}

def speichere_state(state):
    json.dump(state, open(STATE_FILE, "w"), ensure_ascii=False)

def check_akku():
    try:
        r = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=8)
        d = json.loads(r.stdout)
        return {
            "prozent": int(d.get("percentage", 100)),
            "status": d.get("status", "?"),
            "temperatur": float(d.get("temperature", 0)),
            "plugged": d.get("plugged", "?"),
        }
    except Exception:
        return None

def check_ram():
    try:
        werte = {}
        for z in open("/proc/meminfo"):
            t = z.split(":")
            if len(t) == 2:
                werte[t[0].strip()] = int(t[1].strip().split()[0]) // 1024
        return {
            "gesamt_mb": werte.get("MemTotal", 0),
            "verfuegbar_mb": werte.get("MemAvailable", 0),
        }
    except Exception:
        return None

def check_dienste():
    try:
        r = subprocess.run(
            ["sv", "status", "jack_cortex", "jack_telegram", "jack_waechter", "ollama"],
            capture_output=True, text=True, timeout=8
        )
        tote = [l.split(":")[1].strip().split()[0] for l in r.stdout.splitlines() if l.startswith("down:")]
        return {"tote": tote, "alle_ok": len(tote) == 0}
    except Exception:
        return None

def check_wlan():
    try:
        r = subprocess.run(["termux-wifi-connectioninfo"], capture_output=True, text=True, timeout=8)
        d = json.loads(r.stdout)
        return {
            "ssid": d.get("ssid", "?"),
            "ip": d.get("ip", "?"),
            "rssi": int(d.get("rssi", 0)),
        }
    except Exception:
        return None

def event_check():
    """Prueft auf kritische Events. Meldet nur wenn sich was aendert."""
    state = lade_state()
    meldungen = []
    ts = datetime.datetime.now().isoformat()

    # Akku
    akku = check_akku()
    if akku:
        war_niedrig = state.get("akku_niedrig", False)
        ist_niedrig = akku["prozent"] <= SCHWELLEN["akku_min"]
        if ist_niedrig and not war_niedrig:
            meldungen.append(f"Akku kritisch: {akku['prozent']}% ({akku['status']})")
            _log("MONITOR-AKKU-WARN", str(akku["prozent"]) + "%")
        if not ist_niedrig and war_niedrig:
            meldungen.append(f"Akku erholt: {akku['prozent']}%")
        state["akku_niedrig"] = ist_niedrig
        state["akku_prozent"] = akku["prozent"]

        war_heiss = state.get("akku_heiss", False)
        ist_heiss = akku["temperatur"] >= SCHWELLEN["temp_max"]
        if ist_heiss and not war_heiss:
            meldungen.append(f"Temperatur kritisch: {akku['temperatur']}C")
        state["akku_heiss"] = ist_heiss
        state["akku_temp_zuletzt"] = akku["temperatur"]

    # RAM
    ram = check_ram()
    if ram:
        war_knapp = state.get("ram_knapp", False)
        ist_knapp = ram["verfuegbar_mb"] < SCHWELLEN["ram_min_mb"]
        if ist_knapp and not war_knapp:
            meldungen.append(f"RAM knapp: {ram['verfuegbar_mb']} MB verfuegbar")
            _log("MONITOR-RAM-WARN", str(ram["verfuegbar_mb"]) + "MB")
        if not ist_knapp and war_knapp:
            meldungen.append(f"RAM erholt: {ram['verfuegbar_mb']} MB verfuegbar")
        state["ram_knapp"] = ist_knapp
        state["ram_mb"] = ram["verfuegbar_mb"]

    # Dienste
    dienste = check_dienste()
    if dienste:
        tote_vorher = set(state.get("tote_dienste", []))
        tote_jetzt = set(dienste["tote"])
        neu_tot = tote_jetzt - tote_vorher
        erholt = tote_vorher - tote_jetzt
        if neu_tot:
            meldungen.append(f"Dienste tot: {', '.join(neu_tot)}")
            _log("MONITOR-DIENST-TOT", ", ".join(neu_tot))
        if erholt:
            meldungen.append(f"Dienste erholt: {', '.join(erholt)}")
        state["tote_dienste"] = list(tote_jetzt)

    # WLAN
    wlan = check_wlan()
    if wlan:
        letztes_ssid = state.get("wlan_ssid", "")
        if wlan["ssid"] != letztes_ssid and letztes_ssid:
            meldungen.append(f"WLAN gewechselt: {letztes_ssid} -> {wlan['ssid']}")
        state["wlan_ssid"] = wlan["ssid"]
        state["wlan_ip"] = wlan["ip"]

    state["letzter_check"] = ts
    speichere_state(state)

    for m in meldungen:
        _notify(m)

    return meldungen

def vollscan():
    """Vollstaendiger Scan auf Befehl (/scan). Gibt komplettes Bild."""
    ts = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
    zeilen = [f"JACK Scan {ts}"]

    akku = check_akku()
    if akku:
        zeilen.append(f"Akku: {akku['prozent']}% | {akku['status']} | {akku['temperatur']}C | {akku['plugged']}")

    ram = check_ram()
    if ram:
        belegt = ram["gesamt_mb"] - ram["verfuegbar_mb"]
        zeilen.append(f"RAM: {ram['verfuegbar_mb']} MB frei / {ram['gesamt_mb']} MB gesamt ({belegt} MB belegt)")

    dienste = check_dienste()
    if dienste:
        if dienste["alle_ok"]:
            zeilen.append("Dienste: alle 4 laufen")
        else:
            zeilen.append(f"Dienste: TOT -> {', '.join(dienste['tote'])}")

    wlan = check_wlan()
    if wlan:
        zeilen.append(f"WLAN: {wlan['ssid']} | IP {wlan['ip']} | Signal {wlan['rssi']} dBm")

    storage = _run("df -h $HOME | tail -1 | awk '{print $2, $3, $4, $5}'")
    if storage:
        zeilen.append(f"Storage: {storage}")

    fp_pfad = os.path.join(H, "jack_fingerprint.json")
    if os.path.exists(fp_pfad):
        fp = json.load(open(fp_pfad))
        zeilen.append(f"Fingerabdruck: {fp['hash']} ({fp['timestamp'][:16]})")

    skills_db = os.path.join(H, "jack_skills.db")
    if os.path.exists(skills_db):
        c = sqlite3.connect(skills_db)
        total = c.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
        ok = c.execute("SELECT COUNT(*) FROM skills WHERE status='verifiziert'").fetchone()[0]
        c.close()
        zeilen.append(f"Skills: {ok}/{total} verifiziert")

    cog_db = os.path.join(H, "jack_cognition.db")
    if os.path.exists(cog_db):
        c = sqlite3.connect(cog_db)
        n = c.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
        c.close()
        zeilen.append(f"Cognition Traces: {n}")

    _log("MONITOR-VOLLSCAN", "ok")
    return chr(10).join(zeilen)

if __name__ == "__main__":
    print("=== Event Check ===")
    events = event_check()
    print("Events:", events if events else "keine")
    print()
    print("=== Vollscan ===")
    print(vollscan())
