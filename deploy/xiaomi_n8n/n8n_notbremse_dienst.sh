export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:$PATH SVDIR=/data/data/com.termux/files/usr/var/service
# crond ist seit 09/2025 absichtlich aus (alte @reboot-Titan-Jobs) -> nicht anfassen, eigene Zeile wieder raus
crontab -l 2>/dev/null | grep -v n8n_waechter | crontab -
echo cron_zeilen_n8n=$(crontab -l | grep -c n8n_waechter)
D=$SVDIR/n8n_waechter
mkdir -p "$D"
cat > "$D/run" <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
# JACK N1 Notbremse als eigener runit-Dienst (crond ist absichtlich aus). Prueft jede Minute.
exec 2>&1
while true; do /data/data/com.termux/files/usr/bin/sh /data/data/com.termux/files/home/n8n_waechter.sh; sleep 60; done
EOF
chmod 755 "$D/run"
sleep 8
sv status n8n_waechter
echo log=$(tail -n 1 $HOME/n8n_waechter.log 2>/dev/null || echo leer)
sv status n8n | cut -d';' -f1
