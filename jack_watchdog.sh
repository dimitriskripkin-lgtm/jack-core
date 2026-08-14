#!/data/data/com.termux/files/usr/bin/bash
# Watchdog fuer jack_autonomous - startet ihn neu wenn er tot ist
while true; do
  if ! sv status jack_autolearn | grep -q "^run:"; then
    sv up jack_autolearn
    echo "[watchdog] jack_autolearn neugestartet" >> ~/jack/jack_decisions.log
  fi
  sleep 60
done
