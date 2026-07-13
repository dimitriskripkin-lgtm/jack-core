#!/data/data/com.termux/files/usr/bin/bash
echo "=== JACK SESSION START $(date '+%Y-%m-%d %H:%M') ==="
echo ""
echo "--- DIENSTE ---"
sv status jack_telegram jack_waechter jack_cortex jack_autolearn jack_publisher kortex_bridge ollama 2>/dev/null
echo ""
echo "--- BRIDGE ---"
curl -s http://127.0.0.1:5005/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"]}')" 2>/dev/null || echo "OFFLINE"
echo ""
echo "--- GEDAECHTNIS ---"
curl -s "http://127.0.0.1:5005/memory/recent?limit=5" | python3 -c "
import sys,json
r=json.load(sys.stdin)['results']
print(f'{len(r)} Eintraege (letzte 5):')
for e in r: print(f'  [{e[\"category\"]}] {e[\"content\"][:70]}')
" 2>/dev/null
echo ""
echo "--- PROFIL ---"
python3 -c "
import json
p=json.load(open('/data/data/com.termux/files/home/jack/kortex_profile.json'))
print(f'Owner: {p[\"owner\"][\"name\"]} | Ziel: {p[\"owner\"][\"ziel_kurz\"]}')
print(f'Projekte: {[x[\"name\"] for x in p.get(\"projekte\",[])]}')
print(f'Letzte Entscheidung: {p[\"entscheidungen\"][-1][\"entscheidung\"][:70] if p.get(\"entscheidungen\") else \"keine\"}')
" 2>/dev/null
echo ""
echo "--- OFFENE FEHLER ---"
python3 -c "
import sqlite3
con=sqlite3.connect('/data/data/com.termux/files/home/jack/jack_errors.db')
rows=con.execute('SELECT module,error_msg FROM errors WHERE resolved=0 ORDER BY timestamp DESC LIMIT 3').fetchall()
con.close()
if not rows: print('Keine offenen Fehler.')
for r in rows: print(f'  [{r[0]}] {r[1][:70]}')
" 2>/dev/null
echo ""
echo "--- LOGS (letzte 5) ---"
tail -5 ~/jack/jack_decisions.log 2>/dev/null || echo "(kein Log)"
echo ""
echo "=== BEREIT ==="
