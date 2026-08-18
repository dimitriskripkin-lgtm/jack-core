#!/bin/bash
cd ~/jack
echo "====================================="
echo "  JACK MORGEN-BERICHT $(date '+%d.%m.%Y %H:%M')"
echo "====================================="
echo ""
echo "--- Karte ---"
python3 jack_karte.py status 2>/dev/null
echo ""
echo "--- Lerner ---"
python3 jack_lerner.py bericht 2>/dev/null | head -10
echo ""
echo "--- Log (letzte 10 Aktionen über Nacht) ---"
grep "LERNER\|KARTE" jack_decisions.log 2>/dev/null | tail -10
echo ""
echo "--- Dienste ---"
sv status jack_cortex jack_telegram jack_waechter 2>/dev/null | grep -oP '^\w+: \w+'
echo ""
echo "--- System ---"
echo "RAM: $(awk '/MemAvailable/{print int($2/1024)"MB"}' /proc/meminfo)"
echo "Akku: $(termux-battery-status 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get("percentage","?"),"%" )' 2>/dev/null)"
echo ""
echo "====================================="
echo "  Befehle zum Weitermachen:"
echo "  tail -20 ~/jack/karte_loop.log"
echo "  python3 jack_lerner.py runde"
echo "  python3 jack_karte.py chunk 50"
echo "====================================="
