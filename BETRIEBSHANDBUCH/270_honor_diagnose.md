# 270 Honor-Diagnose (jack_honor_diag.py, 09.10.2026 21:5x)
Anlass: Honor wurde heiss (Akku 47 C, Load 17), Termux-Prozesse waren alle im Leerlauf, die Last lag ausserhalb von Termux.
## Idee
Termux sieht fremde Apps nicht. Shizuku-Shell (rish, liegt schon in PATH und ~/rish) liefert Shell-Rechte (uid 2000) ohne Root: top, dumpsys battery/thermalservice/cpuinfo/meminfo/batterystats.
## Werkzeug
python3 jack_honor_diag.py snap | hot [grad] | watch [grad]. Schreibt reports/honor_diag.txt. Nur festes Allowlist-Dict ALLOW, keine freien Kommandos, Ausgabe gefiltert (Token-Woerter) und gekuerzt. hot sichert ab 43 C (Standard) einen Snapshot nach reports/honor_hot/ (max 20). watch prueft jede Minute, 10 Min Sperre zwischen Snapshots. Dienst jack_honor_watch (runit, run-Datei in usr/var/service) laeuft seit 09.10. 22:0x mit Schwelle 43 C. Notbremse: sv down jack_honor_watch. Erster Messbefund: Claude-App Platz 1 (14 % CPU), Anzeige-Kette ~23 %, RAM 10,4 von 11,1 GB, 5 GB Swap.
## Voraussetzung
Shizuku muss laufen (Server is not running = aus). Ohne Root nach jedem Neustart per Wireless-Debugging starten. Ohne Shizuku liefert snap nur Akku, Uptime und Termux-Prozesse und sagt das.
## Rechte
jack_honor_diag.py steht in CHATGPT_NOWRITE (privilegierter Wrapper). Lesen darf ChatGPT.
## Offen
Shizuku laeuft nur bis zum Neustart des Handys (danach per Wireless-Debugging neu starten, sonst nur Termux-Werte). Strom-Rohwert von termux-battery-status hat uneinheitliche Einheit (µA oder mA), nicht interpretieren.

## Nachtrag 11.10.2026: Hitze-Ursache gefunden
- com.appseleration.android.selfcare (v15.8.1, normale User-App) lief dauerhaft bei ca. 125 % CPU, in allen honor_hot-Schnappschuessen seit 09.10. 22:08, mit wechselnder PID (Neustarts). force-stop half nicht: neue PID nach <1 s, wieder 129 %.
- Massnahme (Dima, 11.10. 00:4x): rish pm disable-user --user 0 <paket>. Danach keine Last mehr, Akku 41 -> 37 C. Rueckgaengig: rish -c 'pm enable --user 0 <paket>'.
- Ursache der App-Last und Herkunft der App unbekannt. JACK-Anteil an der Last: gering (jack_mcp_server ca. 3 %).
