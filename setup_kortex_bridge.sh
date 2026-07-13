#!/bin/bash
set -e

JACK_PATH="$HOME/jack"
BRIDGE_PID_FILE="$JACK_PATH/.kortex_bridge.pid"

echo "=== KORTEX Bridge Setup ==="

echo "[1/4] Installing dependencies..."

echo "[2/4] Stopping old bridge if running..."
if [ -f "$BRIDGE_PID_FILE" ]; then
    OLD_PID=$(cat "$BRIDGE_PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        kill "$OLD_PID" || true
        sleep 1
    fi
fi

echo "[3/4] Killing old Flask on port 5005..."
pkill -f "python.*5005" || true
sleep 1

echo "[4/4] Starting KORTEX Bridge..."
cd "$JACK_PATH"
nohup python3 kortex_controller.py > kortex_bridge.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > "$BRIDGE_PID_FILE"
sleep 2

if kill -0 "$NEW_PID" 2>/dev/null; then
    echo ""
    echo "✅ KORTEX Bridge running!"
    echo "   PID: $NEW_PID"
    echo "   Port: 5005"
    echo "   Log: tail -f $JACK_PATH/kortex_bridge.log"
else
    echo "❌ Failed to start. Check:"
    tail -20 "$JACK_PATH/kortex_bridge.log"
    exit 1
fi
