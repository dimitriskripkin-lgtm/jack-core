#!/data/data/com.termux/files/usr/bin/bash
cd ~/jack
if ! sv status jack_cortex 2>/dev/null | grep -q "^run:"; then
  echo "$(date): Cortex nicht run - sv up" >> ~/jack/startup.log
  sv up jack_cortex >> ~/jack/startup.log 2>&1
else
  echo "$(date): Cortex laeuft bereits" >> ~/jack/startup.log
fi
if ! sv status ollama 2>/dev/null | grep -q "^run:"; then
  echo "$(date): Ollama nicht run - sv up" >> ~/jack/startup.log
  sv up ollama >> ~/jack/startup.log 2>&1
else
  echo "$(date): Ollama laeuft bereits" >> ~/jack/startup.log
fi
PORT=$(cat ~/jack/.adb_port 2>/dev/null || echo "36205")
adb connect 127.0.0.1:$PORT >/dev/null 2>&1
