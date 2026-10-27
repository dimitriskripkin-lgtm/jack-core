export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:$PATH SVDIR=/data/data/com.termux/files/usr/var/service
S=$SVDIR/n8n
cp "$S/run" "$HOME/n8n_run_alt_20261027.bak"
cat > "$S/run" <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
# JACK N1 (27.10.2026, Claude): n8n in proot-Ubuntu als User n8n, nur 127.0.0.1:5678.
# Neustart-Bremse: 30 s warten + Hitzesperre 45 C vor jedem Start; finish pausiert 120 s nach Absturz.
export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:$PATH
exec 2>&1
sleep 30
t=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0)
if [ "$t" -ge 45000 ]; then echo "n8n: zu heiss ($t), kein Start"; exit 1; fi
exec proot-distro login ubuntu --user n8n -- /bin/bash -lc 'set -a; . "$HOME/.config/jack-n8n/key.env"; . "$HOME/.config/jack-n8n/service.env"; set +a; export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"; nvm use 24 >/dev/null; exec "$HOME/jack_n8n/node_modules/n8n/bin/n8n" start'
EOF
cat > "$S/finish" <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
# JACK N1: nach Absturz 120 s Pause; gewolltes Stoppen (sv down = TERM) ohne Pause
if [ "$1" = "-1" ] && [ "$2" = "15" ]; then exit 0; fi
echo "n8n beendet (rc=$1 sig=$2), Pause 120 s"
sleep 120
EOF
chmod 755 "$S/run" "$S/finish"
pkill -TERM -f 'jack_n8n/node_modules' && echo handstart_gestoppt
sleep 8
echo rest=$(pgrep -c -f jack_n8n)
rm -f "$S/down"
sv up n8n
sleep 2
sv status n8n
