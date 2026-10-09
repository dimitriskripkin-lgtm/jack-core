# 270 Honor-Diagnose (jack_honor_diag.py, 09.10.2026 21:5x)
Anlass: Honor wurde heiss (Akku 47 C, Load 17), Termux-Prozesse waren alle im Leerlauf, die Last lag ausserhalb von Termux.
## Idee
Termux sieht fremde Apps nicht. Shizuku-Shell (rish, liegt schon in PATH und ~/rish) liefert Shell-Rechte (uid 2000) ohne Root: top, dumpsys battery/thermalservice/cpuinfo/meminfo/batterystats.
## Werkzeug
python3 jack_honor_diag.py snap | hot [grad] | watch [grad]. Schreibt reports/honor_diag.txt. Nur festes Allowlist-Dict ALLOW, keine freien Kommandos, Ausgabe gefiltert (Token-Woerter) und gekuerzt. hot sichert ab 43 C (Standard) einen Snapshot nach reports/honor_hot/ (max 20). watch prueft jede Minute, 10 Min Sperre zwischen Snapshots. Noch KEIN Dienst eingerichtet.
## Voraussetzung
Shizuku muss laufen (Server is not running = aus). Ohne Root nach jedem Neustart per Wireless-Debugging starten. Ohne Shizuku liefert snap nur Akku, Uptime und Termux-Prozesse und sagt das.
## Rechte
jack_honor_diag.py steht in CHATGPT_NOWRITE (privilegierter Wrapper). Lesen darf ChatGPT.
## Offen
Dienst fuer watch (runit) nach Dima-Go. Strom-Rohwert von termux-battery-status hat uneinheitliche Einheit (µA oder mA), nicht interpretieren.
