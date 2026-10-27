export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home PATH=/data/data/com.termux/files/usr/bin:$PATH
W=$HOME/n8n_waechter.sh
cat > "$W" <<'EOF'
#!/data/data/com.termux/files/usr/bin/sh
# JACK N1 Notbremse (27.10.2026, Claude, Kap 307): laeuft jede Minute per cron auf dem XIAOMI, braucht kein SSH/Honor.
# Stoppt n8n (sv down + down-Datei = kein Autostart), wenn Xiaomi >= 48 C ODER n8n in den letzten 15 Min >= 3x abgestuerzt ist.
export PREFIX=/data/data/com.termux/files/usr PATH=/data/data/com.termux/files/usr/bin:$PATH SVDIR=/data/data/com.termux/files/usr/var/service
S=$SVDIR/n8n; L=/data/data/com.termux/files/home/n8n_waechter.log
[ -d "$S" ] || exit 0
[ -e "$S/down" ] && exit 0
t=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null || echo 0)
grund=""
[ "$t" -ge 48000 ] && grund="Hitze $t"
seit=$(date -d '-15 min' +%s 2>/dev/null || echo 0)
n=0
for z in $(grep 'n8n beendet' $PREFIX/var/log/sv/n8n/current 2>/dev/null | cut -c1-19 | tr '_' ' ' | tail -n 20 | sed 's/ /T/'); do
  s=$(date -d "$(echo $z | tr 'T' ' ')" +%s 2>/dev/null || echo 0)
  [ "$s" -ge "$seit" ] && n=$((n+1))
done
[ "$n" -ge 3 ] && grund="${grund:+$grund, }$n Abstuerze in 15 Min"
if [ -n "$grund" ]; then
  touch "$S/down"; sv down n8n
  echo "$(date '+%F %T') NOTBREMSE n8n gestoppt: $grund" >> "$L"
fi
EOF
chmod 700 "$W"
( crontab -l 2>/dev/null | grep -v n8n_waechter; echo "* * * * * $W  # JACK_N1_NOTBREMSE" ) | crontab -
crontab -l | grep -c n8n_waechter
sv status crond 2>/dev/null || SVDIR=$PREFIX/var/service sv status crond
sh "$W" && echo testlauf_ok
tail -n 2 $HOME/n8n_waechter.log 2>/dev/null; SVDIR=$PREFIX/var/service sv status n8n | cut -d';' -f1
