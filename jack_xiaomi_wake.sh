#!/data/data/com.termux/files/usr/bin/bash
# Startet SSH-Daemon auf Xiaomi via Shizuku RPC
# Voraussetzung: Shizuku läuft, User hat Shizuku-Berechtigung

XIAOMI_IP="192.168.178.154"
XIAOMI_SSH_PORT=8022

echo "[WAKE] Versuche SSH auf Xiaomi zu starten via Shizuku..."

# Shizuku RPC: starten eines beliebigen Befehls
# Das geht via 'cmd' Shell-Befehl, den Shizuku mit elevated rights ausführt
adb shell cmd package install-existing com.termux 2>/dev/null

# Trigger: setprop um den SSH-Daemon zu starten (Xiaomi-spezifisch)
adb shell setprop ctl.start sshd 2>/dev/null

sleep 2

# Verifikation: Ping
if ping -c 1 -W 1 $XIAOMI_IP > /dev/null 2>&1; then
    echo "[WAKE] ✓ Xiaomi erreichbar (Ping ok)"
else
    echo "[WAKE] ✗ Xiaomi nicht erreichbar"
    exit 1
fi

# SSH-Test
if timeout 3 ssh -o ConnectTimeout=2 -p $XIAOMI_SSH_PORT root@$XIAOMI_IP "echo SSH_OK" 2>/dev/null; then
    echo "[WAKE] ✓ SSH-Daemon läuft"
    exit 0
else
    echo "[WAKE] ✗ SSH-Daemon antwortet nicht - Shizuku Permission fehlt?"
    exit 1
fi
