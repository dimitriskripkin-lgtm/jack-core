#!/data/data/com.termux/files/usr/bin/bash
TRIGGER=~/.voice_trigger
while true; do
  if [ -f "$TRIGGER" ]; then
    SEC=$(cat "$TRIGGER")
    rm -f "$TRIGGER" ~/.voice_rec.m4a
    termux-microphone-record -f ~/.voice_rec.m4a -l ${SEC:-5} -e aac
    echo "done" > ~/.voice_done
  fi
  sleep 1
done
