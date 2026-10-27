#!/usr/bin/env python3
"""JACK_TUNE_XINOTAUS (27.10.2026, Claude, Kap 307): Notfall-Werkzeug fuer "Xiaomi heiss, miss durch".
messen(): Temperatur, Akku, Last, n8n-Status, Notbremse-Log.  n8n_aus(): n8n stoppen + Autostart sperren.
n8n_an(): Sperre aufheben + starten. Alles als Termux-Nutzer (as_root=False), Skripte per stdin.
Aufruf: python3 jack_xiaomi_notaus.py messen | n8n_aus | n8n_an
"""
import sys
sys.path.insert(0, "/data/data/com.termux/files/home/jack")
import jack_xiaomi as _x

_ENV = ("export PREFIX=/data/data/com.termux/files/usr HOME=/data/data/com.termux/files/home "
        "PATH=/data/data/com.termux/files/usr/bin:$PATH SVDIR=/data/data/com.termux/files/usr/var/service\n")

_MESSEN = _ENV + r"""
echo "temp_cpu=$(cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null)"
echo "akku=$(cat /sys/class/power_supply/battery/capacity 2>/dev/null)% akku_temp=$(cat /sys/class/power_supply/battery/temp 2>/dev/null)"
echo "n8n: $(sv status n8n 2>&1 | cut -d';' -f1)"
echo "notbremse: $(sv status n8n_waechter 2>&1 | cut -d';' -f1)"
echo "ollama: $(pgrep -f 'ollama serve' >/dev/null && echo laeuft || echo aus)"
echo "proot_prozesse=$(pgrep -c proot)"
echo "n8n_neustarts_log=$(grep -c 'n8n beendet' $PREFIX/var/log/sv/n8n/current 2>/dev/null)"
tail -n 3 $HOME/n8n_waechter.log 2>/dev/null
"""

_AUS = _ENV + r"""
touch $SVDIR/n8n/down; sv down n8n
sleep 4
for p in $(pgrep -f '^n8n '); do kill -TERM "$p"; done
sleep 3
echo "n8n: $(sv status n8n | cut -d';' -f1) rest=$(pgrep -f '^n8n ' | wc -l)"
echo "$(date '+%F %T') n8n_aus durch Claude/JACK" >> $HOME/n8n_waechter.log
"""

_AN = _ENV + r"""
rm -f $SVDIR/n8n/down; sv up n8n; sleep 2
echo "n8n: $(sv status n8n | cut -d';' -f1) (Start dauert ca. 85 s)"
"""


def _lauf(skript, timeout=40):
    r = _x.run_shell("/data/data/com.termux/files/usr/bin/bash -s", timeout=timeout,
                     as_root=False, input_data=skript)
    if isinstance(r, dict):
        if not r.get("success") and not r.get("stdout"):
            return "XIAOMI nicht erreichbar oder Fehler: " + str(r.get("stderr"))[:200]
        return str(r.get("stdout", "")).strip()
    return str(r)


def messen():
    return _lauf(_MESSEN)


def n8n_aus():
    return _lauf(_AUS, timeout=45)


def n8n_an():
    return _lauf(_AN)


if __name__ == "__main__":
    f = {"messen": messen, "n8n_aus": n8n_aus, "n8n_an": n8n_an}.get(sys.argv[1] if len(sys.argv) > 1 else "messen")
    print(f() if f else "Aufruf: messen | n8n_aus | n8n_an")
