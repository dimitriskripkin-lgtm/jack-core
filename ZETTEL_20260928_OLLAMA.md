# ZETTEL 28.09.2026 - Ollama-Politik (Entscheidung Dima)

ENTSCHEIDUNG (Dima, 28.09.2026): Ollama ist STANDARD AUS. Bei Bedarf wird es einzeln eingeschaltet und geht danach wieder aus.
- HONOR: kein Ollama. Der frueher bewusst gewollte "Hybrid" (jack_ollama_guard.py, Marker JACK_TUNE_OLLHYB: startete ollama serve auf dem Honor, solange < 42 C) wurde von Dima am 28.09. revidiert und ABGESCHALTET.
- XIAOMI: Standard aus. Sitzung: Act xiaomi_ollama_restart (Parameter auto_off_min, Standard 20, 0 = kein Timer) hebt den Lock auf und schaltet per sv up ein. Ende: xiaomi_ollama_stop oder automatisch per Timer.

WAS TECHNISCH GEAENDERT WURDE
- Honor: Service ollama_local per sv down gestoppt, Datei usr/var/service/ollama_local/down gesetzt (bleibt auch nach Termux-Neustart aus), ollama-Prozess beendet. Act: honor_ollama_disable.
- Xiaomi: Service ollama hat jetzt eine down-Datei (usr/var/service/ollama/down). Einschalten nur ueber xiaomi_ollama_restart.
- Lock ~/jack/.ollama_lock = Standard aus (Waechter meldet dann keinen Alarm). Eine Sitzung benennt ihn vorruebergehend in .ollama_lock.session um.

WIEDER EINSCHALTEN (nur mit neuem Wort von Dima)
- Honor: rm usr/var/service/ollama_local/down und sv up usr/var/service/ollama_local
- Xiaomi: Act xiaomi_ollama_restart

LEHREN (28.09.)
- Auf dem Xiaomi gibt es runit/sv unter Termux (Service ollama). sv fehlt nur in der ROOT-Umgebung von su. Ollama nie per pkill beenden: der Supervisor holt es zurueck. Immer sv down.
- pkill -f <name> trifft auch die eigene Shell und den Supervisor (deren Befehlszeile enthaelt den Namen). Immer pkill -x oder sv.
- Regeln und laufende Dienste gegeneinander pruefen: Der Guard startete Ollama auf dem Honor, obwohl in den Regeln "kein Ollama auf Honor" stand.
- Der fact-Act im Runner ist nur ein Pruefer fuer den Chat-Router und schreibt NICHT in den Graph. Ein Schreibweg fuer Claude in den Graph existiert noch nicht.
