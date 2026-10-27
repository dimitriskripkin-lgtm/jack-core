#!/data/data/com.termux/files/usr/bin/bash
# JACK N1 (27.10.2026, Claude): n8n in proot-Ubuntu, User n8n, Node 24 via nvm, n8n fest 2.44.7. Nur 127.0.0.1. Termux-Node bleibt unangetastet.
export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home
export PATH=$PREFIX/bin:$PATH
L=$HOME/n8n_install.log
trap 'echo "FEHLER in Schritt $S (rc=$?)" >>"$L"; exit 1' ERR
set -e
step(){ S=$1; t=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0); echo "=== $(date +%H:%M:%S) Schritt $1 temp=$t" >>"$L"; if [ "$t" -ge 45000 ]; then echo "ABBRUCH Hitze $t" >>"$L"; exit 9; fi; }
U(){ proot-distro login ubuntu -- /bin/bash -lc "$1" >>"$L" 2>&1; }
N(){ proot-distro login ubuntu --user n8n -- /bin/bash -lc "$1" >>"$L" 2>&1; }
echo "START $(date)" >"$L"
step 4; U 'id n8n >/dev/null 2>&1 || useradd -m -s /bin/bash n8n'
step 5; U 'apt-get update'
step 6; U 'DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl git python3 build-essential pkg-config openssl'
step 7; N '[ -d "$HOME/.nvm" ] || git clone --branch v0.40.3 --depth 1 https://github.com/nvm-sh/nvm.git "$HOME/.nvm"'
step 8; N 'export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm install 24'
step 9; N 'export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24 >/dev/null; v=$(node -v); echo "node $v"; case "$v" in v24.*) ;; *) echo "FALSCHE NODE $v"; exit 3;; esac'
step 10a; N 'export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24 >/dev/null; echo "npm view:"; npm view n8n@2.44.7 version'
step 10; N 'export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24 >/dev/null; mkdir -p "$HOME/jack_n8n"; npm install --prefix "$HOME/jack_n8n" --no-audit --no-fund --save-exact n8n@2.44.7'
step 11; N 'export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24 >/dev/null; "$HOME/jack_n8n/node_modules/.bin/n8n" --version'
echo "FERTIG $(date +%H:%M:%S)" >>"$L"
