#!/data/data/com.termux/files/usr/bin/bash
cd ~/jack
FAIL_COUNT_FILE=~/jack/.cortex_fail_count

if ! pgrep -f "ollama serve" > /dev/null; then
    echo "$(date): Ollama tot, starte neu" >> ~/jack/startup.log
    nohup ollama serve > ~/jack/ollama.log 2>&1 &
else
    echo "$(date): Ollama laeuft bereits" >> ~/jack/startup.log
fi

if pgrep -f "jack_cortex.py" > /dev/null; then
    echo "$(date): Cortex laeuft bereits" >> ~/jack/startup.log
    echo 0 > "$FAIL_COUNT_FILE"
    exit 0
fi

FAILS=$(cat "$FAIL_COUNT_FILE" 2>/dev/null || echo 0)
FAILS=$((FAILS + 1))
echo "$FAILS" > "$FAIL_COUNT_FILE"

if [ "$FAILS" -ge 3 ]; then
    echo "$(date): Cortex 3x hintereinander tot, rufe Fixer" >> ~/jack/startup.log
    python3 -c "from jack_bug_fixer import JackBugFixer; JackBugFixer().run()" >> ~/jack/startup.log 2>&1
    echo 0 > "$FAIL_COUNT_FILE"
else
    echo "$(date): Cortex tot (Versuch $FAILS/3), starte neu" >> ~/jack/startup.log
    nohup python3 jack_cortex.py >> ~/jack/cortex_stdout.log 2>&1 &
fi
