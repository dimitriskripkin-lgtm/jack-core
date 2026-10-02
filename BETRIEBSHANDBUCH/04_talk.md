## 4. jack_talk.py (643 Zeilen, Gespräch/LLM-Anbindung)

**Zweck:** Baut den eigentlichen Prompt für die Sprach-KI zusammen und ruft sie auf. Wird von
`jack_telegram.py` als letzter Fallback genutzt (Kapitel 2, Schritt 10), wenn kein Befehl und keine
Chat-Router-Lane gegriffen hat.

**Modellaufteilung, hier im Code bestätigt (nicht nur in alten Notizen):** Persönliche Gespräche
("wer bin ich", "was denkst du", "kumpel", ...) laufen über Groq (`jack_groq_bridge`) wegen besserer
Persona-Treue; Status-/Technik-Anfragen ("zustand", "status", "tune", "health") nehmen einen anderen
Pfad. Der genaue Verzweigungspunkt zwischen beiden ist nicht vollständig nachvollzogen (eine
Bedingung mit doppelter Verneinung) — für später vormerken, nicht als sicher hinschreiben.

**`_scrub_out(s)`** — Nachbearbeitung JEDER Antwort, bevor sie rausgeht. Zwei bekannte Filter:
- `JACK_TUNE_NOOLLAMA_CLAIM` (26.09. gebaut) — erkennt Ollama-Behauptungen, schneidet nur den
  betroffenen Satz raus (nicht die ganze Antwort), Totalersatz nur wenn nichts Sinnvolles übrig bleibt.
- Ein **"Log-Ausrede"-Filter** (`JACK_TUNE_SCRUB4`) — erkennt Formulierungen wie "müsste im Log
  stehen" und ersetzt sie durch "Das steht in keinem Log. Ich rate nicht." Bisher nirgends
  dokumentiert gewesen, faktisch ein weiterer Anti-Halluzinations-Filter neben
  `JACK_TUNE_NOFAKEACTION` (Zeile 351, noch nicht im Detail gelesen).
- Dazu ein Prompt-Leak-Filter: enthält die Antwort interne Regel-Stichworte
  ("SATZANFAENGE VERBOTEN" u. ä.), wird sie komplett verworfen.

**`ist_zustand()`** — liefert den Text, den auch `jack_mission_runner.py`s `fact`-Act prüft
(Kapitel 1: `"SSH" in out and "Akku" not in out`). Bemerkenswert: **prüft den Git-Push-Status nicht
live, sondern liest nur, ob der Quelltext von `jack_publish.py` die Zeichenkette
"git push origin main" enthält** — ein Text-Grep auf den eigenen Code, keine echte Prüfung ob der
letzte Push geklappt hat. Ruft dafür extra `jack_health.py` als Subprozess auf und liest dessen
Ergebnis aus `jack_health_now.json` (eigenes Kapitel offen).

**Weitere Bausteine:**
- `add_to_window()`/`get_window_ctx()` — ein kurzes Gesprächsfenster (letzte paar Nachrichten),
  getrennt von `jack_memory.db`.
- `get_embedding()` + `jack_vecdb.search_mem()` — Vektor-Ähnlichkeitssuche fürs Gedächtnis;
  fällt bei leerem Ergebnis auf eine FTS5-Volltextsuche über `memory_fts` zurück
  (`PHASE 3.4`, Kommentar nennt explizit "Ollama-Sperre" als Grund — die Embedding-Funktion
  hing früher wohl an Ollama).
- `talk_to_ollama()` — existiert als Funktion, obwohl Ollama auf dem Honor hart verboten ist.
  Vermutlich Altlast aus einer Zeit vor dem Verbot, aufrufbar aber (hoffentlich) unbenutzt — noch
  nicht geprüft, ob irgendwas sie wirklich aufruft.
- Graph-Einbindung (`jack_graph.prompt_block()`) nur wenn der Prompt sich erkennbar auf eine Person
  bezieht (Namensabgleich gegen Graph-Knoten oder Schlüsselwörter) — spart Tokens, wenn's nicht nötig ist.
- System-Prompt beginnt bewusst mit Verboten ("Erfinde KEINE Fakten", "Zähle NIEMALS Fakten auf"),
  nicht am Ende — Kommentar verweist auf eine frühere Erkenntnis, dass Verbote am Ende weniger wirken.

**Offene Fragen für später:** Genauer Verzweigungspunkt Groq-vs-Gemini. Was prüft
`JACK_TUNE_NOFAKEACTION` genau (Zeile 351)? Wird `talk_to_ollama()` von irgendwo noch aufgerufen?
Was ist `jack_health.py`/`jack_health_now.json` im Detail?
