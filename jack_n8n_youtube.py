#!/usr/bin/env python3
"""JACK_TUNE_N8NYOUTUBE (27.10.2026, Claude, Kap 307): YouTube-Zugang in n8n mit EINEM Befehl.
Uebernimmt Client-ID/Schluessel aus dem vorhandenen Google-Kalender-Zugang (bleibt alles auf dem Xiaomi),
legt den n8n-Zugang "YouTube (JACK)" an, oeffnet die Verbindung Honor->Xiaomi und die richtige n8n-Seite.
Gibt keine Geheimnisse aus.
"""
import subprocess, sys, time
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
import jack_xiaomi as _x

CRED_ID = "jackYouTube00001"
URL = "http://localhost:5678/home/credentials/" + CRED_ID

_SKRIPT = r"""export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:$PATH
timeout 110 proot-distro login ubuntu --user n8n -- /bin/bash -lc '
set -e; umask 077
set -a; . "$HOME/.config/jack-n8n/key.env"; . "$HOME/.config/jack-n8n/service.env"; set +a
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24 >/dev/null
N="$HOME/jack_n8n/node_modules/n8n/bin/n8n"
"$N" export:credentials --id=jackGoogleCal001 --decrypted --output="$HOME/k.json" >/dev/null 2>&1
node -e "
const fs=require(\"fs\"),H=process.env.HOME;
const k=JSON.parse(fs.readFileSync(H+\"/k.json\",\"utf8\")); const c=(Array.isArray(k)?k[0]:k).data;
fs.writeFileSync(H+\"/y.json\",JSON.stringify([{id:\"jackYouTube00001\",name:\"YouTube (JACK)\",type:\"youTubeOAuth2Api\",data:{clientId:c.clientId,clientSecret:c.clientSecret}}]));
console.log(\"client uebernommen\");
"
"$N" import:credentials --input="$HOME/y.json" 2>&1 | grep -i -E "import|error" | tail -n 2
rm -f "$HOME/k.json" "$HOME/y.json"
' 2>&1 | grep -v -i "proot warning"
"""

print("Lege den YouTube-Zugang in n8n an (ca. 1 Minute) ...")
r = _x.run_shell("/data/data/com.termux/files/usr/bin/bash -s", timeout=115, as_root=False, input_data=_SKRIPT)
out = (r.get("stdout", "") if isinstance(r, dict) else str(r)).strip()
print(out or "(keine Ausgabe)")
if "Successfully" not in out:
    sys.exit("FEHLER: YouTube-Zugang nicht angelegt. Screenshot an Claude. Nichts weiter passiert.")
ok = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", "3", "http://127.0.0.1:5678/"],
                    capture_output=True, text=True).stdout
if ok != "200":
    subprocess.run(["ssh", "-f", "-N", "-o", "ExitOnForwardFailure=yes", "-L", "5678:127.0.0.1:5678", "xiaomi-jack"])
    time.sleep(3)
subprocess.run(["termux-open-url", URL])
print("JETZT in Chrome: 'Sign in with Google' -> Konto -> kleines 'Weiter' -> 'Weiter/Zulassen' -> in n8n 'Save'.")
