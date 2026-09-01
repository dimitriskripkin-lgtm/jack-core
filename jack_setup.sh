#!/data/data/com.termux/files/usr/bin/sh
# jack_setup.sh — JACK auf neuem Termux-Gerät in ~10 Minuten
set -e
JACK_HOME="$HOME/jack"
echo "=== JACK Setup ==="
echo "[1/6] Pakete..."
pkg install -y python git openssh sqlite curl termux-api 2>/dev/null
echo "[2/6] Python-Pakete..."
pip install requests 2>/dev/null || true
echo "[3/6] Repo..."
if [ -d "$JACK_HOME/.git" ]; then
    cd "$JACK_HOME" && git pull origin master
else
    git clone https://github.com/dimitriskripkin-lgtm/jack-core.git "$JACK_HOME"
fi
echo "[4/6] Config..."
[ ! -f "$JACK_HOME/config.ini" ] && echo "WARNUNG: config.ini fehlt"
echo "[5/6] Verzeichnisse..."
mkdir -p "$JACK_HOME/missions/pending" "$JACK_HOME/missions/done"
mkdir -p "$JACK_HOME/missions/fail" "$JACK_HOME/missions/archive"
mkdir -p "$JACK_HOME/shadow" "$JACK_HOME/logs"
echo "[6/6] Selftest..."
python3 "$JACK_HOME/jack_selftest.py"
echo "=== Setup abgeschlossen ==="
echo "Dienste starten: sv up jack_cortex jack_telegram jack_waechter"
