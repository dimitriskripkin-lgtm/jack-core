#!/usr/bin/env python3
"""JACK_TUNE_MUSIKGUT (28.10.2026, Claude, Kap 307): Playlist-Rettung "Musik gut (wiederhergestellt)".
Honor -> Xiaomi (as_root=False): legt IDs + Fuellskript in den n8n-Container, fuellt bis zur YouTube-Tagesquote (~190).
Taeglich per Honor-Cron 09:15 bis fertig. Freigabe Dima 28.10.2026 03:47 ("Go"). Keine Geheimnisse in der Ausgabe.
"""
import sys, pathlib, datetime
J = pathlib.Path("/data/data/com.termux/files/home/jack")
sys.path.insert(0, str(J))
import jack_xiaomi as _x

ids = (J / "logs/musik_gut_ids.txt").read_text()
js = (J / "deploy/xiaomi_n8n/musik_gut_fuell.js").read_text()
assert "JACKIDS" not in ids and "JACKJS" not in js

SKRIPT = """export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:$PATH
B="$PREFIX/var/lib/proot-distro/installed-rootfs/ubuntu/home/n8n"
[ -d "$B" ] || { echo "FEHLER rootfs nicht gefunden"; exit 1; }
R="$B/yt_rettung"; mkdir -p "$R"; chmod 700 "$R"
cat > "$R/ids.txt" <<'JACKIDS'
""" + ids + """JACKIDS
cat > "$R/fuell.js" <<'JACKJS'
""" + js + """
JACKJS
timeout 1200 proot-distro login ubuntu --user n8n -- /bin/bash -lc 'set -a; . "$HOME/.config/jack-n8n/key.env"; . "$HOME/.config/jack-n8n/service.env"; set +a; export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24 >/dev/null; node "$HOME/yt_rettung/fuell.js" 190' 2>&1 | grep -v -i "proot warning" | tail -n 5
"""

r = _x.run_shell("/data/data/com.termux/files/usr/bin/bash -s", timeout=1300, as_root=False, input_data=SKRIPT)
out = (r.get("stdout", "") if isinstance(r, dict) else str(r)).strip()
print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), out or "(keine Ausgabe)", flush=True)
