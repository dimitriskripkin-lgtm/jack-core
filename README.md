# JACK — Just Autonomous Command Kit

Ein Lebens-OS auf zwei Android-Handys. Honor denkt, Xiaomi führt aus.
Gebaut von Dima, LKW, ein Daumen, Termux.

GitHub ist der Spiegel. Honor ist die Wahrheit.

## Ist 14.09.2026

Pflicht-Dienste: jack_telegram, jack_cortex, jack_waechter.
Messgürtel: jack_missions an, nur messen, kein Live-Write.
Bewusst aus: jack_autolearn, jack_publisher, ssh_tunnel_ollama.
Ollama: aus. Datei `.ollama_lock` ist hartes Nein. Dienst heißt `_ollama_disabled`.
Mund: Groq. Gemini denkt, chattet nicht.
Persona-Kern: klein, `jack_persona_kern.md`.
Selftest-Soll: 3 Dienste, nicht 6 und nicht Ollama-up.

## Geräte

Honor = Gehirn. Termux, jack_*.py, Telegram, Wahrheit.
Xiaomi = Muskel. SSH-Alias `xiaomi-jack`. Hotspot-IP wechselt. Alias schlägt feste Zahl.

## Was JACK wirklich tut

Telegram nimmt den Satz. Router sortiert Werkzeug oder Talk.
Talk geht an Groq. Xiaomi führt aus, denkt nicht.
Wächter prüft Pulse. Shadow-Fixes enden vor Freigabe.
Ollama startet nur nach Dimas Satz „ollama an“.

## Was JACK nicht tut

Kein lokaler Chat-Server auf dem Honor.
Kein `pkill -f`.
Kein neues `jack_*.py` ohne Dimas Satz.
Wächter nicht neu starten ohne Drain: pending 0, fail 0, runner 0, stop 1.
GitHub nicht als Wahrheit lesen.

## Selftest

```
python3 /data/data/com.termux/files/home/jack/jack_selftest.py
```

Soll: services 3/3, Ollama-Check = Lock liegt.

## Eisen

P0 Temperatur.
Backup vor Patch.
Attic statt rm.
Eine Prüfung, eine Frage.
Kompiliert heißt nicht läuft.
Datei ist nicht Prozess.
