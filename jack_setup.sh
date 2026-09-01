#!/data/data/com.termux/files/usr/bin/sh
# jack_setup.sh — JACK auf neuem Termux-Gerät in ~10 Minuten aufsetzen
# Getestet: Honor Magic8 Pro, Termux 0.118, kein Root nötig
set -e

JACK_HOME="$HOME/jack"
echo "=== JACK Setup ==="
echo "Ziel: $JACK_HOME"

# 1. Pakete
echo "[1/6] Pakete installieren..."
pkg install -y python git openssh sqlite curl termux-api 2>/dev/null

# 2. Python-Deps
echo "[2/6] Python-Pakete..."
pip install requests 2>/dev/null || true

# 3. Repo klonen
echo "[3/6] Repo klonen..."
if [ -d "$JACK_HOME/.git" ]; then
    echo "  Repo existiert — pull"
    cd "$JACK_HOME" && git pull origin master
else
    git clone https://github.com/dimitriskripkin-lgtm/jack-core.git "$JACK_HOME"
fi

# 4. Config prüfen
echo "[4/6] Config..."
if [ ! -f "$JACK_HOME/config.ini" ]; then
    echo "  WARNUNG: config.ini fehlt — bitte manuell anlegen"
    echo "  Vorlage: $JACK_HOME/config.ini.example"
fi

# 5. Verzeichnisse
echo "[5/6] Verzeichnisse..."
mkdir -p "$JACK_HOME/missions/pending"
mkdir -p "$JACK_HOME/missions/done"
mkdir -p "$JACK_HOME/missions/fail"
mkdir -p "$JACK_HOME/missions/archive"
mkdir -p "$JACK_HOME/shadow"
mkdir -p "$JACK_HOME/logs"

# 6. Selftest
echo "[6/6] Selftest..."
python3 "$JACK_HOME/jack_selftest.py"

echo ""
echo "=== Setup abgeschlossen ==="
echo "Dienste starten: sv up jack_cortex jack_telegram jack_waechter"
