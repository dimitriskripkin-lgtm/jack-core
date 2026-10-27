# 22. jack_gemini_bridge.py

Gelesen 03.10.2026, erste 70 Zeilen. Kein Umbau.

**Zweck:** Gemini-Ruf plus Status sammeln. Schluessel aus der Secrets-Datei, Name GEMINI_API_KEY.

**Funktionen:** load_api_key, collect_status. Circuit-Breaker im RAM: _CB_FAILS, _CB_OPEN. Fehler landen in jack_errors.db.

**Grenze:** Kein Groq-Ersatz in dieser Datei. Aufrufer sind coder und write.

**Offen:** ask_gemini selbst hinter dem Schnitt.

## Nachtrag 11.10.2026 (JACK_TUNE_FLASHCODE)
- ask_gemini(question, status=None, model=None): model nur aus Whitelist (gemini-2.5-flash, gemini-2.5-flash-lite), sonst Config (gemini.model, steht auf flash-lite). Bei Override thinkingBudget 0 (so in der Arena gemessen, sonst frisst Denken die 1400 Ausgabetokens).
- Grund: Arena-Messung 11.10.: Flash 50/58, Flash-Lite 41/58 Aufgaben (ARBEITSPLATZ/gemeinsam/arena/claude_regeln_v1.md). Dima hat am 11.10. Flash fuer schwierige Technik-Aufgaben freigegeben.
- Aufrufer mit Flash: jack_coder.write_code, jack_bugfix_loop. Alle anderen Aufrufer unveraendert (Lite). Live getestet: Flash antwortet, falsches Modell faellt auf Config zurueck.

**Nachtrag 26.10.2026 (Claude, K3b)**
JACK_TUNE_NOHONOROLLAMA: _ollama_fallback ruft kein Honor-localhost mehr, gibt None + Audit [Gemini Fehler]. CB-Skip ruft nicht mehr Groq. ask_gemini(timeout, max_attempts, system_override) optional, Defaults unveraendert (15 s, 3 Versuche).
