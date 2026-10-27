#!/usr/bin/env python3
"""JACK_TUNE_N8NGOOGLE (27.10.2026, Claude, Kap 307): Google-Kalender-Zugang in n8n mit EINEM Befehl.
Fragt Client-ID + Client-Schluessel ab (Schluessel unsichtbar), legt den n8n-Zugang per CLI-Import an,
oeffnet die Verbindung Honor->Xiaomi und direkt die richtige n8n-Seite. Gibt keine Geheimnisse aus.
"""
import getpass, json, subprocess, sys, time
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
import jack_xiaomi as _x

CRED_ID = "jackGoogleCal001"
URL = "http://localhost:5678/home/credentials/" + CRED_ID

cid = input("Client-ID einfuegen: ").strip()
if not cid.endswith(".apps.googleusercontent.com"):
    sys.exit("FEHLER: Das sieht nicht wie eine Client-ID aus (endet auf .apps.googleusercontent.com). Nichts geaendert.")
sec = getpass.getpass("Client-Schluessel einfuegen (bleibt unsichtbar), dann Enter: ").strip()
if len(sec) < 15:
    sys.exit("FEHLER: Client-Schluessel zu kurz. Nichts geaendert.")

daten = json.dumps([{"id": CRED_ID, "name": "Google Kalender (JACK)", "type": "googleCalendarOAuth2Api",
                     "data": {"clientId": cid, "clientSecret": sec}}])
R = "/data/data/com.termux/files/usr/var/lib/proot-distro/installed-rootfs/ubuntu"
cmd = ("export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:$PATH; "
       "umask 077; cat > " + R + "/home/n8n/cred_import.json && "
       "timeout 100 proot-distro login ubuntu --user n8n -- /bin/bash -lc '"
       "set -a; . \"$HOME/.config/jack-n8n/key.env\"; . \"$HOME/.config/jack-n8n/service.env\"; set +a; "
       "export NVM_DIR=\"$HOME/.nvm\"; . \"$NVM_DIR/nvm.sh\"; nvm use 24 >/dev/null; "
       "\"$HOME/jack_n8n/node_modules/n8n/bin/n8n\" import:credentials --input=\"$HOME/cred_import.json\" 2>&1 | grep -i -E \"import|error\" | tail -n 3; "
       "rm -f \"$HOME/cred_import.json\"' 2>&1 | grep -v -i 'proot warning'; rm -f " + R + "/home/n8n/cred_import.json")
print("Lege den Zugang in n8n an (ca. 1 Minute) ...")
r = _x.run_shell(cmd, timeout=115, as_root=False, input_data=daten)
out = (r.get("stdout", "") if isinstance(r, dict) else str(r)).strip()
print(out or "(keine Ausgabe)")
if "Successfully" not in out:
    sys.exit("FEHLER: Zugang nicht angelegt. Schick Claude einen Screenshot. Nichts weiter passiert.")
print("OK: Zugang gespeichert.")

ok = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "3", "http://127.0.0.1:5678/"],
                    capture_output=True, text=True).stdout
if ok != "200":
    subprocess.run(["ssh", "-f", "-N", "-o", "ExitOnForwardFailure=yes", "-L", "5678:127.0.0.1:5678", "xiaomi-jack"])
    time.sleep(3)
print("Verbindung zum Xiaomi: offen. Oeffne jetzt die richtige n8n-Seite ...")
subprocess.run(["termux-open-url", URL])
print("JETZT: in Chrome 'Sign in with Google' -> Konto -> 'Weiter' -> 'Zulassen' -> zurueck in n8n 'Save'.")
