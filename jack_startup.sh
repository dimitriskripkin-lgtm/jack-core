#!/data/data/com.termux/files/usr/bin/bash
SVDIR=/data/data/com.termux/files/usr/var/service
export SVDIR
cd /data/data/com.termux/files/home/jack
LOG=/data/data/com.termux/files/home/jack/startup.log

if sv status jack_cortex 2>/dev/null | grep -q "^run:"; then
  echo "$(date): Cortex laeuft bereits" >> "$LOG"
else
  echo "$(date): Cortex nicht run - sv up" >> "$LOG"
  sv up jack_cortex >> "$LOG" 2>&1
fi

if [ -d "$SVDIR/ollama" ]; then
  if sv status ollama 2>/dev/null | grep -q "^run:"; then
    echo "$(date): Ollama laeuft bereits" >> "$LOG"
  else
    echo "$(date): Ollama nicht run - sv up" >> "$LOG"
    sv up ollama >> "$LOG" 2>&1
  fi
else
  echo "$(date): Ollama auf Honor disabled - skip" >> "$LOG"
fi
